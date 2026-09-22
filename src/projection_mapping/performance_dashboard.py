from __future__ import annotations

from dataclasses import dataclass, asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
from typing import Any

from .performance_control import HOT_CUES, PerformanceControlBus


@dataclass(frozen=True)
class LivePerformanceState:
    cue: str = "liquid_intro"
    journey: str = "liquid_arc"
    mode: str = "hybrid"
    section: str = "steady"
    macro: float = 0.0
    energy: float = 0.0
    bpm: float = 0.0
    beat_confidence: float = 0.0
    quantize: str = "off"
    pending: int = 0
    loop: str = "idle"
    loop_events: int = 0
    chord: str = "silence"
    notes: int = 0
    sustain: float = 0.0
    piano_velocity: float = 0.0
    piano_strike: float = 0.0


class LiveStateHub:
    def __init__(self, initial: LivePerformanceState | None = None) -> None:
        self._state = initial or LivePerformanceState()
        self._lock = threading.Lock()

    def set(self, state: LivePerformanceState) -> None:
        with self._lock:
            self._state = state

    def get(self) -> LivePerformanceState:
        with self._lock:
            return self._state


_DASHBOARD_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ProjectionMapping Performance Director</title>
<style>
:root{color-scheme:dark;background:#07090e;color:#eaf6ff;font-family:Inter,ui-sans-serif,system-ui,sans-serif}
*{box-sizing:border-box}body{margin:0;padding:20px;max-width:1100px;margin-inline:auto}
h1{font-size:20px;margin:0 0 14px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}
.card{background:#10141e;border:1px solid #273142;border-radius:12px;padding:14px}
.label{font-size:11px;text-transform:uppercase;letter-spacing:.11em;color:#8090a7}.value{font-size:24px;font-weight:700;margin-top:4px}
.cues{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;margin-top:12px}
button,select,input{font:inherit}.cue,.action{border:1px solid #334057;background:#171d29;color:#eaf6ff;border-radius:9px;padding:12px;cursor:pointer}
.cue.active{border-color:#11d7ff;background:#112630}.controls{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}
.action.hot{border-color:#ff2ccf}.range{width:100%;accent-color:#14d7ff}.tiny{font-size:12px;color:#93a0b4}
.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.row>*{min-width:0}
select{background:#111722;color:#eaf6ff;border:1px solid #334057;border-radius:8px;padding:9px}
.good{color:#64f7ba}.warn{color:#ffd166}
</style>
</head>
<body>
<h1>Performance Director</h1>
<div class="grid">
  <div class="card"><div class="label">Cue</div><div class="value" id="cue">—</div><div class="tiny" id="journey">—</div></div>
  <div class="card"><div class="label">Music</div><div class="value" id="section">—</div><div class="tiny" id="bpm">—</div></div>
  <div class="card"><div class="label">MADNESS</div><div class="value" id="macro">0.00</div><input id="madness" class="range" type="range" min="0" max="1" step="0.01" value=".45"></div>
  <div class="card"><div class="label">Piano</div><div class="value" id="chord">silence</div><div class="tiny" id="piano">0 notes</div></div>
</div>
<div class="controls">
  <button class="action" id="next">Next cue</button>
  <button class="action hot" id="rec">Record loop</button>
  <button class="action" id="stopLoop">Stop loop</button>
  <button class="action" id="clearLoop">Clear loop</button>
  <label class="tiny">Quantize
    <select id="quantize"><option>off</option><option>beat</option><option>bar</option></select>
  </label>
  <span class="tiny" id="loopState">loop idle</span>
</div>
<div class="cues" id="cues"></div>
<p class="tiny">Local control dashboard. OSC/MIDI and this browser feed the same Director state machine.</p>
<script>
const cueNames = __HOT_CUES__;
const cueBox = document.getElementById('cues');
for (const cue of cueNames) {
  const b=document.createElement('button'); b.className='cue'; b.textContent=cue; b.dataset.cue=cue;
  b.addEventListener('click',()=>action('cue',[cue])); cueBox.appendChild(b);
}
async function action(name,args=[]){
  await fetch('/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:name,args})});
}
document.getElementById('next').addEventListener('click',()=>action('next'));
document.getElementById('rec').addEventListener('click',()=>action('loop_record_toggle'));
document.getElementById('stopLoop').addEventListener('click',()=>action('loop_stop'));
document.getElementById('clearLoop').addEventListener('click',()=>action('loop_clear'));
document.getElementById('quantize').addEventListener('change',e=>action('quantize',[e.target.value]));
let sliderBusy=false;
const madness=document.getElementById('madness');
madness.addEventListener('pointerdown',()=>sliderBusy=true);
madness.addEventListener('pointerup',()=>sliderBusy=false);
madness.addEventListener('input',e=>action('madness',[Number(e.target.value)]));
async function refresh(){
  try{
    const s=await fetch('/state',{cache:'no-store'}).then(r=>r.json());
    document.getElementById('cue').textContent=s.cue;
    document.getElementById('journey').textContent=s.journey+' · '+s.mode;
    document.getElementById('section').textContent=s.section;
    document.getElementById('bpm').textContent=(s.bpm? s.bpm.toFixed(1)+' BPM':'tempo —')+' · conf '+s.beat_confidence.toFixed(2);
    document.getElementById('macro').textContent=s.macro.toFixed(2);
    if(!sliderBusy) madness.value=s.macro;
    document.getElementById('chord').textContent=s.chord;
    document.getElementById('piano').textContent=s.notes+' notes · sustain '+s.sustain.toFixed(2)+' · strike '+s.piano_strike.toFixed(2);
    document.getElementById('quantize').value=s.quantize;
    document.getElementById('loopState').textContent='loop '+s.loop+' · '+s.loop_events+' events · '+s.pending+' pending';
    document.querySelectorAll('.cue').forEach(b=>b.classList.toggle('active',b.dataset.cue===s.cue));
  }catch(e){}
}
setInterval(refresh,200); refresh();
</script>
</body>
</html>
""".replace("__HOT_CUES__", json.dumps(list(HOT_CUES)))


class PerformanceDashboardServer:
    """Tiny localhost web controller + live state dashboard with no extra dependencies."""

    def __init__(
        self,
        bus: PerformanceControlBus,
        state: LiveStateHub,
        *,
        host: str = "127.0.0.1",
        port: int = 8765,
    ) -> None:
        self.bus = bus
        self.state = state
        self.host = host
        self.port = int(port)
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> "PerformanceDashboardServer":
        if self.port <= 0:
            return self
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def _json(self, payload: Any, status: int = 200) -> None:
                encoded = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(encoded)

            def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
                if self.path == "/":
                    encoded = _DASHBOARD_HTML.encode("utf-8")
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(encoded)))
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    self.wfile.write(encoded)
                    return
                if self.path == "/state":
                    self._json(asdict(outer.state.get()))
                    return
                self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)

            def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
                if self.path != "/action":
                    self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
                    return
                try:
                    size = min(int(self.headers.get("Content-Length", "0")), 8192)
                    payload = json.loads(self.rfile.read(size).decode("utf-8"))
                    action = str(payload.get("action", "")).strip()
                    args = payload.get("args", [])
                    if not action or not isinstance(args, list):
                        raise ValueError("invalid action payload")
                    outer.bus.emit(action, *args[:16])
                    self._json({"ok": True})
                except (ValueError, TypeError, json.JSONDecodeError) as exc:
                    self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

            def log_message(self, _format: str, *_args: Any) -> None:
                return

        self._server = ThreadingHTTPServer((self.host, self.port), Handler)
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="pm-performance-dashboard",
            daemon=True,
        )
        self._thread.start()
        return self

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}/"

    def close(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        self._server = None
        self._thread = None


class OSCStateBroadcaster:
    """Optional outbound OSC state feedback for TouchDesigner/controllers."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9001) -> None:
        self.host = host
        self.port = int(port)
        self._client = None
        self._last: dict[str, Any] = {}

    def start(self) -> "OSCStateBroadcaster":
        if self.port <= 0:
            return self
        try:
            from pythonosc.udp_client import SimpleUDPClient
        except ImportError as exc:
            raise RuntimeError("OSC state output requires the controls extra") from exc
        self._client = SimpleUDPClient(self.host, self.port)
        return self

    def send(self, state: LivePerformanceState) -> None:
        if self._client is None:
            return
        payload = asdict(state)
        for key, value in payload.items():
            if self._last.get(key) == value:
                continue
            self._client.send_message(f"/pm/state/{key}", value)
        self._last = payload

    def close(self) -> None:
        self._client = None


__all__ = [
    "LivePerformanceState",
    "LiveStateHub",
    "OSCStateBroadcaster",
    "PerformanceDashboardServer",
]

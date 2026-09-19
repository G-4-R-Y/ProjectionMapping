from __future__ import annotations

import argparse
import json
import threading
import webbrowser
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .color_palettes import palette_swatches
from .feature_registry import Feature, FeatureRegistry, current_platform, load_registry
from .launcher import FeatureLauncher


def _feature_payload(feature: Feature) -> dict[str, Any]:
    def param_payload(param: Any) -> dict[str, Any]:
        payload = asdict(param)
        if "palette" in param.key.lower() and param.choices:
            payload["swatches"] = palette_swatches(param.choices)
        return payload

    return {
        "id": feature.id,
        "name": feature.name,
        "category": feature.category,
        "description": feature.description,
        "fullscreen": feature.fullscreen,
        "available": feature.available(),
        "availability_hint": feature.availability_hint(),
        "groups": [
            {
                "name": group_name,
                "params": [param_payload(param) for param in params],
            }
            for group_name, params in feature.grouped_params()
        ],
    }


class ControlDeck:
    """Thread-safe application state shared by the browser API and child launcher."""

    def __init__(
        self,
        registry: FeatureRegistry | None = None,
        launcher: FeatureLauncher | None = None,
    ) -> None:
        self.registry = registry or load_registry()
        self.launcher = launcher or FeatureLauncher()
        self.values = {feature.id: feature.defaults() for feature in self.registry.features}
        self.lock = threading.RLock()

    def _state_payload(self) -> dict[str, Any]:
        state = self.launcher.poll()
        return {
            "feature_id": state.feature_id,
            "feature_name": state.feature_name,
            "pid": state.pid,
            "started_at": state.started_at,
            "returncode": state.returncode,
            "running": state.running,
            "log_path": str(state.log_path) if state.log_path else None,
        }

    def bootstrap(self) -> dict[str, Any]:
        with self.lock:
            return {
                "platform": current_platform(),
                "features": [_feature_payload(feature) for feature in self.registry.features],
                "values": self.values,
                "state": self._state_payload(),
            }

    def status(self, offset: int = 0) -> dict[str, Any]:
        with self.lock:
            state = self._state_payload()
            chunk, next_offset = self.launcher.read_log_since(offset)
            return {"state": state, "log": chunk, "log_offset": next_offset}

    def launch(self, feature_id: str, values: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            feature = self.registry.by_id(feature_id)
            merged = feature.defaults()
            merged.update(values)
            # Validate/coerce before replacing the remembered form state.
            feature.build_argv(merged)
            self.values[feature.id] = dict(merged)
            self.launcher.launch(feature, merged)
            return self._state_payload()

    def stop(self) -> dict[str, Any]:
        with self.lock:
            self.launcher.stop()
            return self._state_payload()

    def close(self) -> None:
        with self.lock:
            self.launcher.close()


class ControlDeckServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], deck: ControlDeck):
        self.deck = deck
        super().__init__(address, ControlDeckHandler)


class ControlDeckHandler(BaseHTTPRequestHandler):
    server: ControlDeckServer

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, exc: Exception, status: HTTPStatus = HTTPStatus.BAD_REQUEST) -> None:
        self._json({"error": f"{type(exc).__name__}: {exc}"}, status)

    def _body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 2_000_000:
            raise ValueError("request body too large")
        data = self.rfile.read(length) if length else b"{}"
        value = json.loads(data.decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("JSON body must be an object")
        return value

    def do_GET(self) -> None:
        path, _, query = self.path.partition("?")
        try:
            if path == "/":
                body = HTML.encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if path == "/api/bootstrap":
                self._json(self.server.deck.bootstrap())
                return
            if path == "/api/status":
                params = dict(
                    part.split("=", 1) if "=" in part else (part, "")
                    for part in query.split("&")
                    if part
                )
                self._json(self.server.deck.status(int(params.get("offset", "0") or 0)))
                return
            self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self._error(exc)

    def do_POST(self) -> None:
        try:
            data = self._body()
            if self.path == "/api/launch":
                feature_id = str(data.get("feature_id", ""))
                values = data.get("values", {})
                if not isinstance(values, dict):
                    raise ValueError("values must be an object")
                self._json({"state": self.server.deck.launch(feature_id, values)})
                return
            if self.path == "/api/stop":
                self._json({"state": self.server.deck.stop()})
                return
            self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
        except KeyError as exc:
            self._error(exc, HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self._error(exc)


HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ProjectionMapping Control Deck</title>
<style>
:root{color-scheme:dark;--bg:#07090f;--panel:#0e1220;--line:#242b42;--text:#eef1ff;--muted:#939bb8;--violet:#9d8cff;--cyan:#46e4ff;--green:#4cf2a1;--red:#ff6685}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 70% -20%,#20224a 0,transparent 40%),var(--bg);color:var(--text);font:14px Inter,ui-sans-serif,system-ui,sans-serif;height:100vh;overflow:hidden}
button,input,select{font:inherit}.shell{display:grid;grid-template-columns:310px minmax(0,1fr);height:100vh}.sidebar{border-right:1px solid var(--line);background:#090c15dd;padding:20px 14px;overflow:auto}.brand{font-weight:800;letter-spacing:.11em;font-size:15px;margin:2px 8px 18px}.brand span{color:var(--cyan)}
.search{width:100%;background:#111626;border:1px solid var(--line);color:var(--text);border-radius:10px;padding:10px 12px;outline:none;position:sticky;top:0;z-index:2}.category{color:var(--muted);font-size:11px;font-weight:800;letter-spacing:.14em;margin:20px 8px 7px}.feature{width:100%;text-align:left;border:1px solid transparent;background:transparent;color:#c9cee4;padding:10px 11px;border-radius:9px;cursor:pointer;margin:2px 0}.feature:hover{background:#151a2b}.feature.active{background:#1a2035;border-color:#3c4568;color:#fff}.feature small{display:block;color:#69718d;margin-top:3px}.feature.unavailable{opacity:.48}
.main{display:grid;grid-template-rows:auto minmax(0,1fr);overflow:hidden}.topbar{display:flex;align-items:center;gap:14px;padding:14px 22px;border-bottom:1px solid var(--line);background:#0a0d16cc}.status-dot{width:9px;height:9px;border-radius:50%;background:#69718d;box-shadow:0 0 0 4px #69718d18}.status-dot.running{background:var(--green);box-shadow:0 0 16px var(--green)}.status-copy{min-width:0;flex:1}.status-title{font-weight:800}.status-meta{color:var(--muted);font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.stop{border:1px solid #7f2e45;background:#351522;color:#ffb3c2;padding:9px 14px;border-radius:9px;cursor:pointer}.stop:disabled{opacity:.3;cursor:default}
.workspace{display:grid;grid-template-columns:minmax(460px,1fr) minmax(320px,.7fr);min-height:0}.editor{overflow:auto;padding:26px 30px 100px}.empty{color:var(--muted);max-width:620px;margin:80px auto;text-align:center}.title{font-size:27px;font-weight:850;letter-spacing:-.02em}.description{color:#aeb5ce;line-height:1.55;max-width:850px;margin:8px 0 24px}.warning{padding:11px 13px;border:1px solid #654925;background:#2c2113;color:#ffd99b;border-radius:9px;margin-bottom:18px}.group{border:1px solid var(--line);background:linear-gradient(145deg,#111625,#0d111d);border-radius:14px;padding:16px 17px;margin:13px 0}.group-title{font-weight:800;color:#b9b1ff;letter-spacing:.08em;font-size:12px;margin-bottom:10px}.field{display:grid;grid-template-columns:minmax(160px,.8fr) minmax(200px,1.2fr);gap:9px 18px;align-items:center;padding:9px 0;border-top:1px solid #20263a}.field:first-of-type{border-top:0}.field label{font-weight:650}.help{grid-column:1/-1;color:#737c9a;font-size:12px;margin-top:-5px}.control{width:100%;background:#090d17;border:1px solid #343d5c;border-radius:8px;color:var(--text);padding:9px 10px;outline:none}.control:focus{border-color:var(--violet);box-shadow:0 0 0 3px #9d8cff1c}.palette-control{display:grid;grid-template-columns:1fr 92px;gap:9px}.palette-preview{border:1px solid #46506e;border-radius:8px;min-height:38px;box-shadow:inset 0 0 12px #0007}.check{width:20px;height:20px;accent-color:var(--violet)}.launchbar{position:sticky;bottom:-82px;margin:24px -30px -100px;padding:18px 30px 26px;background:linear-gradient(transparent,#090c15 25%);display:flex;gap:10px}.launch{flex:1;border:0;border-radius:11px;background:linear-gradient(100deg,var(--violet),#6f7cff 55%,var(--cyan));color:#070911;font-weight:900;padding:13px 18px;cursor:pointer}.launch:disabled{filter:grayscale(1);opacity:.35;cursor:default}
.console{border-left:1px solid var(--line);background:#080b12;display:grid;grid-template-rows:auto minmax(0,1fr);min-height:0}.console-head{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;border-bottom:1px solid var(--line);font-weight:800}.console-head label{font-weight:500;color:var(--muted);font-size:12px}.log{margin:0;padding:16px;overflow:auto;white-space:pre-wrap;word-break:break-word;color:#b7f8d3;font:12px/1.55 ui-monospace,SFMono-Regular,Consolas,monospace}.toast{position:fixed;right:22px;bottom:22px;max-width:420px;background:#20263a;border:1px solid #4b557b;border-radius:11px;padding:12px 15px;box-shadow:0 12px 40px #0008;display:none}.toast.error{border-color:#9b3852;color:#ffc0cc}
@media(max-width:980px){body{overflow:auto;height:auto}.shell{grid-template-columns:1fr;height:auto}.sidebar{max-height:38vh;border-right:0;border-bottom:1px solid var(--line)}.main{height:auto}.workspace{grid-template-columns:1fr}.editor{min-height:600px}.console{height:440px;border-left:0;border-top:1px solid var(--line)}}
</style></head>
<body><div class="shell"><aside class="sidebar"><div class="brand">PROJECTION<span>MAPPING</span></div><input id="search" class="search" placeholder="Search features…"><div id="features"></div></aside><main class="main"><header class="topbar"><div id="dot" class="status-dot"></div><div class="status-copy"><div id="statusTitle" class="status-title">Control deck starting…</div><div id="statusMeta" class="status-meta"></div></div><button id="stop" class="stop" disabled>Stop visual</button></header><section class="workspace"><div id="editor" class="editor"><div class="empty"><div class="title">Choose a visual instrument</div><p>Configure it here, launch fullscreen, press ESC in the projector window, and continue with the same settings.</p></div></div><aside class="console"><div class="console-head"><span>RUN LOG</span><label><input id="autoscroll" type="checkbox" checked> follow</label></div><pre id="log" class="log">No run log yet.</pre></aside></section></main></div><div id="toast" class="toast"></div>
<script>
const app={data:null,selected:null,drafts:{},offset:0,logPath:null};
const $=s=>document.querySelector(s); const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function toast(message,error=false){const t=$('#toast');t.textContent=message;t.className='toast'+(error?' error':'');t.style.display='block';clearTimeout(t._timer);t._timer=setTimeout(()=>t.style.display='none',5000)}
async function api(path,options={}){const r=await fetch(path,{headers:{'Content-Type':'application/json'},...options});const d=await r.json();if(!r.ok||d.error)throw new Error(d.error||`HTTP ${r.status}`);return d}
function renderFeatures(filter=''){const root=$('#features');root.innerHTML='';const query=filter.trim().toLowerCase();const cats=[...new Set(app.data.features.map(f=>f.category))];for(const cat of cats){const fs=app.data.features.filter(f=>f.category===cat&&(!query||(f.name+' '+f.description).toLowerCase().includes(query)));if(!fs.length)continue;root.insertAdjacentHTML('beforeend',`<div class="category">${esc(cat)}</div>`);for(const f of fs){const b=document.createElement('button');b.className='feature '+(f.id===app.selected?'active ':'')+(!f.available?'unavailable':'');b.innerHTML=`${esc(f.name)}<small>${f.available?'ready':esc(f.availability_hint)}</small>`;b.onclick=()=>selectFeature(f.id);root.appendChild(b)}}}
function draftFor(f){return app.drafts[f.id]||(app.drafts[f.id]={...(app.data.values[f.id]||{})})}
function selectFeature(id){app.selected=id;renderFeatures($('#search').value);const f=app.data.features.find(x=>x.id===id),v=draftFor(f),e=$('#editor');let html=`<div class="title">${esc(f.name)}</div><div class="description">${esc(f.description)}</div>`;if(!f.available)html+=`<div class="warning">${esc(f.availability_hint)}</div>`;for(const g of f.groups){html+=`<section class="group"><div class="group-title">${esc(g.name).toUpperCase()}</div>`;for(const p of g.params){const id='p-'+p.key;html+=`<div class="field"><label for="${esc(id)}">${esc(p.label)}</label>`;if(p.type==='choice'){const select=`<select class="control" id="${esc(id)}">${p.choices.map(c=>`<option value="${esc(c)}" ${String(v[p.key])===String(c)?'selected':''}>${esc(p.choice_labels?.[c]||c)}</option>`).join('')}</select>`;html+=p.swatches?`<div class="palette-control">${select}<div id="${esc(id)}-swatch" class="palette-preview"></div></div>`:select}else if(p.type==='bool'){html+=`<input class="check" id="${esc(id)}" type="checkbox" ${v[p.key]?'checked':''}>`}else{const type=(p.type==='int'||p.type==='float')?'number':'text',step=p.type==='int'?'1':p.type==='float'?'any':'';html+=`<input class="control" id="${esc(id)}" type="${type}" value="${esc(v[p.key])}" ${step?`step="${step}"`:''} ${p.min!=null?`min="${p.min}"`:''} ${p.max!=null?`max="${p.max}"`:''}>`}if(p.help)html+=`<div class="help">${esc(p.help)}</div>`;html+='</div>'}html+='</section>'}html+=`<div class="launchbar"><button id="launch" class="launch" ${f.available?'':'disabled'}>Launch fullscreen</button></div>`;e.innerHTML=html;for(const p of f.groups.flatMap(g=>g.params)){const input=$('#p-'+CSS.escape(p.key));const update=()=>{v[p.key]=p.type==='bool'?input.checked:input.value;if(p.swatches){const swatch=$('#p-'+CSS.escape(p.key)+'-swatch');swatch.style.background=p.swatches[input.value]||'#111'}};input.oninput=update;update()}$('#launch').onclick=launchSelected;e.scrollTop=0}
async function launchSelected(){const f=app.data.features.find(x=>x.id===app.selected);try{await api('/api/launch',{method:'POST',body:JSON.stringify({feature_id:f.id,values:draftFor(f)})});app.offset=0;app.logPath=null;$('#log').textContent='';toast(`Launched ${f.name}`);await poll()}catch(e){toast(e.message,true)}}
function showState(s){$('#dot').classList.toggle('running',s.running);$('#statusTitle').textContent=s.running?`RUNNING · ${s.feature_name}`:s.feature_name?`IDLE · ${s.feature_name}`:'IDLE';$('#statusMeta').textContent=s.running?`PID ${s.pid} · started ${s.started_at}`:s.returncode!=null?`last exit ${s.returncode}`:'Choose a feature';$('#stop').disabled=!s.running;if(s.log_path!==app.logPath){app.logPath=s.log_path;app.offset=0;$('#log').textContent=''}}
async function poll(){try{const d=await api('/api/status?offset='+app.offset);showState(d.state);if(d.log){const log=$('#log'),follow=$('#autoscroll').checked;log.textContent=(log.textContent==='No run log yet.'?'':log.textContent)+d.log;if(log.textContent.length>200000)log.textContent=log.textContent.slice(-200000);if(follow)log.scrollTop=log.scrollHeight}app.offset=d.log_offset}catch(e){toast(e.message,true)}}
$('#search').oninput=e=>renderFeatures(e.target.value);$('#stop').onclick=async()=>{try{await api('/api/stop',{method:'POST',body:'{}'});toast('Visual process tree stopped');await poll()}catch(e){toast(e.message,true)}};
(async()=>{try{app.data=await api('/api/bootstrap');showState(app.data.state);renderFeatures();if(app.data.features.length)selectFeature(app.data.features[0].id);setInterval(poll,750);await poll()}catch(e){toast(e.message,true)}})();
</script></body></html>"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ProjectionMapping browser control deck")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--allow-remote", action="store_true")
    parser.add_argument("--registry", default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.host not in {"127.0.0.1", "localhost", "::1"} and not args.allow_remote:
        raise SystemExit("Refusing a non-loopback bind without --allow-remote")
    deck = ControlDeck(registry=load_registry(args.registry))
    server = ControlDeckServer((args.host, args.port), deck)
    url = f"http://{args.host}:{server.server_port}/"
    print(f"ProjectionMapping control deck: {url}", flush=True)
    if not args.no_browser:
        threading.Timer(0.35, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        deck.close()


if __name__ == "__main__":
    main()

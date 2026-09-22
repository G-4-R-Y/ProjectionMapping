from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import queue
import threading
from typing import Any, Iterable, Mapping

import numpy as np

from .app_runtime import runtime_root


HOT_CUES: tuple[str, ...] = (
    "liquid_intro",
    "membrane_drift",
    "data_build",
    "mercury_rise",
    "cathedral_release",
    "reactor_release",
    "singularity_drop",
    "afterglow",
)

MIDI_NOTE_BASE = 36
MIDI_NEXT_NOTE = 44
MIDI_SAVE_A_NOTE = 45
MIDI_LOAD_A_NOTE = 46
MIDI_SAVE_B_NOTE = 47
MIDI_LOAD_B_NOTE = 48


@dataclass(frozen=True)
class ControlEvent:
    action: str
    args: tuple[Any, ...] = ()


@dataclass(frozen=True)
class PerformanceSnapshot:
    name: str
    cue: str
    journey: str
    mode: str
    madness: float


class PerformanceControlBus:
    """Thread-safe event inbox for keyboard, MIDI and OSC adapters."""

    def __init__(self) -> None:
        self._queue: queue.SimpleQueue[ControlEvent] = queue.SimpleQueue()

    def emit(self, action: str, *args: Any) -> None:
        self._queue.put(ControlEvent(action, tuple(args)))

    def drain(self, limit: int = 128) -> list[ControlEvent]:
        out: list[ControlEvent] = []
        for _ in range(max(1, int(limit))):
            try:
                out.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return out


class PerformanceStateStore:
    """Persistent user journeys + named snapshots under the runtime directory."""

    VERSION = 1

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path).expanduser() if path else runtime_root() / "performance_states.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _empty(self) -> dict[str, Any]:
        return {"version": self.VERSION, "snapshots": {}, "journeys": {}}

    def load(self) -> dict[str, Any]:
        with self._lock:
            if not self.path.exists():
                return self._empty()
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return self._empty()
            if not isinstance(raw, dict):
                return self._empty()
            snapshots = raw.get("snapshots")
            journeys = raw.get("journeys")
            return {
                "version": self.VERSION,
                "snapshots": snapshots if isinstance(snapshots, dict) else {},
                "journeys": journeys if isinstance(journeys, dict) else {},
            }

    def _write(self, data: Mapping[str, Any]) -> None:
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self.path)

    def snapshots(self) -> dict[str, PerformanceSnapshot]:
        raw = self.load()["snapshots"]
        result: dict[str, PerformanceSnapshot] = {}
        for name, payload in raw.items():
            if not isinstance(payload, dict):
                continue
            try:
                result[str(name)] = PerformanceSnapshot(
                    name=str(name),
                    cue=str(payload["cue"]),
                    journey=str(payload["journey"]),
                    mode=str(payload["mode"]),
                    madness=float(np.clip(float(payload["madness"]), 0.0, 1.0)),
                )
            except (KeyError, TypeError, ValueError):
                continue
        return result

    def save_snapshot(self, snapshot: PerformanceSnapshot) -> None:
        data = self.load()
        data["snapshots"][snapshot.name] = {
            key: value for key, value in asdict(snapshot).items() if key != "name"
        }
        with self._lock:
            self._write(data)

    def get_snapshot(self, name: str) -> PerformanceSnapshot | None:
        return self.snapshots().get(name)

    def journeys(self) -> dict[str, tuple[str, ...]]:
        raw = self.load()["journeys"]
        result: dict[str, tuple[str, ...]] = {}
        for name, cues in raw.items():
            if not isinstance(cues, list):
                continue
            seq = tuple(str(cue) for cue in cues if str(cue))
            if seq:
                result[str(name)] = seq
        return result

    def save_journey(self, name: str, cues: Iterable[str]) -> None:
        name = str(name).strip()
        seq = tuple(str(cue).strip() for cue in cues if str(cue).strip())
        if not name:
            raise ValueError("journey name cannot be empty")
        if not seq:
            raise ValueError("journey must contain at least one cue")
        data = self.load()
        data["journeys"][name] = list(seq)
        with self._lock:
            self._write(data)


class OSCControlServer:
    """Small localhost-first OSC adapter. Import dependency only when enabled."""

    def __init__(
        self,
        bus: PerformanceControlBus,
        host: str = "127.0.0.1",
        port: int = 9000,
    ) -> None:
        self.bus = bus
        self.host = host
        self.port = int(port)
        self._server = None
        self._thread: threading.Thread | None = None

    def start(self) -> "OSCControlServer":
        if self.port <= 0:
            return self
        try:
            from pythonosc.dispatcher import Dispatcher
            from pythonosc.osc_server import ThreadingOSCUDPServer
        except ImportError as exc:
            raise RuntimeError(
                "OSC control requires the controls extra: python -m pip install -e '.[controls]'"
            ) from exc

        dispatcher = Dispatcher()
        dispatcher.map("/pm/madness", lambda _addr, value: self.bus.emit("madness", float(value)))
        dispatcher.map("/pm/cue", lambda _addr, cue: self.bus.emit("cue", str(cue)))
        dispatcher.map("/pm/next", lambda _addr, *_args: self.bus.emit("next"))
        dispatcher.map("/pm/mode", lambda _addr, mode: self.bus.emit("mode", str(mode)))
        dispatcher.map("/pm/journey", lambda _addr, name: self.bus.emit("journey", str(name)))
        dispatcher.map(
            "/pm/journey/save",
            lambda _addr, name, *cues: self.bus.emit(
                "journey_save", str(name), *(str(cue) for cue in cues)
            ),
        )
        dispatcher.map(
            "/pm/snapshot/save",
            lambda _addr, name: self.bus.emit("snapshot_save", str(name)),
        )
        dispatcher.map(
            "/pm/snapshot/load",
            lambda _addr, name: self.bus.emit("snapshot_load", str(name)),
        )

        self._server = ThreadingOSCUDPServer((self.host, self.port), dispatcher)
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="pm-osc-control",
            daemon=True,
        )
        self._thread.start()
        return self

    def close(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        self._server = None
        self._thread = None

    def __enter__(self) -> "OSCControlServer":
        return self.start()

    def __exit__(self, *_exc) -> None:
        self.close()


class MIDIControlInput:
    """MIDI adapter with a stable default performance mapping.

    CC1 -> MADNESS
    notes 36..43 -> eight hot cues
    note 44 -> next cue
    notes 45/46 -> save/load A
    notes 47/48 -> save/load B
    program changes -> journey index
    """

    def __init__(
        self,
        bus: PerformanceControlBus,
        *,
        device: str | None = None,
        madness_cc: int = 1,
        note_base: int = MIDI_NOTE_BASE,
        journey_names: Iterable[str] = (),
        mode: str = "controls",
        piano_hot_cues: bool = False,
        piano_cue_note_base: int = 21,
    ) -> None:
        if mode not in {"controls", "piano"}:
            raise ValueError(f"unknown MIDI mode: {mode}")
        self.bus = bus
        self.device = device or None
        self.madness_cc = int(np.clip(madness_cc, 0, 127))
        self.note_base = int(np.clip(note_base, 0, 120))
        self.journey_names = tuple(journey_names)
        self.mode = mode
        self._port = None
        self.piano = None
        if self.mode == "piano":
            from .piano_performance import PianoMIDIInterpreter

            self.piano = PianoMIDIInterpreter(
                bus,
                hot_cues=piano_hot_cues,
                cue_note_base=piano_cue_note_base,
                cue_names=HOT_CUES,
            )

    @staticmethod
    def list_devices() -> tuple[str, ...]:
        try:
            import mido
            mido.set_backend("mido.backends.rtmidi")
        except ImportError as exc:
            raise RuntimeError(
                "MIDI control requires the controls extra: python -m pip install -e '.[controls]'"
            ) from exc
        return tuple(mido.get_input_names())

    def _callback(self, message) -> None:
        msg_type = getattr(message, "type", "")
        if msg_type == "control_change" and int(message.control) == self.madness_cc:
            self.bus.emit("madness", float(message.value) / 127.0)
            if self.mode != "piano":
                return
        if msg_type == "program_change" and self.journey_names:
            index = int(message.program) % len(self.journey_names)
            self.bus.emit("journey", self.journey_names[index])
            return

        if self.mode == "piano":
            if self.piano is not None:
                self.piano.feed(message)
            return

        if msg_type != "note_on" or int(getattr(message, "velocity", 0)) <= 0:
            return

        note = int(message.note)
        index = note - self.note_base
        if 0 <= index < len(HOT_CUES):
            self.bus.emit("cue", HOT_CUES[index])
        elif note == self.note_base + 8:
            self.bus.emit("next")
        elif note == self.note_base + 9:
            self.bus.emit("snapshot_save", "A")
        elif note == self.note_base + 10:
            self.bus.emit("snapshot_load", "A")
        elif note == self.note_base + 11:
            self.bus.emit("snapshot_save", "B")
        elif note == self.note_base + 12:
            self.bus.emit("snapshot_load", "B")

    def piano_expression(self, *, now: float | None = None):
        if self.piano is None:
            return None
        return self.piano.expression(now=now)

    def start(self) -> "MIDIControlInput":
        try:
            import mido
            mido.set_backend("mido.backends.rtmidi")
        except ImportError as exc:
            raise RuntimeError(
                "MIDI control requires the controls extra: python -m pip install -e '.[controls]'"
            ) from exc

        names = list(mido.get_input_names())
        if self.device:
            needle = self.device.lower()
            match = next((name for name in names if needle in name.lower()), None)
            if match is None:
                raise RuntimeError(f"MIDI input not found: {self.device!r}; available={names}")
            name = match
        else:
            if not names:
                raise RuntimeError("No MIDI input devices were found.")
            name = names[0]
        self._port = mido.open_input(name, callback=self._callback)
        self.device = name
        return self

    def close(self) -> None:
        if self._port is not None:
            self._port.close()
        self._port = None

    def __enter__(self) -> "MIDIControlInput":
        return self.start()

    def __exit__(self, *_exc) -> None:
        self.close()



class MIDIStateOutput:
    """Optional CC-only feedback for hardware controllers/pianos.

    No note messages are sent. CC20..24 carry MADNESS, cue index, section, energy and quantize mode.
    """

    SECTION_VALUES = {
        "steady": 0,
        "breakdown": 28,
        "build": 64,
        "drop": 127,
        "release": 92,
    }

    def __init__(
        self,
        *,
        device: str | None = None,
        cc_base: int = 20,
        channel: int = 0,
    ) -> None:
        self.device = device or None
        self.cc_base = int(np.clip(cc_base, 0, 123))
        self.channel = int(np.clip(channel, 0, 15))
        self._port = None
        self._last: tuple[int, ...] | None = None

    @staticmethod
    def list_devices() -> tuple[str, ...]:
        try:
            import mido

            mido.set_backend("mido.backends.rtmidi")
        except ImportError as exc:
            raise RuntimeError(
                "MIDI feedback requires the controls extra: python -m pip install -e '.[controls]'"
            ) from exc
        return tuple(mido.get_output_names())

    def start(self) -> "MIDIStateOutput":
        try:
            import mido

            mido.set_backend("mido.backends.rtmidi")
        except ImportError as exc:
            raise RuntimeError(
                "MIDI feedback requires the controls extra: python -m pip install -e '.[controls]'"
            ) from exc

        names = list(mido.get_output_names())
        if self.device:
            needle = self.device.lower()
            match = next((name for name in names if needle in name.lower()), None)
            if match is None:
                raise RuntimeError(f"MIDI output not found: {self.device!r}; available={names}")
            name = match
        else:
            if not names:
                raise RuntimeError("No MIDI output devices were found.")
            name = names[0]
        self._port = mido.open_output(name)
        self.device = name
        return self

    def send(
        self,
        *,
        madness: float,
        cue: str,
        section: str,
        energy: float,
        quantize: str,
    ) -> None:
        if self._port is None:
            return
        import mido

        cue_index = HOT_CUES.index(cue) if cue in HOT_CUES else 0
        quantize_value = {"off": 0, "beat": 64, "bar": 127}.get(quantize, 0)
        values = (
            int(np.clip(round(madness * 127.0), 0, 127)),
            int(np.clip(cue_index * 16, 0, 127)),
            int(self.SECTION_VALUES.get(section, 0)),
            int(np.clip(round(energy * 127.0), 0, 127)),
            quantize_value,
        )
        if values == self._last:
            return
        self._last = values
        for offset, value in enumerate(values):
            self._port.send(
                mido.Message(
                    "control_change",
                    channel=self.channel,
                    control=self.cc_base + offset,
                    value=value,
                )
            )

    def close(self) -> None:
        if self._port is not None:
            self._port.close()
        self._port = None
        self._last = None


def keyboard_events(key: int) -> tuple[ControlEvent, ...]:
    """Map OpenCV keycodes into performance events without owning the display loop."""

    if key < 0:
        return ()
    code = key & 0xFF
    if ord("1") <= code <= ord("8"):
        return (ControlEvent("cue", (HOT_CUES[code - ord("1")],)),)
    if code in (ord("n"), ord("N")):
        return (ControlEvent("next"),)
    if code in (ord("]"), ord("+"), ord("=")):
        return (ControlEvent("madness_delta", (0.05,)),)
    if code in (ord("["), ord("-"), ord("_")):
        return (ControlEvent("madness_delta", (-0.05,)),)
    if code == ord("a"):
        return (ControlEvent("snapshot_save", ("A",)),)
    if code == ord("A"):
        return (ControlEvent("snapshot_load", ("A",)),)
    if code == ord("b"):
        return (ControlEvent("snapshot_save", ("B",)),)
    if code == ord("B"):
        return (ControlEvent("snapshot_load", ("B",)),)
    if code in (ord("r"), ord("R")):
        return (ControlEvent("loop_record_toggle"),)
    if code in (ord("l"), ord("L")):
        return (ControlEvent("loop_stop"),)
    if code in (ord("c"), ord("C")):
        return (ControlEvent("loop_clear"),)
    return ()


__all__ = [
    "ControlEvent",
    "HOT_CUES",
    "MIDIControlInput",
    "MIDIStateOutput",
    "OSCControlServer",
    "PerformanceControlBus",
    "PerformanceSnapshot",
    "PerformanceStateStore",
    "keyboard_events",
]

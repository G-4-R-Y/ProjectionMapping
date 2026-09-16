from __future__ import annotations

from dataclasses import dataclass

from .performance_bus import PerformanceState


@dataclass(frozen=True)
class OscAddressSchema:
    root: str = "/pm"

    def anchor(self, name: str) -> str:
        return f"{self.root}/tracking/{name}"

    def gesture(self, name: str) -> str:
        return f"{self.root}/event/{name}"

    def music(self, name: str) -> str:
        return f"{self.root}/music/{name}"

    def control(self, name: str) -> str:
        return f"{self.root}/control/{name}"


class OscPerformancePublisher:
    """Renderer-agnostic OSC publisher for optional external tools.

    TouchDesigner is one possible consumer, but this contract is deliberately generic: Max,
    Pure Data, Processing, Unity, Godot, Unreal bridges, or another ProjectionMapping process
    can consume the same state. The open-source core never depends on OSC being present.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 9000, root: str = "/pm") -> None:
        try:
            from pythonosc.udp_client import SimpleUDPClient
        except ImportError as exc:
            raise RuntimeError(
                "OSC interoperability requires `python -m pip install -e '.[interop]'`."
            ) from exc
        self.client = SimpleUDPClient(host, int(port))
        self.schema = OscAddressSchema(root=root.rstrip("/"))

    def publish(self, state: PerformanceState) -> None:
        t = state.tracking
        self.client.send_message(f"{self.schema.root}/timestamp", float(state.timestamp))
        self.client.send_message(f"{self.schema.root}/tracking/confidence", float(t.performer_confidence))
        self.client.send_message(f"{self.schema.root}/tracking/source", str(t.source))

        for anchor in t.anchors:
            self.client.send_message(
                self.schema.anchor(anchor.name),
                [
                    float(anchor.position.x),
                    float(anchor.position.y),
                    float(anchor.position.z),
                    float(anchor.velocity.x),
                    float(anchor.velocity.y),
                    float(anchor.velocity.z),
                    float(anchor.confidence),
                ],
            )
        for event in t.gestures:
            self.client.send_message(
                self.schema.gesture(event.name),
                [float(event.strength), str(event.phase), str(event.source_anchor or ""), str(event.target_anchor or "")],
            )
        for event in t.room_events:
            self.client.send_message(
                f"{self.schema.root}/room/{event.name}",
                [float(event.uv[0]), float(event.uv[1]), float(event.strength), str(event.surface)],
            )

        m = state.music
        if m is not None:
            fields = (
                "loudness", "bass", "mids", "highs", "color", "strike", "beat", "ascension",
                "tempo_bpm", "beat_phase", "bar_phase", "beat_confidence", "section_energy", "drop",
            )
            for field in fields:
                self.client.send_message(self.schema.music(field), float(getattr(m, field)))
        for key, value in state.controls.items():
            self.client.send_message(self.schema.control(key), value)


__all__ = ["OscAddressSchema", "OscPerformancePublisher"]

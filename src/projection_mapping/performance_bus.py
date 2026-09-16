from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
from typing import Iterable

from .music_reactivity import MusicalSignals


@dataclass(frozen=True)
class Vec3:
    x: float
    y: float
    z: float = 0.0

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def distance(self, other: "Vec3") -> float:
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z).length()


@dataclass(frozen=True)
class AnchorState:
    """Stable semantic point in normalized camera coordinates.

    x/y are [0,1] image coordinates, z is tracker-defined camera-relative depth.
    Velocity is normalized units/second so renderers do not depend on camera resolution.
    """

    name: str
    position: Vec3
    velocity: Vec3 = Vec3(0.0, 0.0, 0.0)
    confidence: float = 0.0
    normal: Vec3 | None = None
    handedness: str | None = None
    source: str = "unknown"

    @property
    def speed(self) -> float:
        return self.velocity.length()


@dataclass(frozen=True)
class MotionPoint:
    id: int
    position: Vec3
    velocity: Vec3
    confidence: float = 1.0
    age: float = 0.0

    @property
    def speed(self) -> float:
        return self.velocity.length()


@dataclass(frozen=True)
class GestureEvent:
    name: str
    strength: float
    phase: str = "active"  # begin / active / release / impulse
    source_anchor: str | None = None
    target_anchor: str | None = None
    payload: dict[str, float | str | bool] = field(default_factory=dict)


@dataclass(frozen=True)
class RoomAnchorEvent:
    name: str
    uv: tuple[float, float]
    strength: float
    surface: str = "unknown"
    world_xyz: tuple[float, float, float] | None = None


@dataclass(frozen=True)
class TrackingState:
    timestamp: float
    frame_size: tuple[int, int]
    anchors: tuple[AnchorState, ...] = ()
    motion_points: tuple[MotionPoint, ...] = ()
    gestures: tuple[GestureEvent, ...] = ()
    room_events: tuple[RoomAnchorEvent, ...] = ()
    performer_confidence: float = 0.0
    source: str = "none"

    def anchor(self, name: str, minimum_confidence: float = 0.0) -> AnchorState | None:
        for anchor in self.anchors:
            if anchor.name == name and anchor.confidence >= minimum_confidence:
                return anchor
        return None

    def anchors_with_prefix(self, prefix: str) -> tuple[AnchorState, ...]:
        return tuple(a for a in self.anchors if a.name.startswith(prefix))


@dataclass(frozen=True)
class PerformanceState:
    """One immutable snapshot shared by every realtime visual subsystem."""

    timestamp: float
    tracking: TrackingState
    music: MusicalSignals | None = None
    controls: dict[str, float | str | bool] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def merge_gestures(state: TrackingState, gestures: Iterable[GestureEvent]) -> TrackingState:
    return TrackingState(
        timestamp=state.timestamp,
        frame_size=state.frame_size,
        anchors=state.anchors,
        motion_points=state.motion_points,
        gestures=tuple(gestures),
        room_events=state.room_events,
        performer_confidence=state.performer_confidence,
        source=state.source,
    )


__all__ = [
    "Vec3",
    "AnchorState",
    "MotionPoint",
    "GestureEvent",
    "RoomAnchorEvent",
    "TrackingState",
    "PerformanceState",
    "merge_gestures",
]

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
import math

import numpy as np

from .performance_bus import AnchorState, GestureEvent, TrackingState, merge_gestures


@dataclass(frozen=True)
class SpellThresholds:
    charge_distance: float = 0.18
    charge_speed: float = 0.42
    charge_seconds: float = 0.45
    release_distance: float = 0.30
    slash_speed: float = 1.15
    slash_refractory: float = 0.28
    shield_distance: float = 0.34
    shield_speed: float = 0.36
    ascension_margin: float = 0.04
    portal_min_samples: int = 18
    portal_min_angular_travel: float = 4.6
    portal_radius_cv: float = 0.38


class SpellGrammar:
    """Stateful performer-event grammar driven by *real* semantic anchors.

    The grammar never fabricates hands. Missing/low-confidence anchors simply disable the
    corresponding spell. Continuous renderer state should use anchors directly; this layer emits
    sparse semantic events (charge/release/slash/shield/portal/ascension) for choreography.
    """

    def __init__(self, thresholds: SpellThresholds | None = None) -> None:
        self.t = thresholds or SpellThresholds()
        self._charge = 0.0
        self._last_time: float | None = None
        self._was_charging = False
        self._last_slash: dict[str, float] = defaultdict(lambda: -999.0)
        self._shield_active = False
        self._ascension_active = False
        self._paths: dict[str, deque[tuple[float, float, float]]] = {
            "left_palm": deque(maxlen=44),
            "right_palm": deque(maxlen=44),
        }
        self._portal_latched: dict[str, bool] = defaultdict(bool)

    @staticmethod
    def _good(state: TrackingState, name: str, confidence: float = 0.35) -> AnchorState | None:
        return state.anchor(name, confidence)

    @staticmethod
    def _distance(a: AnchorState, b: AnchorState) -> float:
        dx = a.position.x - b.position.x
        dy = a.position.y - b.position.y
        return math.hypot(dx, dy)

    @staticmethod
    def _speed2(a: AnchorState) -> float:
        return math.hypot(a.velocity.x, a.velocity.y)

    def _portal_event(self, name: str, anchor: AnchorState, now: float) -> GestureEvent | None:
        path = self._paths[name]
        path.append((anchor.position.x, anchor.position.y, now))
        if len(path) < self.t.portal_min_samples:
            return None
        pts = np.asarray([(x, y) for x, y, _ in path], dtype=np.float32)
        centre = np.mean(pts, axis=0)
        rel = pts - centre
        radii = np.linalg.norm(rel, axis=1)
        mean_r = float(np.mean(radii))
        if mean_r < 0.035:
            self._portal_latched[name] = False
            return None
        cv = float(np.std(radii) / max(mean_r, 1e-6))
        angles = np.unwrap(np.arctan2(rel[:, 1], rel[:, 0]))
        angular_travel = float(abs(angles[-1] - angles[0]))
        if angular_travel >= self.t.portal_min_angular_travel and cv <= self.t.portal_radius_cv:
            if not self._portal_latched[name]:
                self._portal_latched[name] = True
                strength = float(np.clip((angular_travel - 4.0) / 2.5, 0.45, 1.0))
                return GestureEvent(
                    "portal_open",
                    strength,
                    phase="impulse",
                    source_anchor=name,
                    payload={"cx": float(centre[0]), "cy": float(centre[1]), "radius": mean_r},
                )
        elif angular_travel < 2.0:
            self._portal_latched[name] = False
        return None

    def update(self, state: TrackingState) -> TrackingState:
        now = state.timestamp
        dt = 1.0 / 60.0 if self._last_time is None else float(np.clip(now - self._last_time, 1e-4, 0.2))
        self._last_time = now
        events: list[GestureEvent] = []

        left = self._good(state, "left_palm")
        right = self._good(state, "right_palm")
        if left and right:
            distance = self._distance(left, right)
            calm = max(self._speed2(left), self._speed2(right)) <= self.t.charge_speed
            charging = distance <= self.t.charge_distance and calm
            if charging:
                self._charge = min(1.0, self._charge + dt / max(self.t.charge_seconds, 1e-3))
                events.append(
                    GestureEvent(
                        "charge_orb",
                        self._charge,
                        phase="begin" if not self._was_charging else "active",
                        source_anchor="left_palm",
                        target_anchor="right_palm",
                    )
                )
            elif self._was_charging and self._charge >= 0.55 and distance >= self.t.release_distance:
                events.append(
                    GestureEvent(
                        "charge_release",
                        self._charge,
                        phase="impulse",
                        source_anchor="left_palm",
                        target_anchor="right_palm",
                    )
                )
                self._charge = 0.0
            else:
                self._charge *= math.exp(-dt * 4.2)
            self._was_charging = charging

            avg_speed = (self._speed2(left) + self._speed2(right)) * 0.5
            shield = distance >= self.t.shield_distance and avg_speed <= self.t.shield_speed
            if shield:
                events.append(
                    GestureEvent(
                        "shield_dome",
                        float(np.clip((distance - self.t.shield_distance) / 0.25 + 0.35, 0.0, 1.0)),
                        phase="begin" if not self._shield_active else "active",
                        source_anchor="left_palm",
                        target_anchor="right_palm",
                    )
                )
            elif self._shield_active:
                events.append(GestureEvent("shield_dome", 0.0, phase="release"))
            self._shield_active = shield

        for name in ("left_palm", "right_palm"):
            anchor = self._good(state, name)
            if not anchor:
                continue
            speed = self._speed2(anchor)
            if speed >= self.t.slash_speed and now - self._last_slash[name] >= self.t.slash_refractory:
                strength = float(np.clip((speed - self.t.slash_speed) / 1.8 + 0.35, 0.0, 1.0))
                events.append(
                    GestureEvent(
                        "slash_trail",
                        strength,
                        phase="impulse",
                        source_anchor=name,
                        payload={"vx": anchor.velocity.x, "vy": anchor.velocity.y},
                    )
                )
                self._last_slash[name] = now
            portal = self._portal_event(name, anchor, now)
            if portal:
                events.append(portal)

        head = self._good(state, "head")
        left_wrist = self._good(state, "left_wrist") or left
        right_wrist = self._good(state, "right_wrist") or right
        ascension = bool(
            head
            and left_wrist
            and right_wrist
            and left_wrist.position.y < head.position.y + self.t.ascension_margin
            and right_wrist.position.y < head.position.y + self.t.ascension_margin
        )
        if ascension:
            events.append(
                GestureEvent(
                    "ascension_aura",
                    1.0,
                    phase="begin" if not self._ascension_active else "active",
                )
            )
        elif self._ascension_active:
            events.append(GestureEvent("ascension_aura", 0.0, phase="release"))
        self._ascension_active = ascension

        return merge_gestures(state, events)


__all__ = ["SpellThresholds", "SpellGrammar"]

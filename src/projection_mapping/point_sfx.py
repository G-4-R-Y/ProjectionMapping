from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
import math

import cv2
import numpy as np

from .point_tracker import TrackedPoint


PALETTES: dict[str, tuple[tuple[int, int, int], ...]] = {
    "cyber": ((35, 235, 255), (255, 70, 220), (120, 80, 255), (210, 255, 255)),
    "ion": ((255, 180, 40), (70, 245, 255), (255, 90, 150), (245, 250, 255)),
    "acid": ((90, 255, 120), (0, 225, 255), (255, 70, 230), (235, 255, 190)),
    "ember": ((0, 90, 255), (0, 210, 255), (80, 40, 255), (235, 245, 255)),
    "ice": ((255, 235, 160), (255, 120, 50), (220, 70, 255), (255, 255, 255)),
}


@dataclass
class Shockwave:
    x: float
    y: float
    radius: float
    velocity: float
    life: float
    color_index: int


class PointSFXRenderer:
    """Persistent point-track SFX renderer with additive trails, mesh, sparks and shockwaves."""

    def __init__(
        self,
        width: int,
        height: int,
        *,
        mode: str = "plasma_mesh",
        palette: str = "cyber",
        trail_length: int = 24,
        feedback: float = 0.91,
        connection_radius: float = 95.0,
        point_radius: float = 2.2,
        bloom: float = 1.0,
    ) -> None:
        self.width = int(width)
        self.height = int(height)
        self.mode = mode
        self.palette_name = palette if palette in PALETTES else "cyber"
        self.trail_length = max(2, int(trail_length))
        self.feedback_decay = float(np.clip(feedback, 0.0, 0.985))
        self.connection_radius = float(max(connection_radius, 12.0))
        self.point_radius = float(max(point_radius, 0.5))
        self.bloom = float(max(bloom, 0.0))
        self.feedback = np.zeros((self.height, self.width, 3), dtype=np.float32)
        self.histories: dict[int, deque[tuple[float, float, float]]] = defaultdict(
            lambda: deque(maxlen=self.trail_length)
        )
        self.previous_speed: dict[int, float] = {}
        self.shockwaves: list[Shockwave] = []
        self.frame_index = 0

    @property
    def palette(self) -> tuple[tuple[int, int, int], ...]:
        return PALETTES[self.palette_name]

    def _color(self, pid: int, energy: float = 0.0) -> tuple[int, int, int]:
        palette = self.palette
        base = np.asarray(palette[pid % len(palette)], dtype=np.float32)
        hi = np.asarray(palette[-1], dtype=np.float32)
        mix = float(np.clip(energy, 0.0, 1.0))
        return tuple(np.clip(base * (1.0 - mix * 0.45) + hi * (mix * 0.45), 0, 255).astype(np.uint8))

    def _draw_track(self, layer: np.ndarray, p: TrackedPoint) -> None:
        hist = self.histories[p.id]
        hist.append((p.x, p.y, p.speed))
        if len(hist) < 2:
            return
        items = list(hist)
        speed_energy = float(np.clip(p.speed / 12.0, 0.0, 1.0))
        color = self._color(p.id, speed_energy)
        for i in range(1, len(items)):
            age_alpha = i / max(len(items) - 1, 1)
            x0, y0, s0 = items[i - 1]
            x1, y1, s1 = items[i]
            local = float(np.clip((s0 + s1) / 18.0, 0.0, 1.0))
            c = tuple(int(v * (0.18 + 0.82 * age_alpha)) for v in color)
            thickness = max(1, int(1 + local * 3 + age_alpha * 1.2))
            cv2.line(layer, (int(x0), int(y0)), (int(x1), int(y1)), c, thickness, cv2.LINE_AA)

    def _draw_connections(self, layer: np.ndarray, points: list[TrackedPoint]) -> None:
        if self.mode not in {"plasma_mesh", "constellation", "liquid_wire"}:
            return
        radius2 = self.connection_radius * self.connection_radius
        pts = points[:120]
        for i in range(len(pts)):
            a = pts[i]
            for j in range(i + 1, len(pts)):
                b = pts[j]
                dx = a.x - b.x
                dy = a.y - b.y
                d2 = dx * dx + dy * dy
                if d2 >= radius2:
                    continue
                closeness = 1.0 - math.sqrt(d2) / self.connection_radius
                kinetic = float(np.clip((a.speed + b.speed) / 16.0, 0.0, 1.0))
                if self.mode == "constellation" and closeness < 0.42:
                    continue
                alpha = closeness * (0.20 + 0.80 * kinetic)
                if alpha < 0.10:
                    continue
                ca = np.asarray(self._color(a.id, kinetic), dtype=np.float32)
                cb = np.asarray(self._color(b.id, kinetic), dtype=np.float32)
                c = tuple(np.clip((ca + cb) * 0.5 * alpha, 0, 255).astype(np.uint8))
                cv2.line(layer, a.xy(), b.xy(), c, 1, cv2.LINE_AA)

    def _emit_sparks(self, layer: np.ndarray, p: TrackedPoint) -> None:
        if p.speed < 3.5:
            return
        energy = float(np.clip((p.speed - 3.5) / 14.0, 0.0, 1.0))
        n = 1 + int(energy * (8 if self.mode == "afterburner" else 5))
        rng = np.random.default_rng(p.id * 100_003 + self.frame_index)
        base_angle = math.atan2(p.vy, p.vx) + math.pi
        color = self._color(p.id, energy)
        for _ in range(n):
            ang = base_angle + float(rng.normal(0.0, 0.55))
            length = float(rng.uniform(5.0, 18.0 + energy * 28.0))
            x2 = int(round(p.x + math.cos(ang) * length))
            y2 = int(round(p.y + math.sin(ang) * length))
            c = tuple(int(v * float(rng.uniform(0.45, 1.0))) for v in color)
            cv2.line(layer, p.xy(), (x2, y2), c, 1, cv2.LINE_AA)

    def _update_shockwaves(self, layer: np.ndarray, points: list[TrackedPoint]) -> None:
        if points:
            speeds = np.asarray([p.speed for p in points], dtype=np.float32)
            fast = [p for p in points if p.speed > max(7.0, float(np.percentile(speeds, 90)))]
            if fast and self.frame_index % 5 == 0:
                p = max(fast, key=lambda q: q.speed)
                prev = self.previous_speed.get(p.id, p.speed)
                acceleration = p.speed - prev
                if acceleration > 2.0:
                    self.shockwaves.append(
                        Shockwave(p.x, p.y, 4.0, 5.0 + min(p.speed, 20.0) * 0.3, 1.0, p.id)
                    )

        survivors: list[Shockwave] = []
        for wave in self.shockwaves:
            energy = float(np.clip(wave.life, 0.0, 1.0))
            color = self._color(wave.color_index, energy)
            radius = max(2, int(wave.radius))
            cv2.circle(layer, (int(wave.x), int(wave.y)), radius, color, max(1, int(1 + energy * 2)), cv2.LINE_AA)
            wave.radius += wave.velocity
            wave.velocity *= 1.018
            wave.life *= 0.88
            if wave.life > 0.06 and wave.radius < max(self.width, self.height) * 0.8:
                survivors.append(wave)
        self.shockwaves = survivors[-24:]

    def render(
        self,
        points: list[TrackedPoint],
        *,
        mask: np.ndarray | None = None,
        intensity: float = 1.0,
    ) -> np.ndarray:
        self.frame_index += 1
        intensity = float(np.clip(intensity, 0.0, 2.5))
        layer = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        live_ids = {p.id for p in points}
        for stale in list(self.histories):
            if stale in live_ids:
                continue
            hist = self.histories[stale]
            if hist:
                hist.popleft()
            if len(hist) < 2:
                self.histories.pop(stale, None)
                self.previous_speed.pop(stale, None)

        self._draw_connections(layer, points)
        for p in points:
            self._draw_track(layer, p)
            speed_energy = float(np.clip(p.speed / 12.0, 0.0, 1.0))
            color = self._color(p.id, speed_energy)
            radius = max(1, int(self.point_radius * (1.0 + speed_energy * 1.5)))
            cv2.circle(layer, p.xy(), radius + 4, tuple(int(v * 0.18) for v in color), -1, cv2.LINE_AA)
            cv2.circle(layer, p.xy(), radius, color, -1, cv2.LINE_AA)
            self._emit_sparks(layer, p)

        # Detect acceleration BEFORE updating the per-track speed history.
        self._update_shockwaves(layer, points)
        for p in points:
            self.previous_speed[p.id] = p.speed

        if mask is not None and self.mode in {"plasma_mesh", "liquid_wire"}:
            m = (np.asarray(mask) > 0).astype(np.uint8) * 255
            edge = cv2.Canny(m, 50, 140)
            edge = cv2.GaussianBlur(edge, (0, 0), 2.3).astype(np.float32) / 255.0
            c = np.asarray(self.palette[0], dtype=np.float32)
            for ch in range(3):
                layer[..., ch] = np.clip(layer[..., ch].astype(np.float32) + edge * c[ch] * 0.30, 0, 255).astype(np.uint8)

        glow_small = cv2.GaussianBlur(layer, (0, 0), 2.2 + self.bloom * 1.4)
        glow_large = cv2.GaussianBlur(layer, (0, 0), 9.0 + self.bloom * 3.0)
        composite = np.clip(
            layer.astype(np.float32) * (0.82 + 0.18 * intensity)
            + glow_small.astype(np.float32) * (0.72 * self.bloom)
            + glow_large.astype(np.float32) * (0.28 * self.bloom),
            0,
            255,
        )

        self.feedback *= self.feedback_decay
        if self.mode == "afterburner":
            self.feedback *= 0.975
        self.feedback = np.maximum(self.feedback, composite)
        self.feedback = np.clip(self.feedback, 0, 255)
        return self.feedback.astype(np.uint8)

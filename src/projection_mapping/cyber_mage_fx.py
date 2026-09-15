from __future__ import annotations

from collections import deque
import math

import cv2
import numpy as np

from .performer_rig import PerformerState
from .spell_state import SpellState


PALETTES: dict[str, tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]] = {
    "arcane": ((45, 220, 255), (245, 60, 255), (180, 255, 255)),
    "solar": ((0, 150, 255), (0, 40, 255), (180, 245, 255)),
    "void": ((255, 80, 190), (150, 20, 255), (255, 210, 245)),
    "jade": ((80, 255, 170), (255, 180, 40), (220, 255, 245)),
}


class CyberMageRenderer:
    """Deterministic body-anchored spell renderer.

    Effects are attached to semantic anchors from PerformerRig. Neural generation can be
    composited later as a lower-rate style skin without owning spatial consistency.
    """

    def __init__(
        self,
        width: int,
        height: int,
        palette: str = "arcane",
        complexity: float = 0.75,
        trail_length: int = 28,
        feedback: float = 0.90,
    ) -> None:
        self.width = int(width)
        self.height = int(height)
        self.palette_name = palette if palette in PALETTES else "arcane"
        self.complexity = float(np.clip(complexity, 0.0, 1.0))
        self.feedback_decay = float(np.clip(feedback, 0.0, 0.985))
        self.feedback = np.zeros((self.height, self.width, 3), dtype=np.float32)
        self.left_trail: deque[tuple[int, int]] = deque(maxlen=max(2, int(trail_length)))
        self.right_trail: deque[tuple[int, int]] = deque(maxlen=max(2, int(trail_length)))
        self._burst = 0.0
        self._release_radius = 0.0

    @property
    def palette(self):
        return PALETTES[self.palette_name]

    @staticmethod
    def _add_glow(layer: np.ndarray, glow_sigma: float = 5.0, strength: float = 0.75) -> np.ndarray:
        glow = cv2.GaussianBlur(layer, (0, 0), glow_sigma)
        return np.clip(layer.astype(np.float32) + glow.astype(np.float32) * strength, 0, 255).astype(np.uint8)

    def _sigil(self, layer: np.ndarray, center: tuple[int, int], radius: int, t: float, color: tuple[int, int, int]) -> None:
        x, y = center
        radius = max(radius, 6)
        cv2.circle(layer, center, radius, color, 1, cv2.LINE_AA)
        cv2.circle(layer, center, int(radius * 0.72), color, 1, cv2.LINE_AA)
        spokes = 8 + int(self.complexity * 10)
        phase = t * 0.9
        for i in range(spokes):
            a = phase + i * math.tau / spokes
            a2 = a + (0.12 if i % 2 else -0.12)
            p1 = (int(x + math.cos(a) * radius * 0.70), int(y + math.sin(a) * radius * 0.70))
            p2 = (int(x + math.cos(a2) * radius), int(y + math.sin(a2) * radius))
            cv2.line(layer, p1, p2, color, 1, cv2.LINE_AA)
        tri_phase = -t * 0.55
        tri = []
        for i in range(3):
            a = tri_phase + i * math.tau / 3.0
            tri.append((int(x + math.cos(a) * radius * 0.52), int(y + math.sin(a) * radius * 0.52)))
        cv2.polylines(layer, [np.asarray(tri, np.int32)], True, color, 1, cv2.LINE_AA)

    def _arc(self, layer: np.ndarray, a: tuple[int, int], b: tuple[int, int], t: float, color: tuple[int, int, int], energy: float) -> None:
        if energy <= 0.02:
            return
        ax, ay = a
        bx, by = b
        steps = 18
        dx, dy = bx - ax, by - ay
        length = math.hypot(dx, dy) + 1e-6
        nx, ny = -dy / length, dx / length
        pts = []
        amp = (4.0 + 15.0 * energy) * (0.6 + self.complexity)
        for i in range(steps + 1):
            u = i / steps
            envelope = math.sin(math.pi * u)
            wobble = math.sin(i * 2.73 + t * 17.0) + 0.45 * math.sin(i * 5.11 - t * 10.0)
            off = wobble * amp * envelope
            pts.append((int(ax + dx * u + nx * off), int(ay + dy * u + ny * off)))
        cv2.polylines(layer, [np.asarray(pts, np.int32)], False, color, max(1, int(1 + energy * 3)), cv2.LINE_AA)

    def _trail(self, layer: np.ndarray, points: deque[tuple[int, int]], color: tuple[int, int, int]) -> None:
        if len(points) < 2:
            return
        pts = list(points)
        n = len(pts)
        for i in range(1, n):
            alpha = i / n
            c = tuple(int(v * alpha) for v in color)
            cv2.line(layer, pts[i - 1], pts[i], c, max(1, int(1 + alpha * 4)), cv2.LINE_AA)

    def render(
        self,
        mask: np.ndarray,
        state: PerformerState,
        t: float,
        intensity: float = 1.0,
        spell: SpellState | None = None,
    ) -> np.ndarray:
        intensity = float(np.clip(intensity, 0.0, 2.0))
        layer = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        c1, c2, c3 = self.palette
        spell = spell or SpellState()

        if not state.visible:
            self.feedback *= self.feedback_decay
            return np.clip(self.feedback, 0, 255).astype(np.uint8)

        a = state.anchors
        lh = a["left_hand"].xy()
        rh = a["right_hand"].xy()
        chest = a["chest"].xy()
        core = a["core"].xy()
        head = a["head"].xy()
        lf = a["left_foot"].xy()
        rf = a["right_foot"].xy()
        self.left_trail.append(lh)
        self.right_trail.append(rh)

        g = state.gestures
        motion = g.motion_energy
        self._burst = max(self._burst * 0.88, 1.0 if g.motion_burst else 0.0)

        body = (np.asarray(mask) > 0).astype(np.uint8) * 255
        edge = cv2.Canny(body, 50, 130)
        aura = cv2.GaussianBlur(body, (0, 0), 9.0).astype(np.float32) / 255.0
        edge_glow = cv2.GaussianBlur(edge, (0, 0), 3.0).astype(np.float32) / 255.0
        aura_gain = 0.18 + spell.shield_energy * 0.20 + spell.ascension_energy * 0.12
        layer[..., 0] = np.clip(aura * c1[0] * aura_gain + edge_glow * c1[0], 0, 255).astype(np.uint8)
        layer[..., 1] = np.clip(aura * c1[1] * aura_gain + edge_glow * c1[1], 0, 255).astype(np.uint8)
        layer[..., 2] = np.clip(aura * c1[2] * aura_gain + edge_glow * c1[2], 0, 255).astype(np.uint8)

        if state.bbox is not None:
            _x, _y, bw, bh = state.bbox
        else:
            bw, bh = self.width // 3, self.height // 2
        hand_r = int(max(12, min(bw, bh) * (0.10 + 0.04 * intensity + 0.04 * spell.charge)))
        chest_r = int(max(18, min(bw, bh) * (0.16 + 0.05 * self._burst)))

        self._sigil(layer, lh, hand_r, t, c1)
        self._sigil(layer, rh, hand_r, -t * 1.07, c2)
        self._sigil(layer, chest, chest_r, t * 0.45, c3)
        if spell.ascension_energy > 0.08:
            halo_center = (head[0], max(12, head[1] - int(bh * 0.16)))
            self._sigil(layer, halo_center, int(chest_r * (1.0 + 0.5 * spell.ascension_energy)), -t * 0.35, c1)

        self._trail(layer, self.left_trail, c1)
        self._trail(layer, self.right_trail, c2)

        arc_energy = np.clip(0.20 + motion * 1.6 + spell.charge * 0.8, 0.0, 1.0)
        self._arc(layer, lh, rh, t, c3, float(arc_energy))
        self._arc(layer, lh, core, t + 0.4, c1, float(np.clip(motion * 1.1 + spell.cast_energy, 0, 1)))
        self._arc(layer, rh, core, t - 0.3, c2, float(np.clip(motion * 1.1 + spell.cast_energy, 0, 1)))

        if spell.shield_energy > 0.05:
            shield_r = int(chest_r * (1.5 + 0.8 * spell.shield_energy))
            cv2.circle(layer, chest, shield_r, c3, max(1, int(1 + spell.shield_energy * 3)), cv2.LINE_AA)
            cv2.circle(layer, chest, int(shield_r * 0.82), c1, 1, cv2.LINE_AA)

        if spell.charge > 0.02:
            mx, my = int((lh[0] + rh[0]) * 0.5), int((lh[1] + rh[1]) * 0.5)
            orb_r = int(hand_r * (0.35 + spell.charge * 0.80 + 0.08 * math.sin(t * 10.0)))
            cv2.circle(layer, (mx, my), max(3, orb_r), c3, -1, cv2.LINE_AA)
            cv2.circle(layer, (mx, my), max(5, int(orb_r * 1.8)), c2, 1, cv2.LINE_AA)

        # A charged release becomes a spatial event instead of simply turning the orb off.
        if spell.release_energy > 0.02:
            self._release_radius += 9.0 + spell.release_energy * 14.0
            max_r = max(self.width, self.height) * 0.72
            if self._release_radius > max_r:
                self._release_radius = 0.0
            cv2.circle(layer, chest, max(1, int(self._release_radius)), c3, max(1, int(1 + spell.release_energy * 5)), cv2.LINE_AA)
        else:
            self._release_radius *= 0.90

        if spell.cast_energy > 0.05:
            for p, color in ((lh, c1), (rh, c2)):
                r = int(hand_r * (1.2 + spell.cast_energy * 2.0))
                cv2.circle(layer, p, r, color, max(1, int(1 + spell.cast_energy * 3)), cv2.LINE_AA)

        ground_y = max(lf[1], rf[1])
        ground_x = int((lf[0] + rf[0]) * 0.5)
        ground_r = int(max(20, abs(rf[0] - lf[0]) * (0.72 + 0.20 * spell.shield_energy)))
        cv2.ellipse(layer, (ground_x, ground_y), (ground_r, max(8, int(ground_r * 0.25))), 0, 0, 360, c1, 1, cv2.LINE_AA)

        layer = self._add_glow(layer, 5.0 + 3.0 * self.complexity, 0.55 + 0.35 * intensity)
        self.feedback *= self.feedback_decay
        self.feedback = np.maximum(self.feedback, layer.astype(np.float32))
        return np.clip(self.feedback, 0, 255).astype(np.uint8)

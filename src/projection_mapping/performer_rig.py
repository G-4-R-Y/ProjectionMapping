from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Mapping

import cv2
import numpy as np


@dataclass(frozen=True)
class Anchor:
    x: float
    y: float
    confidence: float = 1.0

    def xy(self) -> tuple[int, int]:
        return int(round(self.x)), int(round(self.y))


@dataclass(frozen=True)
class GestureState:
    arms_spread: bool = False
    hands_together: bool = False
    hands_raised: bool = False
    motion_burst: bool = False
    motion_energy: float = 0.0


@dataclass(frozen=True)
class PerformerState:
    visible: bool
    anchors: Mapping[str, Anchor] = field(default_factory=dict)
    gestures: GestureState = GestureState()
    bbox: tuple[int, int, int, int] | None = None
    occupancy: float = 0.0


class PerformerRig:
    """Low-dependency persistent body rig derived from a foreground mask.

    This is deliberately a classical baseline. It gives effects stable semantic ownership
    (head/chest/hands/feet) without requiring a pose model. A MediaPipe/learned landmark
    backend can later replace the anchor estimator while preserving this interface.
    """

    def __init__(self, smoothing: float = 0.72, min_area_fraction: float = 0.015) -> None:
        self.smoothing = float(np.clip(smoothing, 0.0, 0.98))
        self.min_area_fraction = float(max(min_area_fraction, 0.0))
        self._anchors: dict[str, Anchor] = {}
        self._motion_ema = 0.0

    def _smooth(self, name: str, x: float, y: float, confidence: float = 1.0) -> Anchor:
        previous = self._anchors.get(name)
        if previous is None:
            anchor = Anchor(float(x), float(y), float(confidence))
        else:
            a = self.smoothing
            anchor = Anchor(
                x=previous.x * a + float(x) * (1.0 - a),
                y=previous.y * a + float(y) * (1.0 - a),
                confidence=previous.confidence * a + float(confidence) * (1.0 - a),
            )
        self._anchors[name] = anchor
        return anchor

    @staticmethod
    def _extreme(points: np.ndarray, axis: int, mode: str) -> tuple[float, float]:
        values = points[:, axis]
        idx = int(np.argmin(values) if mode == "min" else np.argmax(values))
        return float(points[idx, 0]), float(points[idx, 1])

    def update(self, mask: np.ndarray, flow_mag: np.ndarray | None = None) -> PerformerState:
        binary = (np.asarray(mask) > 0).astype(np.uint8) * 255
        h, w = binary.shape[:2]
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            self._motion_ema *= 0.85
            return PerformerState(visible=False, gestures=GestureState(motion_energy=self._motion_ema))

        contour = max(contours, key=cv2.contourArea)
        area = float(cv2.contourArea(contour))
        if area < h * w * self.min_area_fraction:
            self._motion_ema *= 0.85
            return PerformerState(visible=False, gestures=GestureState(motion_energy=self._motion_ema))

        x0, y0, bw, bh = cv2.boundingRect(contour)
        cx = x0 + bw * 0.5
        points = contour.reshape(-1, 2).astype(np.float32)
        upper = points[points[:, 1] < y0 + bh * 0.68]
        lower = points[points[:, 1] > y0 + bh * 0.55]
        if len(upper) < 2:
            upper = points
        if len(lower) < 2:
            lower = points

        left_hand = self._extreme(upper, 0, "min")
        right_hand = self._extreme(upper, 0, "max")
        left_foot = self._extreme(lower, 0, "min")
        right_foot = self._extreme(lower, 0, "max")

        anchors = {
            "head": self._smooth("head", cx, y0 + bh * 0.10),
            "chest": self._smooth("chest", cx, y0 + bh * 0.36),
            "core": self._smooth("core", cx, y0 + bh * 0.52),
            "left_hand": self._smooth("left_hand", *left_hand),
            "right_hand": self._smooth("right_hand", *right_hand),
            "left_foot": self._smooth("left_foot", *left_foot),
            "right_foot": self._smooth("right_foot", *right_foot),
        }

        if flow_mag is None:
            motion = 0.0
        else:
            inside = np.asarray(flow_mag, dtype=np.float32)[binary > 0]
            motion = float(np.mean(np.clip(inside / 8.0, 0.0, 1.0))) if inside.size else 0.0
        self._motion_ema = self._motion_ema * 0.80 + motion * 0.20

        lh = anchors["left_hand"]
        rh = anchors["right_hand"]
        head = anchors["head"]
        hand_distance = math.hypot(lh.x - rh.x, lh.y - rh.y) / max(float(bw), 1.0)
        arms_spread = hand_distance > 0.78
        hands_together = hand_distance < 0.24
        raised_line = head.y + bh * 0.22
        hands_raised = lh.y < raised_line and rh.y < raised_line
        motion_burst = self._motion_ema > 0.22

        gestures = GestureState(
            arms_spread=arms_spread,
            hands_together=hands_together,
            hands_raised=hands_raised,
            motion_burst=motion_burst,
            motion_energy=float(np.clip(self._motion_ema, 0.0, 1.0)),
        )
        return PerformerState(
            visible=True,
            anchors=anchors,
            gestures=gestures,
            bbox=(x0, y0, bw, bh),
            occupancy=area / max(float(h * w), 1.0),
        )

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class TemporalStats:
    warp_residual: float = 0.0
    blend_residual: float = 0.0


class FlowTemporalStabilizer:
    """Display-side temporal stabilizer for sparse neural keyframes.

    Each camera-frame optical flow increment warps the currently displayed neural frame
    forward. When a fresh neural keyframe arrives it is blended against that warped
    prediction to reduce one-frame appearance jumps. This does not make the diffusion
    model itself recurrent; it is the deterministic baseline that later temporal/video
    models must beat.
    """

    def __init__(self, width: int, height: int, keyframe_blend: float = 0.78) -> None:
        self.width = int(width)
        self.height = int(height)
        self.keyframe_blend = float(np.clip(keyframe_blend, 0.0, 1.0))
        y, x = np.mgrid[0:self.height, 0:self.width].astype(np.float32)
        self._grid_x = x
        self._grid_y = y
        self._frame: np.ndarray | None = None
        self.stats = TemporalStats()

    @property
    def frame(self) -> np.ndarray | None:
        return self._frame

    def reset(self, frame_rgb: np.ndarray | None = None) -> None:
        self._frame = None if frame_rgb is None else np.asarray(frame_rgb, dtype=np.uint8).copy()
        self.stats = TemporalStats()

    def warp(self, flow: np.ndarray) -> np.ndarray | None:
        if self._frame is None:
            return None
        flow = np.asarray(flow, dtype=np.float32)
        if flow.shape[:2] != (self.height, self.width) or flow.ndim != 3 or flow.shape[2] != 2:
            raise ValueError("flow must be HxWx2 and match stabilizer resolution")

        # Farneback(prev, curr) stores displacement from previous pixel positions to
        # current positions. For inverse remap of the destination frame, sample the
        # previous image approximately at destination - flow.
        map_x = self._grid_x - flow[..., 0]
        map_y = self._grid_y - flow[..., 1]
        previous = self._frame
        warped = cv2.remap(
            previous,
            map_x,
            map_y,
            interpolation=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT101,
        )
        self.stats.warp_residual = float(np.mean(np.abs(warped.astype(np.float32) - previous.astype(np.float32)))) / 255.0
        self._frame = warped
        return warped

    def ingest_keyframe(self, generated_rgb: np.ndarray) -> np.ndarray:
        generated = np.asarray(generated_rgb, dtype=np.uint8)
        if generated.shape[:2] != (self.height, self.width):
            generated = cv2.resize(generated, (self.width, self.height), interpolation=cv2.INTER_CUBIC)
        if self._frame is None:
            self._frame = generated.copy()
            self.stats.blend_residual = 0.0
            return self._frame

        old = self._frame
        self.stats.blend_residual = float(np.mean(np.abs(generated.astype(np.float32) - old.astype(np.float32)))) / 255.0
        alpha = self.keyframe_blend
        self._frame = cv2.addWeighted(generated, alpha, old, 1.0 - alpha, 0.0)
        return self._frame

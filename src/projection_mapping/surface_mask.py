from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SurfaceMaskSpec:
    """Projector-output-space polygon and edge-feather mask."""

    polygon: tuple[tuple[float, float], ...] | None = None
    polygon_feather_px: float = 0.0
    edge_feather_px: float = 0.0


def _smoothstep01(value: np.ndarray) -> np.ndarray:
    x = np.clip(np.asarray(value, dtype=np.float32), 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def _validate_polygon(polygon: tuple[tuple[float, float], ...]) -> np.ndarray:
    points = np.asarray(polygon, dtype=np.float32)
    if points.ndim != 2 or points.shape[1:] != (2,) or len(points) < 3:
        raise ValueError("surface-mask polygon must contain at least three (x, y) points")
    if not np.isfinite(points).all():
        raise ValueError("surface-mask polygon coordinates must be finite")
    next_points = np.roll(points, -1, axis=0)
    twice_area = np.sum(
        points[:, 0] * next_points[:, 1] - points[:, 1] * next_points[:, 0]
    )
    if abs(float(twice_area)) <= 1e-8:
        raise ValueError("surface-mask polygon must enclose a non-zero area")
    return points


def _polygon_alpha(
    width: int,
    height: int,
    polygon: tuple[tuple[float, float], ...],
    feather_px: float,
) -> np.ndarray:
    points = _validate_polygon(polygon)
    x_norm = (np.arange(width, dtype=np.float32) + 0.5) / float(width)
    y_norm = (np.arange(height, dtype=np.float32) + 0.5) / float(height)
    x, y = np.meshgrid(x_norm, y_norm)

    inside = np.zeros((height, width), dtype=bool)
    epsilon = np.float32(1e-12)
    for index, point_a in enumerate(points):
        point_b = points[(index + 1) % len(points)]
        x0, y0 = point_a
        x1, y1 = point_b
        crosses_scanline = (y0 > y) != (y1 > y)
        x_at_scanline = (x1 - x0) * (y - y0) / (y1 - y0 + epsilon) + x0
        inside ^= crosses_scanline & (x < x_at_scanline)

    if feather_px <= 0.0:
        return inside.astype(np.float32)

    x_px = np.arange(width, dtype=np.float32) + 0.5
    y_px = np.arange(height, dtype=np.float32) + 0.5
    xx, yy = np.meshgrid(x_px, y_px)
    points_px = points * np.asarray([width, height], dtype=np.float32)
    distance_sq = np.full((height, width), np.inf, dtype=np.float32)

    for index, point_a in enumerate(points_px):
        point_b = points_px[(index + 1) % len(points_px)]
        vx, vy = point_b - point_a
        segment_sq = float(vx * vx + vy * vy)
        if segment_sq <= 1e-12:
            continue
        along = np.clip(
            ((xx - point_a[0]) * vx + (yy - point_a[1]) * vy) / segment_sq,
            0.0,
            1.0,
        )
        dx = xx - (point_a[0] + along * vx)
        dy = yy - (point_a[1] + along * vy)
        distance_sq = np.minimum(distance_sq, dx * dx + dy * dy)

    distance = np.sqrt(distance_sq)
    feather = _smoothstep01(distance / max(float(feather_px), 1e-6))
    return inside.astype(np.float32) * feather


def build_surface_alpha(width: int, height: int, spec: SurfaceMaskSpec) -> np.ndarray:
    """Build reusable alpha in final projector/output coordinates."""

    width = int(width)
    height = int(height)
    if width <= 0 or height <= 0:
        raise ValueError("surface-mask dimensions must be positive")
    if spec.edge_feather_px < 0.0 or spec.polygon_feather_px < 0.0:
        raise ValueError("surface-mask feather widths cannot be negative")

    alpha = np.ones((height, width), dtype=np.float32)
    if spec.edge_feather_px > 0.0:
        x = np.arange(width, dtype=np.float32)
        y = np.arange(height, dtype=np.float32)
        xx, yy = np.meshgrid(x, y)
        distance_to_frame_edge = np.minimum.reduce(
            (xx, (width - 1) - xx, yy, (height - 1) - yy)
        )
        alpha *= _smoothstep01(
            distance_to_frame_edge / float(spec.edge_feather_px)
        )

    if spec.polygon is not None:
        alpha *= _polygon_alpha(
            width,
            height,
            spec.polygon,
            float(spec.polygon_feather_px),
        )

    return np.clip(alpha, 0.0, 1.0).astype(np.float32, copy=False)


def apply_surface_alpha(
    frame: np.ndarray,
    alpha: np.ndarray,
    *,
    background: np.ndarray | None = None,
) -> np.ndarray:
    """Composite through output-space alpha, optionally over a background."""

    frame_array = np.asarray(frame)
    alpha_array = np.asarray(alpha, dtype=np.float32)
    if frame_array.ndim not in (2, 3):
        raise ValueError("surface-mask frames must be HxW or HxWxC arrays")
    if alpha_array.shape != frame_array.shape[:2]:
        raise ValueError("surface-mask alpha dimensions must match the frame")
    if not np.isfinite(alpha_array).all():
        raise ValueError("surface-mask alpha must contain only finite values")

    mask = np.clip(alpha_array, 0.0, 1.0)
    if frame_array.ndim == 3:
        mask = mask[..., None]

    foreground = frame_array.astype(np.float32)
    if background is None:
        composed = foreground * mask
    else:
        background_array = np.asarray(background)
        if background_array.shape != frame_array.shape:
            raise ValueError("surface-mask background must match the frame shape")
        composed = (
            foreground * mask
            + background_array.astype(np.float32) * (1.0 - mask)
        )

    if np.issubdtype(frame_array.dtype, np.integer):
        limits = np.iinfo(frame_array.dtype)
        composed = np.clip(np.rint(composed), limits.min, limits.max)
    return composed.astype(frame_array.dtype, copy=False)


class SurfaceMaskProcessor:
    """Runtime processor with a precomputed output-space alpha mask."""

    def __init__(self, width: int, height: int, spec: SurfaceMaskSpec) -> None:
        self.alpha = build_surface_alpha(width, height, spec)

    def __call__(self, frame: np.ndarray) -> np.ndarray:
        return apply_surface_alpha(frame, self.alpha)

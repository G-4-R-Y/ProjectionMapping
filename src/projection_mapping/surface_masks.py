"""Experimental projector-space polygon mattes for static Room Skin output.

Normalized (0..1) outlines use even-odd fill: nested outlines create holes.
This is a *manual* output-space clipping mask, not projector-camera calibration.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np


MAX_JSON_BYTES = 128 * 1024
MAX_OUTLINES = 16
MAX_VERTICES = 512


def load_surface_mask(
    path: str | Path, width: int, height: int, *, feather_px: float = 0.0
) -> np.ndarray:
    """Load a manually traced surface and rasterize an inner-feathered (H,W) alpha mask.

    JSON: {"space": "normalized", "outlines": [[[x, y], ...], ...]}.
    Coordinates are relative to *projector output*, not camera input. The
    optional feather stays inside the polygon to prevent light bleed.
    """
    if not (isinstance(width, int) and isinstance(height, int) and 1 < width <= 8192 and 1 < height <= 8192):
        raise ValueError("Invalid projector dimensions")
    if not (isinstance(feather_px, (int, float)) and math.isfinite(feather_px) and 0 <= feather_px <= 256):
        raise ValueError("feather_px must be between 0 and 256")
    p = Path(path)
    if p.stat().st_size > MAX_JSON_BYTES:
        raise ValueError("Surface JSON exceeds 128 KiB")
    spec = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(spec, dict) or spec.get("space") != "normalized":
        raise ValueError("Surface JSON requires space='normalized'")
    paths = spec.get("outlines")
    if not isinstance(paths, list) or not (1 <= len(paths) <= MAX_OUTLINES):
        raise ValueError("Surface requires 1-16 polygon outlines")

    # OpenCV is already a Room Skin/vision dependency. Allocate once at startup.
    import cv2

    binary = np.zeros((height, width), np.uint8)
    layer = np.zeros_like(binary)
    for outline in paths:
        if not isinstance(outline, list) or not (3 <= len(outline) <= MAX_VERTICES):
            raise ValueError("Outlines need 3-512 vertices")
        for point in outline:
            if (not isinstance(point, list) or len(point) != 2
                    or any(isinstance(v, bool) or not isinstance(v, (int, float))
                           or not math.isfinite(v) or not 0 <= v <= 1 for v in point)):
                raise ValueError("Vertices must be normalized finite [x, y] pairs")
        vertices = np.asarray(outline, dtype=np.float64)
        shoelace = np.dot(vertices[:, 0], np.roll(vertices[:, 1], 1)) - np.dot(vertices[:, 1], np.roll(vertices[:, 0], 1))
        if abs(shoelace) < 1e-8:
            raise ValueError("Degenerate polygon outline")
        vertices[:, 0] *= width - 1
        vertices[:, 1] *= height - 1
        pixels = np.rint(vertices).astype(np.int32)
        layer.fill(0)
        cv2.fillPoly(layer, [pixels], 255)
        cv2.bitwise_xor(binary, layer, dst=binary)

    if feather_px == 0:
        return binary.astype(np.float32) / 255.0
    # distanceTransform returns 0 outside; taper *inward*, never emit outside.
    distance = cv2.distanceTransform(binary, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
    ramp = np.clip(distance / float(feather_px), 0.0, 1.0)
    return (ramp * ramp * (3.0 - 2.0 * ramp)).astype(np.float32)


def apply_surface_mask(frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Composite a static matte over an 8-bit mono or RGB projector frame."""
    if frame.dtype != np.uint8 or frame.ndim not in (2, 3) or (frame.ndim == 3 and frame.shape[2] != 3):
        raise ValueError("Expected a uint8 HxW or HxWx3 frame")
    if mask.shape != frame.shape[:2] or mask.ndim != 2:
        raise ValueError("Mask must match the frame height and width")
    alpha = np.clip(mask, 0.0, 1.0)
    return np.clip(frame.astype(np.float32) * (alpha[..., None] if frame.ndim == 3 else alpha), 0, 255).astype(np.uint8)

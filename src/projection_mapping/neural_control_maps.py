from __future__ import annotations

import cv2
import numpy as np

from .performance_bus import PerformanceState


def performer_control_map(
    state: PerformanceState,
    width: int,
    height: int,
    *,
    anchor_radius: int = 12,
) -> np.ndarray:
    """Encode deterministic performer semantics into an RGB neural control image.

    Channels are deliberately interpretable rather than model-specific:
    R = semantic anchor / body energy
    G = velocity magnitude and direction trails
    B = high-level gesture / room-event energy

    StreamDiffusion, ControlNet adapters, a custom CNN, or a later video model can consume or
    remap this image while exact realtime particles remain composited deterministically.
    """
    w = int(width)
    h = int(height)
    out = np.zeros((h, w, 3), dtype=np.float32)
    tracking = state.tracking

    for anchor in tracking.anchors:
        if anchor.confidence <= 0.0:
            continue
        x = int(np.clip(anchor.position.x * (w - 1), 0, w - 1))
        y = int(np.clip(anchor.position.y * (h - 1), 0, h - 1))
        speed = min(anchor.speed / 1.5, 1.0)
        radius = max(3, int(anchor_radius * (0.65 + 0.65 * anchor.confidence)))
        cv2.circle(out[..., 0], (x, y), radius, float(anchor.confidence), -1, cv2.LINE_AA)
        if speed > 0.01:
            x2 = int(np.clip(x - anchor.velocity.x * w * 0.08, 0, w - 1))
            y2 = int(np.clip(y - anchor.velocity.y * h * 0.08, 0, h - 1))
            cv2.line(out[..., 1], (x2, y2), (x, y), float(speed), max(1, radius // 3), cv2.LINE_AA)

    for point in tracking.motion_points:
        x = int(np.clip(point.position.x * (w - 1), 0, w - 1))
        y = int(np.clip(point.position.y * (h - 1), 0, h - 1))
        speed = min(point.speed / 1.5, 1.0)
        cv2.circle(out[..., 1], (x, y), 2, float(speed * point.confidence), -1, cv2.LINE_AA)

    for event in tracking.gestures:
        anchor = tracking.anchor(event.source_anchor or "", 0.0) if event.source_anchor else None
        if anchor is not None:
            x = int(np.clip(anchor.position.x * (w - 1), 0, w - 1))
            y = int(np.clip(anchor.position.y * (h - 1), 0, h - 1))
        else:
            x, y = w // 2, h // 2
        radius = int(18 + 70 * np.clip(event.strength, 0.0, 1.0))
        cv2.circle(out[..., 2], (x, y), radius, float(np.clip(event.strength, 0.0, 1.0)), -1, cv2.LINE_AA)

    for event in tracking.room_events:
        x = int(np.clip(event.uv[0] * (w - 1), 0, w - 1))
        y = int(np.clip(event.uv[1] * (h - 1), 0, h - 1))
        cv2.circle(out[..., 2], (x, y), 24, float(np.clip(event.strength, 0.0, 1.0)), -1, cv2.LINE_AA)

    # Give models smooth spatial evidence instead of one-pixel landmarks.
    out[..., 0] = cv2.GaussianBlur(out[..., 0], (0, 0), 3.0)
    out[..., 1] = cv2.GaussianBlur(out[..., 1], (0, 0), 2.0)
    out[..., 2] = cv2.GaussianBlur(out[..., 2], (0, 0), 4.5)
    return (np.clip(out, 0.0, 1.0) * 255.0).astype(np.uint8)


__all__ = ["performer_control_map"]

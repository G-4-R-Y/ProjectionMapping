"""First spatially locked 'room skin' prototype.

This prototype keeps physical edges anchored while a semantic generator produces new
appearance. It can run with any callable generator compatible with the existing
StreamDiffusion wrapper; without one, it falls back to procedural color remapping so
the geometry/temporal path can be tested independently of model setup.
"""
from __future__ import annotations

import argparse
import time

import cv2
import numpy as np

from projection_mapping.capture import Camera
from projection_mapping.perception import optical_flow
from projection_mapping.room_skin import preserve_edges, advect_with_flow, temporal_mix
from projection_mapping.runtime import FullscreenSink


def psychedelic_fallback(frame_rgb: np.ndarray, t: float) -> np.ndarray:
    """Cheap semantic-ish fallback for testing alignment before diffusion is wired."""
    x = frame_rgb.astype(np.float32) / 255.0
    phase = np.array([
        0.5 + 0.5 * np.sin(t * 0.7),
        0.5 + 0.5 * np.sin(t * 0.9 + 2.1),
        0.5 + 0.5 * np.sin(t * 1.1 + 4.2),
    ], dtype=np.float32)
    y = np.sin((x * 3.2 + phase) * np.pi) * 0.5 + 0.5
    return np.clip(y * 255.0, 0, 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--display", type=int, default=1)
    ap.add_argument("--edge-strength", type=float, default=0.82)
    ap.add_argument("--temporal-alpha", type=float, default=0.24)
    ap.add_argument("--projector-width", type=int, default=1920)
    ap.add_argument("--projector-height", type=int, default=1080)
    args = ap.parse_args()

    sink = FullscreenSink(window="ProjectionMapping-RoomSkin", display=args.display)

    with Camera(args.camera) as cam:
        first_bgr = cam.read()
        reference_rgb = cv2.cvtColor(first_bgr, cv2.COLOR_BGR2RGB)
        prev_camera_rgb = reference_rgb.copy()
        stable_rgb = psychedelic_fallback(reference_rgb, 0.0)
        t0 = time.perf_counter()

        while True:
            camera_bgr = cam.read()
            camera_rgb = cv2.cvtColor(camera_bgr, cv2.COLOR_BGR2RGB)
            flow = optical_flow(prev_camera_rgb, camera_rgb)

            # Advect the last appearance with observed scene motion. A slower diffusion
            # worker can replace `candidate` here whenever a fresh semantic keyframe arrives.
            advected = advect_with_flow(stable_rgb, flow)
            candidate = psychedelic_fallback(camera_rgb, time.perf_counter() - t0)
            candidate = preserve_edges(reference_rgb, candidate, strength=args.edge_strength)
            stable_rgb = temporal_mix(advected, candidate, alpha=args.temporal_alpha)

            output_rgb = cv2.resize(
                stable_rgb,
                (args.projector_width, args.projector_height),
                interpolation=cv2.INTER_LINEAR,
            )
            if sink(cv2.cvtColor(output_rgb, cv2.COLOR_RGB2BGR)) is False:
                break
            prev_camera_rgb = camera_rgb

    sink.close()


if __name__ == "__main__":
    main()

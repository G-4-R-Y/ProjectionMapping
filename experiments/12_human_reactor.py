"""Human Reactor: camera-driven silhouette/energy visual.

No pose model required: foreground segmentation + optical flow create a responsive reactor
where movement becomes energy, contour edges glow, and motion launches persistent trails.
F11 toggles fullscreen; ESC exits.
"""
from __future__ import annotations

import argparse
import time

import cv2
import numpy as np

from projection_mapping.capture import Camera
from projection_mapping.perception import BackgroundMask, optical_flow
from projection_mapping.runtime import FullscreenSink


def colorize(mask: np.ndarray, flow_mag: np.ndarray, t: float, intensity: float) -> np.ndarray:
    m = np.clip(mask.astype(np.float32) / 255.0, 0.0, 1.0)
    flow = np.clip(flow_mag / 8.0, 0.0, 1.0)

    edge = cv2.Canny((m * 255).astype(np.uint8), 40, 120).astype(np.float32) / 255.0
    edge = cv2.GaussianBlur(edge, (0, 0), 3.0)
    core = cv2.GaussianBlur(m, (0, 0), 15.0)
    motion = cv2.GaussianBlur(flow * m, (0, 0), 7.0)

    pulse = 0.6 + 0.4 * np.sin(t * 2.2 + motion * 8.0)
    energy = np.clip(core * (0.35 + intensity * 0.55) + edge * 1.4 + motion * (1.3 + intensity), 0.0, 1.6)

    r = np.clip(edge * 0.95 + motion * 1.2 + energy * 0.15, 0.0, 1.0)
    g = np.clip(core * 0.10 + edge * 0.25 + motion * 0.30, 0.0, 1.0)
    b = np.clip(core * 0.55 * pulse + edge * 0.95 + energy * 0.45, 0.0, 1.0)
    return np.dstack([r, g, b])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--display", type=int, default=1)
    ap.add_argument("--projector-width", type=int, default=1920)
    ap.add_argument("--projector-height", type=int, default=1080)
    ap.add_argument("--capture-width", type=int, default=640)
    ap.add_argument("--capture-height", type=int, default=360)
    ap.add_argument("--intensity", type=float, default=0.9)
    ap.add_argument("--feedback", type=float, default=0.90)
    args = ap.parse_args()

    sink = FullscreenSink(window="ProjectionMapping-HumanReactor", display=args.display)
    bg = BackgroundMask(history=220, threshold=20.0)
    previous = None
    feedback = np.zeros((args.capture_height, args.capture_width, 3), dtype=np.float32)
    t0 = time.perf_counter()
    report_t = t0
    frames = 0

    try:
        with Camera(args.camera, args.capture_width, args.capture_height) as cam:
            while True:
                now = time.perf_counter()
                frame = cam.read()
                frame = cv2.resize(frame, (args.capture_width, args.capture_height), interpolation=cv2.INTER_AREA)
                mask = bg(frame)
                mask = cv2.medianBlur(mask, 7)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))

                if previous is None:
                    flow_mag = np.zeros(mask.shape, dtype=np.float32)
                else:
                    flow = optical_flow(previous, frame)
                    flow_mag = np.sqrt(flow[..., 0] ** 2 + flow[..., 1] ** 2)
                previous = frame.copy()

                current = colorize(mask, flow_mag, now - t0, float(np.clip(args.intensity, 0.0, 2.0)))

                # Feedback only survives where recent energy existed; this creates comet-like
                # motion trails without allowing the entire frame to wash out.
                decay = float(np.clip(args.feedback, 0.0, 0.985))
                feedback *= decay
                feedback = np.maximum(feedback, current)
                feedback = cv2.GaussianBlur(feedback, (0, 0), 0.7)

                # Add sparse motion sparks at high-flow pixels.
                threshold = np.percentile(flow_mag, 96) if np.any(flow_mag) else 999.0
                sparks = ((flow_mag > max(threshold, 1.2)) & (mask > 0)).astype(np.float32)
                sparks = cv2.GaussianBlur(sparks, (0, 0), 2.0)
                feedback[..., 0] = np.clip(feedback[..., 0] + sparks * 0.8, 0.0, 1.0)
                feedback[..., 2] = np.clip(feedback[..., 2] + sparks * 0.45, 0.0, 1.0)

                rgb8 = (np.clip(feedback, 0.0, 1.0) * 255).astype(np.uint8)
                out = cv2.resize(rgb8, (args.projector_width, args.projector_height), interpolation=cv2.INTER_LINEAR)
                if sink(cv2.cvtColor(out, cv2.COLOR_RGB2BGR)) is False:
                    break

                frames += 1
                if now - report_t >= 2.0:
                    motion_mean = float(np.mean(flow_mag))
                    occupancy = float(np.mean(mask > 0))
                    print(
                        f"fps={frames / (now - report_t):.1f} foreground={occupancy:.3f} "
                        f"motion={motion_mean:.3f} F11=fullscreen ESC=exit",
                        flush=True,
                    )
                    frames = 0
                    report_t = now
    finally:
        sink.close()


if __name__ == "__main__":
    main()

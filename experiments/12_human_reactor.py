"""Human Reactor: camera-driven dance/performance renderer.

Foreground segmentation + optical flow turn a person into a controllable energy sculpture.
No pose model is required. F11 toggles fullscreen; ESC exits.
"""
from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path
import time

import cv2
import numpy as np

from projection_mapping.capture import Camera
from projection_mapping.perception import BackgroundMask, optical_flow
from projection_mapping.runtime import FullscreenSink


PALETTES = {
    "cyan_magenta": ((0.00, 0.96, 1.00), (1.00, 0.02, 0.78), (0.86, 0.96, 1.00)),
    "neon": ((0.96, 0.08, 0.62), (0.05, 0.80, 1.00), (0.75, 0.92, 1.00)),
    "jade": ((0.00, 0.95, 0.58), (0.02, 0.35, 0.25), (0.75, 1.00, 0.88)),
    "ember": ((1.00, 0.12, 0.02), (1.00, 0.55, 0.02), (1.00, 0.93, 0.65)),
    "ice": ((0.10, 0.45, 1.00), (0.05, 0.90, 1.00), (0.92, 0.98, 1.00)),
    "violet": ((0.65, 0.08, 1.00), (0.10, 0.42, 1.00), (1.00, 0.35, 0.90)),
    "mono": ((0.15, 0.18, 0.22), (0.65, 0.78, 0.88), (1.00, 1.00, 1.00)),
}


def _palette(name: str):
    return [np.asarray(c, dtype=np.float32) for c in PALETTES[name]]


def render_reactor(
    mask: np.ndarray,
    flow_mag: np.ndarray,
    t: float,
    *,
    style: str,
    palette: str,
    intensity: float,
    edge_gain: float,
    motion_gain: float,
    body_glow: float,
    spark_gain: float,
) -> np.ndarray:
    m = np.clip(mask.astype(np.float32) / 255.0, 0.0, 1.0)
    flow = np.clip(flow_mag / 8.0, 0.0, 1.0)
    edge = cv2.Canny((m * 255).astype(np.uint8), 35, 105).astype(np.float32) / 255.0
    edge = cv2.GaussianBlur(edge, (0, 0), 2.5)
    core = cv2.GaussianBlur(m, (0, 0), 13.0)
    motion = cv2.GaussianBlur(flow * m, (0, 0), 6.0)
    c0, c1, c2 = _palette(palette)

    pulse = 0.70 + 0.30 * np.sin(t * 2.0 + motion * 7.0)
    if style == "outline":
        e0, e1, e2 = edge * edge_gain, motion * motion_gain * 0.35, core * body_glow * 0.12
    elif style == "ghost":
        e0, e1, e2 = edge * edge_gain * 0.55, motion * motion_gain * 0.80, core * body_glow * pulse
    elif style == "ember":
        e0, e1, e2 = motion * motion_gain * 1.15, edge * edge_gain * 0.70, core * body_glow * 0.45
    elif style == "xray":
        skeletonish = cv2.Laplacian(core, cv2.CV_32F)
        skeletonish = np.abs(skeletonish)
        e0, e1, e2 = core * body_glow * 0.30, edge * edge_gain, skeletonish * 5.0 + motion * motion_gain
    else:  # plasma / default
        e0, e1, e2 = core * body_glow * 0.35, edge * edge_gain, motion * motion_gain * pulse

    rgb = e0[..., None] * c0 + e1[..., None] * c1 + e2[..., None] * c2

    if np.any(flow_mag):
        threshold = np.percentile(flow_mag[mask > 0], 95) if np.any(mask > 0) else 999.0
    else:
        threshold = 999.0
    sparks = ((flow_mag > max(threshold, 1.1)) & (mask > 0)).astype(np.float32)
    sparks = cv2.GaussianBlur(sparks, (0, 0), 1.7)
    rgb += sparks[..., None] * c2 * spark_gain
    return np.clip(rgb * intensity, 0.0, 1.5)


def add_echoes(canvas: np.ndarray, history: deque[np.ndarray], palette: str, strength: float) -> np.ndarray:
    if not history or strength <= 0:
        return canvas
    colors = _palette(palette)
    out = canvas.copy()
    n = len(history)
    for idx, old in enumerate(history):
        age = (idx + 1) / max(n, 1)
        alpha = strength * (1.0 - age) ** 1.6 * 0.42
        if alpha <= 0.002:
            continue
        glow = cv2.GaussianBlur(old.astype(np.float32) / 255.0, (0, 0), 4.0 + age * 9.0)
        color = colors[idx % len(colors)]
        out += glow[..., None] * color * alpha
    return np.clip(out, 0.0, 1.5)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--display", type=int, default=1)
    ap.add_argument("--projector-width", type=int, default=1920)
    ap.add_argument("--projector-height", type=int, default=1080)
    ap.add_argument("--capture-width", type=int, default=640)
    ap.add_argument("--capture-height", type=int, default=360)
    ap.add_argument("--style", choices=["plasma", "outline", "ghost", "ember", "xray"], default="plasma")
    ap.add_argument("--palette", choices=sorted(PALETTES), default="cyan_magenta")
    ap.add_argument("--intensity", type=float, default=0.9)
    ap.add_argument("--feedback", type=float, default=0.90)
    ap.add_argument("--edge-gain", type=float, default=1.35)
    ap.add_argument("--motion-gain", type=float, default=1.25)
    ap.add_argument("--body-glow", type=float, default=0.55)
    ap.add_argument("--spark-gain", type=float, default=0.85)
    ap.add_argument("--echoes", type=int, default=4)
    ap.add_argument("--echo-strength", type=float, default=0.70)
    ap.add_argument("--camera-mix", type=float, default=0.0, help="0=clean effect, 1=full camera beneath FX")
    ap.add_argument("--mirror", action="store_true")
    ap.add_argument("--record", default="", help="optional rendered-video output path (.mp4/.avi)")
    ap.add_argument("--record-fps", type=float, default=30.0)
    args = ap.parse_args()

    sink = FullscreenSink(window="ProjectionMapping-HumanReactor", display=args.display)
    bg = BackgroundMask(history=220, threshold=20.0)
    previous = None
    feedback = np.zeros((args.capture_height, args.capture_width, 3), dtype=np.float32)
    history: deque[np.ndarray] = deque(maxlen=max(0, args.echoes))
    t0 = time.perf_counter()
    report_t = t0
    frames = 0
    frame_index = 0
    writer = None

    if args.record:
        path = Path(args.record).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(path), fourcc, args.record_fps, (args.projector_width, args.projector_height))
        if not writer.isOpened():
            raise RuntimeError(f"could not open video writer: {path}")
        print(f"[human-reactor] recording={path}", flush=True)

    print(
        f"[human-reactor] style={args.style} palette={args.palette} feedback={args.feedback:.3f} "
        f"echoes={args.echoes} camera_mix={args.camera_mix:.2f}",
        flush=True,
    )

    try:
        with Camera(args.camera, args.capture_width, args.capture_height) as cam:
            while True:
                now = time.perf_counter()
                frame = cam.read()
                frame = cv2.resize(frame, (args.capture_width, args.capture_height), interpolation=cv2.INTER_AREA)
                if args.mirror:
                    frame = cv2.flip(frame, 1)
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

                current = render_reactor(
                    mask,
                    flow_mag,
                    now - t0,
                    style=args.style,
                    palette=args.palette,
                    intensity=float(np.clip(args.intensity, 0.0, 2.0)),
                    edge_gain=float(np.clip(args.edge_gain, 0.0, 4.0)),
                    motion_gain=float(np.clip(args.motion_gain, 0.0, 4.0)),
                    body_glow=float(np.clip(args.body_glow, 0.0, 3.0)),
                    spark_gain=float(np.clip(args.spark_gain, 0.0, 4.0)),
                )

                if args.echoes > 0 and frame_index % 3 == 0:
                    history.appendleft(mask.copy())
                current = add_echoes(current, history, args.palette, float(np.clip(args.echo_strength, 0.0, 2.0)))

                decay = float(np.clip(args.feedback, 0.0, 0.99))
                feedback *= decay
                feedback = np.maximum(feedback, current)
                feedback = cv2.GaussianBlur(feedback, (0, 0), 0.65)

                camera_mix = float(np.clip(args.camera_mix, 0.0, 1.0))
                if camera_mix > 0:
                    camera_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
                    # Darken camera to leave room for emissive FX.
                    feedback = np.clip(feedback + camera_rgb * camera_mix * 0.42, 0.0, 1.0)

                rgb8 = (np.clip(feedback, 0.0, 1.0) * 255).astype(np.uint8)
                out_rgb = cv2.resize(rgb8, (args.projector_width, args.projector_height), interpolation=cv2.INTER_CUBIC)
                out_bgr = cv2.cvtColor(out_rgb, cv2.COLOR_RGB2BGR)
                if writer is not None:
                    writer.write(out_bgr)
                if sink(out_bgr) is False:
                    break

                frame_index += 1
                frames += 1
                if now - report_t >= 2.0:
                    motion_mean = float(np.mean(flow_mag))
                    occupancy = float(np.mean(mask > 0))
                    print(
                        f"fps={frames / (now - report_t):.1f} foreground={occupancy:.3f} motion={motion_mean:.3f} "
                        f"style={args.style} palette={args.palette} F11=fullscreen ESC=exit",
                        flush=True,
                    )
                    frames = 0
                    report_t = now
    finally:
        if writer is not None:
            writer.release()
        sink.close()


if __name__ == "__main__":
    main()

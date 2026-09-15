"""Cyber Mage SFX v2: persistent point tracking + cinematic effects.

This deliberately does NOT pretend silhouette extrema are hands. Shi-Tomasi features are
tracked with forward/backward Lucas-Kanade validation, assigned persistent IDs, and used as
continuous SFX emitters. Motion drives trails, mesh links, sparks and shockwaves. An optional
ModernGL post shader adds chromatic bloom and coherent procedural atmosphere.

F11 toggles fullscreen; ESC exits.
"""
from __future__ import annotations

import argparse
import time

import cv2
import numpy as np

from projection_mapping.capture import Camera
from projection_mapping.perception import BackgroundMask
from projection_mapping.point_sfx import PALETTES, PointSFXRenderer
from projection_mapping.point_tracker import LKPointTracker
from projection_mapping.runtime import FullscreenSink


MODES = ("plasma_mesh", "constellation", "afterburner", "liquid_wire")
BACKGROUNDS = {"black": 0, "nebula": 1, "grid": 2, "liquid": 3}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--display", type=int, default=1)
    ap.add_argument("--projector-width", type=int, default=1920)
    ap.add_argument("--projector-height", type=int, default=1080)
    ap.add_argument("--capture-width", type=int, default=640)
    ap.add_argument("--capture-height", type=int, default=360)
    ap.add_argument("--mode", choices=MODES, default="plasma_mesh")
    ap.add_argument("--palette", choices=sorted(PALETTES), default="cyber")
    ap.add_argument("--track-scope", choices=["foreground", "full"], default="foreground")
    ap.add_argument("--max-points", type=int, default=96)
    ap.add_argument("--trail-length", type=int, default=28)
    ap.add_argument("--connection-radius", type=float, default=95.0)
    ap.add_argument("--point-radius", type=float, default=2.2)
    ap.add_argument("--feedback", type=float, default=0.91)
    ap.add_argument("--bloom", type=float, default=1.0)
    ap.add_argument("--intensity", type=float, default=1.0)
    ap.add_argument("--camera-mix", type=float, default=0.03)
    ap.add_argument("--mirror", action="store_true")
    ap.add_argument("--shader", action="store_true")
    ap.add_argument("--shader-background", choices=sorted(BACKGROUNDS), default="nebula")
    args = ap.parse_args()

    sink = FullscreenSink(window="ProjectionMapping-CyberMageSFX", display=args.display)
    bg = BackgroundMask(history=260, threshold=18.0)
    tracker = LKPointTracker(max_points=args.max_points, quality_level=0.010, min_distance=9.0)
    renderer = PointSFXRenderer(
        args.capture_width,
        args.capture_height,
        mode=args.mode,
        palette=args.palette,
        trail_length=args.trail_length,
        feedback=args.feedback,
        connection_radius=args.connection_radius,
        point_radius=args.point_radius,
        bloom=args.bloom,
    )

    shader = None
    if args.shader:
        try:
            from projection_mapping.modern_gl_fx import ModernGLPostFX

            shader = ModernGLPostFX(args.capture_width, args.capture_height)
            print(f"[cyber-sfx] shader=ModernGL backend={shader.backend}", flush=True)
        except Exception as exc:
            print(f"[cyber-sfx] shader unavailable; CPU SFX fallback: {type(exc).__name__}: {exc}", flush=True)

    t0 = time.perf_counter()
    report_t = t0
    frames = 0
    try:
        with Camera(args.camera, args.capture_width, args.capture_height) as cam:
            while True:
                now = time.perf_counter()
                frame = cam.read()
                frame = cv2.resize(frame, (args.capture_width, args.capture_height), interpolation=cv2.INTER_AREA)
                if args.mirror:
                    frame = cv2.flip(frame, 1)

                mask = None
                occupancy = 1.0
                if args.track_scope == "foreground":
                    mask = bg(frame)
                    mask = cv2.medianBlur(mask, 5)
                    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
                    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
                    occupancy = float(np.mean(mask > 0))

                points = tracker.update(frame, mask)
                fx = renderer.render(points, mask=mask, intensity=args.intensity)

                camera_mix = float(np.clip(args.camera_mix, 0.0, 1.0))
                if camera_mix > 0.0:
                    camera_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    fx = cv2.addWeighted(fx, 1.0, camera_rgb, camera_mix, 0.0)

                if shader is not None:
                    fx = shader.render(
                        fx,
                        t=now - t0,
                        intensity=args.intensity,
                        background=BACKGROUNDS[args.shader_background],
                    )

                out = cv2.resize(fx, (args.projector_width, args.projector_height), interpolation=cv2.INTER_CUBIC)
                if sink(cv2.cvtColor(out, cv2.COLOR_RGB2BGR)) is False:
                    break

                frames += 1
                if now - report_t >= 2.0:
                    speeds = np.asarray([p.speed for p in points], dtype=np.float32)
                    mean_speed = float(np.mean(speeds)) if speeds.size else 0.0
                    fast = int(np.sum(speeds > 4.0)) if speeds.size else 0
                    print(
                        f"[cyber-sfx] fps={frames / (now - report_t):.1f} tracks={len(points)} "
                        f"mean_speed={mean_speed:.2f}px/frame fast={fast} shocks={len(renderer.shockwaves)} "
                        f"scope={args.track_scope} occupancy={occupancy:.3f} "
                        f"shader={'on' if shader is not None else 'off'} F11=fullscreen ESC=exit",
                        flush=True,
                    )
                    frames = 0
                    report_t = now
    finally:
        if shader is not None:
            shader.close()
        sink.close()


if __name__ == "__main__":
    main()

"""Continuous CA Lab: Lenia/SmoothLife-inspired stateful GPU worlds.

F11 toggles fullscreen; ESC exits. R reseeds the field.
"""
from __future__ import annotations

import argparse
import time

import cv2

from projection_mapping.continuous_ca import CONTINUOUS_CA_MODES, CONTINUOUS_CA_PALETTES, ContinuousCARenderer
from projection_mapping.runtime import FullscreenSink


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=CONTINUOUS_CA_MODES, default="lenia_ring")
    ap.add_argument("--palette", choices=CONTINUOUS_CA_PALETTES, default="cyan_magenta")
    ap.add_argument("--dt", type=float, default=0.10)
    ap.add_argument("--growth-center", type=float, default=0.28)
    ap.add_argument("--growth-width", type=float, default=0.055)
    ap.add_argument("--kernel-radius", type=float, default=6.0)
    ap.add_argument("--drive", type=float, default=0.10)
    ap.add_argument("--steps", type=int, default=2)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--intensity", type=float, default=1.0)
    ap.add_argument("--display", type=int, default=1)
    ap.add_argument("--render-width", type=int, default=480)
    ap.add_argument("--render-height", type=int, default=270)
    ap.add_argument("--projector-width", type=int, default=1920)
    ap.add_argument("--projector-height", type=int, default=1080)
    args = ap.parse_args()

    renderer = ContinuousCARenderer(args.render_width, args.render_height, mode=args.mode, palette=args.palette)
    sink = FullscreenSink(window=f"ProjectionMapping-ContinuousCA-{args.mode}", display=args.display, fullscreen=True)
    print(
        f"[continuous-ca] mode={args.mode} palette={args.palette} dt={args.dt:.3f} "
        f"mu={args.growth_center:.3f} sigma={args.growth_width:.3f} radius={args.kernel_radius:.2f} "
        f"backend={renderer.backend} gl={renderer.context_info.gl_version}",
        flush=True,
    )
    t0 = time.perf_counter()
    report = t0
    frames = 0
    seed = 23
    try:
        while True:
            now = time.perf_counter()
            rgb = renderer.render(
                t=(now - t0) * args.speed,
                intensity=args.intensity,
                dt=args.dt,
                growth_center=args.growth_center,
                growth_width=args.growth_width,
                kernel_radius=args.kernel_radius,
                drive=args.drive,
                steps=args.steps,
            )
            out = cv2.resize(rgb, (args.projector_width, args.projector_height), interpolation=cv2.INTER_CUBIC)
            if sink(cv2.cvtColor(out, cv2.COLOR_RGB2BGR)) is False:
                break
            key = cv2.waitKeyEx(1)
            if key in (ord("r"), ord("R")):
                seed += 1
                renderer.reset(seed=seed)
            frames += 1
            if now - report >= 2.0:
                print(f"[continuous-ca] fps={frames/(now-report):.1f} mode={args.mode} R=reseed", flush=True)
                frames = 0
                report = now
    finally:
        renderer.close()
        sink.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

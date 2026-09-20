"""Polar Math Lab: vivid analytic radial shader studies.

Five projector-ready equation families built from rose curves, hypotrochoids, logarithmic
spirals, phyllotaxis and Bessel-like standing waves. ``--chaos`` adds cross-harmonic/domain
warping while preserving each mathematical identity. F11 toggles fullscreen; ESC exits.
"""
from __future__ import annotations

import argparse
import time

import cv2

from projection_mapping.polar_math import POLAR_MODES, POLAR_PALETTES, PolarMathRenderer
from projection_mapping.runtime import FullscreenSink


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=POLAR_MODES, default="rose_lattice")
    ap.add_argument("--palette", choices=POLAR_PALETTES, default="cyan_magenta")
    ap.add_argument("--display", type=int, default=1)
    ap.add_argument("--render-width", type=int, default=960)
    ap.add_argument("--render-height", type=int, default=540)
    ap.add_argument("--projector-width", type=int, default=1920)
    ap.add_argument("--projector-height", type=int, default=1080)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--intensity", type=float, default=1.0)
    ap.add_argument("--chaos", type=float, default=1.10)
    args = ap.parse_args()

    renderer = PolarMathRenderer(
        args.render_width,
        args.render_height,
        mode=args.mode,
        palette=args.palette,
    )
    sink = FullscreenSink(
        window=f"ProjectionMapping-PolarMath-{args.mode}",
        display=args.display,
        fullscreen=True,
    )
    print(
        f"[polar-math] mode={args.mode} palette={args.palette} chaos={args.chaos:.2f} "
        f"backend={renderer.backend} gl={renderer.context_info.gl_version} "
        f"renderer={renderer.context_info.renderer}",
        flush=True,
    )
    t0 = time.perf_counter()
    report = t0
    frames = 0
    try:
        while True:
            now = time.perf_counter()
            rgb = renderer.render(
                t=(now - t0) * args.speed,
                intensity=args.intensity,
                chaos=args.chaos,
            )
            out = cv2.resize(
                rgb,
                (args.projector_width, args.projector_height),
                interpolation=cv2.INTER_CUBIC,
            )
            if sink(cv2.cvtColor(out, cv2.COLOR_RGB2BGR)) is False:
                break
            frames += 1
            if now - report >= 2.0:
                print(
                    f"[polar-math] fps={frames/(now-report):.1f} mode={args.mode} "
                    f"chaos={args.chaos:.2f} F11=fullscreen ESC=exit",
                    flush=True,
                )
                frames = 0
                report = now
    finally:
        renderer.close()
        sink.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

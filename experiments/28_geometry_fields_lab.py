"""Geometric Fields Lab: Voronoi, power diagrams, Lloyd relaxation and geometric interference.

F11 toggles fullscreen; ESC exits.
"""
from __future__ import annotations

import argparse
import time

import cv2

from projection_mapping.geometry_fields import GEOMETRY_MODES, GEOMETRY_PALETTES, GeometryFieldRenderer
from projection_mapping.runtime import FullscreenSink


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=GEOMETRY_MODES, default="voronoi_flow")
    ap.add_argument("--palette", choices=GEOMETRY_PALETTES, default="spectral")
    ap.add_argument("--site-count", type=int, default=18)
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--relax-strength", type=float, default=0.52)
    ap.add_argument("--chaos", type=float, default=1.0)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--intensity", type=float, default=1.0)
    ap.add_argument("--display", type=int, default=1)
    ap.add_argument("--render-width", type=int, default=960)
    ap.add_argument("--render-height", type=int, default=540)
    ap.add_argument("--projector-width", type=int, default=1920)
    ap.add_argument("--projector-height", type=int, default=1080)
    args = ap.parse_args()

    renderer = GeometryFieldRenderer(
        args.render_width,
        args.render_height,
        mode=args.mode,
        palette=args.palette,
        site_count=args.site_count,
    )
    sink = FullscreenSink(window=f"ProjectionMapping-Geometry-{args.mode}", display=args.display, fullscreen=True)
    print(
        f"[geometry-fields] mode={args.mode} sites={renderer.site_count} palette={args.palette} "
        f"backend={renderer.backend} gl={renderer.context_info.gl_version} renderer={renderer.context_info.renderer}",
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
                scale=args.scale,
                relax_strength=args.relax_strength,
            )
            out = cv2.resize(rgb, (args.projector_width, args.projector_height), interpolation=cv2.INTER_CUBIC)
            if sink(cv2.cvtColor(out, cv2.COLOR_RGB2BGR)) is False:
                break
            frames += 1
            if now - report >= 2.0:
                print(f"[geometry-fields] fps={frames/(now-report):.1f} mode={args.mode}", flush=True)
                frames = 0
                report = now
    finally:
        renderer.close()
        sink.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

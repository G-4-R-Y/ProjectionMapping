"""Classic strange-attractor projector lab.

Lorenz, Rossler, Aizawa, Thomas, Halvorsen, Clifford, De Jong and Ikeda systems are
precomputed once, then rendered as dense additive GPU point clouds. F11 toggles fullscreen;
ESC exits.
"""
from __future__ import annotations

import argparse
import time

import cv2

from projection_mapping.attractor_lab import ATTRACTOR_MODES, ATTRACTOR_PALETTES, AttractorRenderer
from projection_mapping.runtime import FullscreenSink


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=ATTRACTOR_MODES, default="lorenz")
    ap.add_argument("--palette", choices=ATTRACTOR_PALETTES, default="cyan_magenta")
    ap.add_argument("--points", type=int, default=50000)
    ap.add_argument("--display", type=int, default=1)
    ap.add_argument("--render-width", type=int, default=960)
    ap.add_argument("--render-height", type=int, default=540)
    ap.add_argument("--projector-width", type=int, default=1920)
    ap.add_argument("--projector-height", type=int, default=1080)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--intensity", type=float, default=1.0)
    ap.add_argument("--zoom", type=float, default=1.35)
    ap.add_argument("--point-size", type=float, default=2.2)
    ap.add_argument("--bloom", type=float, default=1.0)
    args = ap.parse_args()

    renderer = AttractorRenderer(
        args.render_width,
        args.render_height,
        mode=args.mode,
        palette=args.palette,
        points=args.points,
    )
    sink = FullscreenSink(
        window=f"ProjectionMapping-Attractor-{args.mode}",
        display=args.display,
        fullscreen=True,
    )
    print(
        f"[attractor] mode={args.mode} points={renderer.point_count} palette={args.palette} "
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
                zoom=args.zoom,
                point_size=args.point_size,
                bloom=args.bloom,
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
                    f"[attractor] fps={frames/(now-report):.1f} mode={args.mode} "
                    f"points={renderer.point_count} F11=fullscreen ESC=exit",
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

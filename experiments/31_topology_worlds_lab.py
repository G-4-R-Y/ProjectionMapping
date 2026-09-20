"""Topology Worlds Lab: knots, linked fibers, gyroids, minimal surfaces and Möbius geometry.

F11 toggles fullscreen; ESC exits.
"""
from __future__ import annotations

import argparse
import time

import cv2

from projection_mapping.runtime import FullscreenSink
from projection_mapping.topology_worlds import TOPOLOGY_MODES, TOPOLOGY_PALETTES, TopologyWorldRenderer


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=TOPOLOGY_MODES, default="torus_knot")
    ap.add_argument("--palette", choices=TOPOLOGY_PALETTES, default="cyan_magenta")
    ap.add_argument("--param-a", type=float, default=0.5)
    ap.add_argument("--param-b", type=float, default=0.5)
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--chaos", type=float, default=1.0)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--intensity", type=float, default=1.0)
    ap.add_argument("--display", type=int, default=1)
    ap.add_argument("--render-width", type=int, default=720)
    ap.add_argument("--render-height", type=int, default=405)
    ap.add_argument("--projector-width", type=int, default=1920)
    ap.add_argument("--projector-height", type=int, default=1080)
    args = ap.parse_args()

    renderer = TopologyWorldRenderer(args.render_width, args.render_height, mode=args.mode, palette=args.palette)
    sink = FullscreenSink(window=f"ProjectionMapping-Topology-{args.mode}", display=args.display, fullscreen=True)
    print(
        f"[topology] mode={args.mode} palette={args.palette} a={args.param_a:.2f} b={args.param_b:.2f} "
        f"backend={renderer.backend} gl={renderer.context_info.gl_version}",
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
                param_a=args.param_a,
                param_b=args.param_b,
            )
            out = cv2.resize(rgb, (args.projector_width, args.projector_height), interpolation=cv2.INTER_CUBIC)
            if sink(cv2.cvtColor(out, cv2.COLOR_RGB2BGR)) is False:
                break
            frames += 1
            if now - report >= 2.0:
                print(f"[topology] fps={frames/(now-report):.1f} mode={args.mode}", flush=True)
                frames = 0
                report = now
    finally:
        renderer.close()
        sink.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

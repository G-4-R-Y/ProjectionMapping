"""Optimal Transport Lab: entropic Sinkhorn morphs between designed point distributions.

F11 toggles fullscreen; ESC exits.
"""
from __future__ import annotations

import argparse
import time

import cv2

from projection_mapping.optimal_transport import TRANSPORT_MODES, TRANSPORT_PALETTES, OptimalTransportRenderer
from projection_mapping.runtime import FullscreenSink


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=TRANSPORT_MODES, default="rose_to_lissajous")
    ap.add_argument("--palette", choices=TRANSPORT_PALETTES, default="spectral")
    ap.add_argument("--points", type=int, default=384)
    ap.add_argument("--epsilon", type=float, default=0.08)
    ap.add_argument("--point-size", type=float, default=7.0)
    ap.add_argument("--arc", type=float, default=0.18)
    ap.add_argument("--cycles", type=float, default=0.18)
    ap.add_argument("--intensity", type=float, default=1.0)
    ap.add_argument("--display", type=int, default=1)
    ap.add_argument("--render-width", type=int, default=960)
    ap.add_argument("--render-height", type=int, default=540)
    ap.add_argument("--projector-width", type=int, default=1920)
    ap.add_argument("--projector-height", type=int, default=1080)
    args = ap.parse_args()

    renderer = OptimalTransportRenderer(
        args.render_width,
        args.render_height,
        mode=args.mode,
        palette=args.palette,
        points=args.points,
        epsilon=args.epsilon,
    )
    sink = FullscreenSink(window=f"ProjectionMapping-OptimalTransport-{args.mode}", display=args.display, fullscreen=True)
    print(
        f"[optimal-transport] mode={args.mode} points={renderer.points} epsilon={args.epsilon:.4f} "
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
                t=now - t0,
                intensity=args.intensity,
                point_size=args.point_size,
                arc=args.arc,
                cycles=args.cycles,
            )
            out = cv2.resize(rgb, (args.projector_width, args.projector_height), interpolation=cv2.INTER_CUBIC)
            if sink(cv2.cvtColor(out, cv2.COLOR_RGB2BGR)) is False:
                break
            frames += 1
            if now - report >= 2.0:
                print(f"[optimal-transport] fps={frames/(now-report):.1f} mode={args.mode}", flush=True)
                frames = 0
                report = now
    finally:
        renderer.close()
        sink.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

"""Wave Equation / Cymatics Lab: persistent GPU membrane dynamics and driven modes.

F11 toggles fullscreen; ESC exits. R reseeds the membrane state.
"""
from __future__ import annotations

import argparse
import time

import cv2

from projection_mapping.runtime import FullscreenSink
from projection_mapping.wave_equation import WAVE_MODES, WAVE_PALETTES, WaveEquationRenderer


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=WAVE_MODES, default="chladni_drive")
    ap.add_argument("--palette", choices=WAVE_PALETTES, default="ultraviolet")
    ap.add_argument("--drive", type=float, default=0.45)
    ap.add_argument("--tension", type=float, default=0.22)
    ap.add_argument("--damping", type=float, default=0.018)
    ap.add_argument("--steps", type=int, default=3)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--intensity", type=float, default=1.0)
    ap.add_argument("--display", type=int, default=1)
    ap.add_argument("--render-width", type=int, default=640)
    ap.add_argument("--render-height", type=int, default=360)
    ap.add_argument("--projector-width", type=int, default=1920)
    ap.add_argument("--projector-height", type=int, default=1080)
    args = ap.parse_args()

    renderer = WaveEquationRenderer(args.render_width, args.render_height, mode=args.mode, palette=args.palette)
    sink = FullscreenSink(window=f"ProjectionMapping-WaveEquation-{args.mode}", display=args.display, fullscreen=True)
    print(
        f"[wave-equation] mode={args.mode} palette={args.palette} drive={args.drive:.2f} "
        f"tension={args.tension:.3f} damping={args.damping:.4f} steps={args.steps} "
        f"backend={renderer.backend} gl={renderer.context_info.gl_version}",
        flush=True,
    )
    t0 = time.perf_counter()
    report = t0
    frames = 0
    seed = 19
    try:
        while True:
            now = time.perf_counter()
            rgb = renderer.render(
                t=(now - t0) * args.speed,
                intensity=args.intensity,
                drive=args.drive,
                tension=args.tension,
                damping=args.damping,
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
                print(f"[wave-equation] fps={frames/(now-report):.1f} mode={args.mode} R=reseed", flush=True)
                frames = 0
                report = now
    finally:
        renderer.close()
        sink.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

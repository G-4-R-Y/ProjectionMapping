"""Stateful Gray-Scott reaction-diffusion projector lab.

The simulation owns persistent GPU state and evolves continuously between frames.
F11 toggles fullscreen; ESC exits. Press R in the visual window to reseed.
"""
from __future__ import annotations

import argparse
import time

import cv2

from projection_mapping.reaction_diffusion import (
    REACTION_PALETTES,
    REACTION_PRESETS,
    ReactionDiffusionRenderer,
)
from projection_mapping.runtime import FullscreenSink


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", choices=tuple(REACTION_PRESETS), default="coral")
    ap.add_argument("--palette", choices=REACTION_PALETTES, default="cyan_magenta")
    ap.add_argument("--display", type=int, default=1)
    ap.add_argument("--render-width", type=int, default=640)
    ap.add_argument("--render-height", type=int, default=360)
    ap.add_argument("--projector-width", type=int, default=1920)
    ap.add_argument("--projector-height", type=int, default=1080)
    ap.add_argument("--steps", type=int, default=8)
    ap.add_argument("--dt", type=float, default=1.0)
    ap.add_argument("--drive", type=float, default=0.35)
    ap.add_argument("--intensity", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    renderer = ReactionDiffusionRenderer(
        args.render_width,
        args.render_height,
        preset=args.preset,
        palette=args.palette,
        seed=args.seed,
    )
    sink = FullscreenSink(
        window=f"ProjectionMapping-ReactionDiffusion-{args.preset}",
        display=args.display,
        fullscreen=True,
    )
    print(
        f"[reaction-diffusion] preset={args.preset} palette={args.palette} steps={args.steps} "
        f"drive={args.drive:.2f} backend={renderer.backend} gl={renderer.context_info.gl_version} "
        f"renderer={renderer.context_info.renderer}",
        flush=True,
    )
    t0 = time.perf_counter()
    report = t0
    frames = 0
    seed = args.seed
    try:
        while True:
            now = time.perf_counter()
            rgb = renderer.render(
                t=now - t0,
                intensity=args.intensity,
                drive=args.drive,
                steps=args.steps,
                dt=args.dt,
            )
            out = cv2.resize(
                rgb,
                (args.projector_width, args.projector_height),
                interpolation=cv2.INTER_CUBIC,
            )
            if sink(cv2.cvtColor(out, cv2.COLOR_RGB2BGR)) is False:
                break
            if sink.last_key in (ord("r"), ord("R")):
                seed += 1
                renderer.reset(seed=seed)
                print(f"[reaction-diffusion] reseed={seed}", flush=True)
            frames += 1
            if now - report >= 2.0:
                print(
                    f"[reaction-diffusion] fps={frames/(now-report):.1f} preset={args.preset} "
                    f"steps={args.steps} drive={args.drive:.2f} R=reseed F11=fullscreen ESC=exit",
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

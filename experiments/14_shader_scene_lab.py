"""ModernGL shader scene lab for projector-ready high-end procedural visuals."""
from __future__ import annotations

import argparse
import time

import cv2
import numpy as np

from projection_mapping.runtime import FullscreenSink
from projection_mapping.shader_scenes import (
    PALETTE_IDS,
    SCENE_IDS,
    SHADER_SCENE_PRESETS,
    ShaderSceneRenderer,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", choices=sorted(SHADER_SCENE_PRESETS), default=None)
    ap.add_argument("--scene", choices=sorted(SCENE_IDS), default="liquid_chrome")
    ap.add_argument("--scene-b", choices=sorted(SCENE_IDS), default="liquid_chrome")
    ap.add_argument("--scene-mix", type=float, default=0.0)
    ap.add_argument("--palette", choices=sorted(PALETTE_IDS), default="cyan_magenta")
    ap.add_argument("--palette-cycle", type=float, default=0.0, help="palette phase cycles per second")
    ap.add_argument("--display", type=int, default=1)
    ap.add_argument("--projector-width", type=int, default=1920)
    ap.add_argument("--projector-height", type=int, default=1080)
    ap.add_argument("--render-width", type=int, default=960)
    ap.add_argument("--render-height", type=int, default=540)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--intensity", type=float, default=1.0)
    ap.add_argument("--chaos", type=float, default=1.15)
    args = ap.parse_args()

    scene = args.scene
    scene_b = args.scene_b
    scene_mix = float(np.clip(args.scene_mix, 0.0, 1.0))
    palette = args.palette
    palette_cycle = args.palette_cycle
    speed = args.speed
    intensity = args.intensity
    chaos = args.chaos
    if args.preset is not None:
        preset = SHADER_SCENE_PRESETS[args.preset]
        scene = preset.scene
        scene_b = preset.scene_b
        scene_mix = preset.scene_mix
        palette = preset.palette
        palette_cycle = preset.palette_cycle
        speed *= preset.speed
        intensity *= preset.intensity
        chaos = preset.chaos

    renderer = ShaderSceneRenderer(args.render_width, args.render_height)
    print(
        f"[shader-lab] ModernGL backend={renderer.backend} preset={args.preset or 'custom'} "
        f"scene={scene}->{scene_b} mix={scene_mix:.2f} palette={palette} chaos={chaos:.2f}",
        flush=True,
    )
    sink = FullscreenSink(window=f"ProjectionMapping-Shader-{args.preset or scene}", display=args.display)
    t0 = time.perf_counter()
    report_t = t0
    frames = 0
    try:
        while True:
            now = time.perf_counter()
            rgb = renderer.render(
                scene,
                t=(now - t0) * speed,
                intensity=intensity,
                chaos=chaos,
                palette=palette,
                palette_shift=(now - t0) * palette_cycle,
                scene_b=scene_b,
                scene_mix=scene_mix,
            )
            out = cv2.resize(
                rgb,
                (args.projector_width, args.projector_height),
                interpolation=cv2.INTER_CUBIC,
            )
            if sink(cv2.cvtColor(out, cv2.COLOR_RGB2BGR)) is False:
                break
            frames += 1
            if now - report_t >= 2.0:
                print(
                    f"[shader-lab] scene={scene}->{scene_b} mix={scene_mix:.2f} "
                    f"palette={palette} chaos={chaos:.2f} "
                    f"fps={frames / (now - report_t):.1f} F11=fullscreen ESC=exit",
                    flush=True,
                )
                frames = 0
                report_t = now
    finally:
        renderer.close()
        sink.close()


if __name__ == "__main__":
    main()

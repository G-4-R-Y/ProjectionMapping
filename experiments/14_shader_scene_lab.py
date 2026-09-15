"""ModernGL shader scene lab for projector-ready high-end procedural visuals."""
from __future__ import annotations

import argparse
import time

import cv2

from projection_mapping.runtime import FullscreenSink
from projection_mapping.shader_scenes import SCENE_IDS, ShaderSceneRenderer


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", choices=sorted(SCENE_IDS), default="event_horizon")
    ap.add_argument("--display", type=int, default=1)
    ap.add_argument("--projector-width", type=int, default=1920)
    ap.add_argument("--projector-height", type=int, default=1080)
    ap.add_argument("--render-width", type=int, default=960)
    ap.add_argument("--render-height", type=int, default=540)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--intensity", type=float, default=1.0)
    args = ap.parse_args()

    renderer = ShaderSceneRenderer(args.render_width, args.render_height)
    print(f"[shader-lab] ModernGL backend={renderer.backend} scene={args.scene}", flush=True)
    sink = FullscreenSink(window=f"ProjectionMapping-Shader-{args.scene}", display=args.display)
    t0 = time.perf_counter()
    report_t = t0
    frames = 0
    try:
        while True:
            now = time.perf_counter()
            rgb = renderer.render(args.scene, t=(now - t0) * args.speed, intensity=args.intensity)
            out = cv2.resize(rgb, (args.projector_width, args.projector_height), interpolation=cv2.INTER_CUBIC)
            if sink(cv2.cvtColor(out, cv2.COLOR_RGB2BGR)) is False:
                break
            frames += 1
            if now - report_t >= 2.0:
                print(
                    f"[shader-lab] scene={args.scene} fps={frames / (now - report_t):.1f} "
                    "F11=fullscreen ESC=exit",
                    flush=True,
                )
                frames = 0
                report_t = now
    finally:
        renderer.close()
        sink.close()


if __name__ == "__main__":
    main()

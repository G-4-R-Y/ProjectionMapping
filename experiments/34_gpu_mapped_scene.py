"""GPU-native shader scene -> surface profile -> projector window.

The source scene, corner-pin compositor and presentation framebuffer share one
OpenGL context. No framebuffer readback or OpenCV resize occurs in the frame loop.
F11 toggles fullscreen and ESC returns to the control deck.
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from projection_mapping.gpu_surface_mapping import GPUSurfaceCompositor, ShaderScenePass
from projection_mapping.native_gl_window import NativeGLWindow
from projection_mapping.shader_scenes import SCENE_IDS
from projection_mapping.surface_mapping import SurfaceMapProfile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GPU-native mapped procedural scene")
    parser.add_argument("--profile", default="calibration_data/surface_map.json")
    parser.add_argument("--scene", choices=sorted(SCENE_IDS), default="liquid_chrome")
    parser.add_argument("--display", type=int, default=1)
    parser.add_argument("--render-width", type=int, default=960)
    parser.add_argument("--render-height", type=int, default=540)
    parser.add_argument("--window-width", type=int, default=1280)
    parser.add_argument("--window-height", type=int, default=720)
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--intensity", type=float, default=1.0)
    parser.add_argument("--chaos", type=float, default=1.15)
    parser.add_argument("--windowed", action="store_true")
    parser.add_argument("--no-vsync", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    profile_path = Path(args.profile)
    profile = (
        SurfaceMapProfile.load(profile_path)
        if profile_path.exists()
        else SurfaceMapProfile(projector_width=args.window_width, projector_height=args.window_height)
    )
    window = NativeGLWindow(
        title=f"ProjectionMapping-GPU-{args.scene}",
        display=args.display,
        width=args.window_width,
        height=args.window_height,
        fullscreen=not args.windowed,
        vsync=not args.no_vsync,
    )
    scene = ShaderScenePass(window.ctx, args.render_width, args.render_height)
    mapper = GPUSurfaceCompositor(window.ctx, profile)
    monitor = window.monitors[args.display]
    print(
        f"[gpu-map] scene={args.scene} profile={profile_path} surfaces={len(profile.surfaces)} "
        f"display={monitor.index}:{monitor.name} {monitor.width}x{monitor.height}@{monitor.refresh_rate} "
        f"renderer={window.context_info.renderer} readbacks=0",
        flush=True,
    )
    started = time.perf_counter()
    report = started
    frames = 0
    try:
        while not window.should_close:
            now = time.perf_counter()
            texture = scene.render(
                args.scene,
                t=(now - started) * args.speed,
                intensity=args.intensity,
                chaos=args.chaos,
            )
            width, height = window.framebuffer_size
            mapper.render(texture, width, height)
            window.present()
            frames += 1
            if now - report >= 2.0:
                print(
                    f"[gpu-map] fps={frames / (now - report):.1f} framebuffer={width}x{height} "
                    "readbacks=0 F11=fullscreen ESC=exit",
                    flush=True,
                )
                frames = 0
                report = now
    finally:
        mapper.close()
        scene.close()
        window.close()


if __name__ == "__main__":
    main()

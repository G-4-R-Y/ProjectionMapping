"""Cyber Mage v3: tracked motion -> dense GPU point-particle field.

The visual target is contemporary point-cloud / particle VFX rather than debug lines. Generic
Shi-Tomasi/LK tracks remain measurement points only; a spatially diverse subset becomes control
emitters for a 32k+ GPU particle simulation with data-point materials, curl/circuit vector fields,
feedback and bloom. No guessed hand semantics are used here.

If ModernGL is unavailable, --engine auto falls back to the legacy CPU point-SFX renderer.
F11 toggles fullscreen; ESC exits.
"""
from __future__ import annotations

import argparse
import time

import cv2
import numpy as np

from projection_mapping.capture import Camera
from projection_mapping.cyber_particle_adapter import (
    CYBER_PARTICLE_MODES,
    profile_for_mode,
    tracked_point_emitters,
)
from projection_mapping.gpu_particles import GPUParticleField
from projection_mapping.perception import BackgroundMask
from projection_mapping.point_sfx import PALETTES as LEGACY_PALETTES, PointSFXRenderer
from projection_mapping.point_tracker import LKPointTracker
from projection_mapping.runtime import FullscreenSink


LEGACY_MODES = ("plasma_mesh", "constellation", "afterburner", "liquid_wire")
MODES = (*CYBER_PARTICLE_MODES, *LEGACY_MODES)
BACKGROUNDS = {"black": 0, "nebula": 1, "grid": 2, "liquid": 3}

LEGACY_TO_GPU = {
    "plasma_mesh": "data_swarm",
    "constellation": "circuit_grid",
    "afterburner": "event_horizon",
    "liquid_wire": "cosmic_roam",
}
GPU_TO_LEGACY = {
    "data_swarm": "plasma_mesh",
    "circuit_grid": "constellation",
    "orbit_core": "plasma_mesh",
    "event_horizon": "afterburner",
    "cosmic_roam": "liquid_wire",
}
GPU_PALETTE_MAP = {
    "cyan_magenta": "cyan_magenta",
    "cyber": "cyan_magenta",
    "ultraviolet": "ultraviolet",
    "deep_ocean": "deep_ocean",
    "sunset_neon": "sunset_neon",
    "ion": "deep_ocean",
    "acid": "bio",
    "ember": "sunset_neon",
    "ice": "deep_ocean",
}


def _gpu_mode(mode: str) -> str:
    return LEGACY_TO_GPU.get(mode, mode)


def _legacy_mode(mode: str) -> str:
    return GPU_TO_LEGACY.get(mode, mode)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--display", type=int, default=1)
    ap.add_argument("--projector-width", type=int, default=1920)
    ap.add_argument("--projector-height", type=int, default=1080)
    ap.add_argument("--capture-width", type=int, default=640)
    ap.add_argument("--capture-height", type=int, default=360)
    ap.add_argument("--render-width", type=int, default=768)
    ap.add_argument("--render-height", type=int, default=432)
    ap.add_argument("--engine", choices=["auto", "gpu", "legacy"], default="auto")
    ap.add_argument("--mode", choices=MODES, default="data_swarm")
    ap.add_argument("--palette", choices=sorted(LEGACY_PALETTES), default="cyan_magenta")
    ap.add_argument("--material", choices=["auto", *sorted(GPUParticleField.MATERIALS)], default="auto")
    ap.add_argument("--particles", type=int, default=32768)
    ap.add_argument("--track-scope", choices=["foreground", "full"], default="foreground")
    ap.add_argument("--max-points", type=int, default=144)
    ap.add_argument("--trail-length", type=int, default=28)
    ap.add_argument("--connection-radius", type=float, default=95.0)
    ap.add_argument("--point-radius", type=float, default=2.2)
    ap.add_argument("--feedback", type=float, default=None)
    ap.add_argument("--bloom", type=float, default=None)
    ap.add_argument("--intensity", type=float, default=1.0)
    ap.add_argument("--camera-mix", type=float, default=0.02)
    ap.add_argument("--mirror", action="store_true")
    ap.add_argument("--shader", action="store_true", help="legacy CPU renderer post FX only")
    ap.add_argument("--shader-background", choices=sorted(BACKGROUNDS), default="nebula")
    args = ap.parse_args()

    sink = FullscreenSink(window="ProjectionMapping-CyberMage", display=args.display)
    bg = BackgroundMask(history=260, threshold=18.0)
    tracker = LKPointTracker(max_points=args.max_points, quality_level=0.009, min_distance=7.0)

    gpu_mode = _gpu_mode(args.mode)
    profile = profile_for_mode(gpu_mode)
    particle_field = None
    legacy_renderer = None

    if args.engine != "legacy":
        try:
            particle_field = GPUParticleField(
                args.render_width,
                args.render_height,
                capacity=args.particles,
                palette=GPU_PALETTE_MAP.get(args.palette, "cyan_magenta"),
                material=profile.material if args.material == "auto" else args.material,
            )
            print(
                f"[cyber-mage] engine=gpu mode={gpu_mode} particles={particle_field.capacity} "
                f"material={profile.material if args.material == 'auto' else args.material} "
                f"palette={args.palette} gl={particle_field.context_info.gl_version} "
                f"renderer={particle_field.context_info.renderer} backend={particle_field.backend}",
                flush=True,
            )
        except Exception as exc:
            if args.engine == "gpu":
                sink.close()
                raise
            print(
                f"[cyber-mage] GPU unavailable; falling back to legacy CPU SFX: "
                f"{type(exc).__name__}: {exc}",
                flush=True,
            )

    if particle_field is None:
        legacy_renderer = PointSFXRenderer(
            args.capture_width,
            args.capture_height,
            mode=_legacy_mode(args.mode),
            palette=args.palette,
            trail_length=args.trail_length,
            feedback=0.91 if args.feedback is None else args.feedback,
            connection_radius=args.connection_radius,
            point_radius=args.point_radius,
            bloom=1.0 if args.bloom is None else args.bloom,
        )

    post_shader = None
    if legacy_renderer is not None and args.shader:
        try:
            from projection_mapping.modern_gl_fx import ModernGLPostFX

            post_shader = ModernGLPostFX(args.capture_width, args.capture_height)
            print(f"[cyber-mage] legacy post=ModernGL backend={post_shader.backend}", flush=True)
        except Exception as exc:
            print(
                f"[cyber-mage] legacy post unavailable: {type(exc).__name__}: {exc}",
                flush=True,
            )

    t0 = time.perf_counter()
    last = t0
    report_t = t0
    frames = 0

    try:
        with Camera(args.camera, args.capture_width, args.capture_height) as cam:
            while True:
                now = time.perf_counter()
                t = now - t0
                dt = float(np.clip(now - last, 1e-4, 0.08))
                last = now

                frame = cam.read()
                frame = cv2.resize(
                    frame,
                    (args.capture_width, args.capture_height),
                    interpolation=cv2.INTER_AREA,
                )
                if args.mirror:
                    frame = cv2.flip(frame, 1)

                mask = None
                occupancy = 1.0
                if args.track_scope == "foreground":
                    mask = bg(frame)
                    mask = cv2.medianBlur(mask, 5)
                    mask = cv2.morphologyEx(
                        mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)
                    )
                    mask = cv2.morphologyEx(
                        mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)
                    )
                    occupancy = float(np.mean(mask > 0))

                points = tracker.update(frame, mask)
                speeds = np.asarray([p.speed for p in points], dtype=np.float32)
                mean_speed = float(np.mean(speeds)) if speeds.size else 0.0
                motion = float(np.clip(mean_speed / 8.0, 0.0, 1.0))
                strike = (
                    float(np.clip((np.percentile(speeds, 92) - 3.0) / 10.0, 0.0, 1.0))
                    if speeds.size
                    else 0.0
                )

                if particle_field is not None:
                    emitters = tracked_point_emitters(
                        points,
                        args.capture_width,
                        args.capture_height,
                        intensity=args.intensity,
                    )
                    particle_field.set_material(
                        profile.material if args.material == "auto" else args.material
                    )
                    feedback = profile.feedback if args.feedback is None else float(args.feedback)
                    bloom = profile.bloom if args.bloom is None else float(args.bloom)
                    fx = particle_field.render(
                        emitters,
                        t=t,
                        dt=dt,
                        emission_rate=profile.emission_rate
                        * (0.72 + 0.72 * args.intensity)
                        * (0.72 + 0.46 * motion),
                        turbulence=profile.turbulence * (0.82 + 0.55 * motion),
                        drag=profile.drag,
                        feedback=feedback,
                        bloom=bloom,
                        energy=0.92 + 0.38 * args.intensity + 0.30 * motion,
                        bass=motion,
                        strike=strike,
                        drop=max(0.0, strike - 0.45),
                        field_mode=profile.field_mode,
                        field_strength=profile.field_strength * (0.86 + 0.34 * motion),
                        field_scale=profile.field_scale,
                        field_spin=profile.field_spin,
                        well_strength=profile.well_strength,
                        nebula_mix=profile.nebula_mix,
                    )
                    camera_frame = cv2.resize(
                        frame,
                        (args.render_width, args.render_height),
                        interpolation=cv2.INTER_AREA,
                    )
                else:
                    emitters = []
                    fx = legacy_renderer.render(points, mask=mask, intensity=args.intensity)
                    camera_frame = frame
                    if post_shader is not None:
                        fx = post_shader.render(
                            fx,
                            t=t,
                            intensity=args.intensity,
                            background=BACKGROUNDS[args.shader_background],
                        )

                camera_mix = float(np.clip(args.camera_mix, 0.0, 1.0))
                if camera_mix > 0.0:
                    camera_rgb = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2RGB)
                    fx = cv2.addWeighted(fx, 1.0, camera_rgb, camera_mix, 0.0)

                out = cv2.resize(
                    fx,
                    (args.projector_width, args.projector_height),
                    interpolation=cv2.INTER_CUBIC,
                )
                if sink(cv2.cvtColor(out, cv2.COLOR_RGB2BGR)) is False:
                    break

                frames += 1
                if now - report_t >= 2.0:
                    print(
                        f"[cyber-mage] fps={frames / (now - report_t):.1f} "
                        f"engine={'gpu' if particle_field is not None else 'legacy'} "
                        f"mode={gpu_mode if particle_field is not None else _legacy_mode(args.mode)} "
                        f"tracks={len(points)} emitters={len(emitters)} mean_speed={mean_speed:.2f} "
                        f"occupancy={occupancy:.3f} F11=fullscreen ESC=exit",
                        flush=True,
                    )
                    frames = 0
                    report_t = now
    finally:
        if post_shader is not None:
            post_shader.close()
        if particle_field is not None:
            particle_field.close()
        sink.close()


if __name__ == "__main__":
    main()

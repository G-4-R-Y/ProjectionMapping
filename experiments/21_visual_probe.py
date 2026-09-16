"""Compile/render smoke test for the high-end visual stack.

This is intentionally a hardware probe rather than a normal unit test: it creates real OpenGL
contexts, compiles every promoted shader family, renders tiny frames, and prints timings/errors.
Use it after graphics-driver or shader changes before debugging the TUI.
"""
from __future__ import annotations

import time
import traceback

import numpy as np


def _probe(name: str, fn) -> bool:
    start = time.perf_counter()
    try:
        fn()
    except Exception as exc:
        print(f"[visual-probe] FAIL {name}: {type(exc).__name__}: {exc}", flush=True)
        traceback.print_exc()
        return False
    print(
        f"[visual-probe] OK   {name}: {(time.perf_counter() - start) * 1000.0:.1f} ms",
        flush=True,
    )
    return True


def _event_horizon_seam_metric(frame: np.ndarray) -> tuple[float, float]:
    """Return mean/p95 two-pixel jump across the old negative-X atan branch cut."""
    h, w, _ = frame.shape
    mid_y = h // 2
    mid_x = w // 2
    lo = max(4, int(w * 0.08))
    hi = max(lo + 1, mid_x - int(w * 0.10))
    a = frame[mid_y - 1, lo:hi].astype(np.float32)
    b = frame[mid_y + 1, lo:hi].astype(np.float32)
    jump = np.mean(np.abs(a - b), axis=1)
    return float(np.mean(jump)), float(np.percentile(jump, 95))


def main() -> None:
    from projection_mapping.graphics_runtime import probe_context

    report = probe_context(require=330)
    print(
        f"[visual-probe] GL backend={report.backend} version={report.gl_version} "
        f"vendor={report.vendor} renderer={report.renderer}",
        flush=True,
    )

    ok = True

    def polar() -> None:
        from projection_mapping.polar_math import POLAR_MODES, PolarMathRenderer

        r = PolarMathRenderer(320, 180)
        try:
            for i, mode in enumerate(POLAR_MODES):
                frame = r.render(
                    t=0.37 + i * 0.11,
                    mode=mode,
                    intensity=1.0,
                    chaos=1.25,
                )
                assert frame.shape == (180, 320, 3)
                assert np.isfinite(frame).all()
                print(
                    f"[visual-probe]   polar={mode} peak={int(frame.max())} "
                    f"mean={float(frame.mean()):.2f}",
                    flush=True,
                )
        finally:
            r.close()

    def scenes() -> None:
        from projection_mapping.shader_scenes import SCENE_IDS, ShaderSceneRenderer

        r = ShaderSceneRenderer(321, 181)
        try:
            for i, scene in enumerate(SCENE_IDS):
                frame = r.render(scene, t=0.43 + i * 0.13, intensity=1.0, chaos=1.25)
                assert frame.shape == (181, 321, 3)
                assert np.isfinite(frame).all()
                print(
                    f"[visual-probe]   scene={scene} peak={int(frame.max())} "
                    f"mean={float(frame.mean()):.2f}",
                    flush=True,
                )
                if scene == "event_horizon":
                    seam_mean, seam_p95 = _event_horizon_seam_metric(frame)
                    print(
                        f"[visual-probe]   event_horizon seam_mean={seam_mean:.2f} "
                        f"seam_p95={seam_p95:.2f}",
                        flush=True,
                    )
                    assert seam_mean < 38.0 and seam_p95 < 96.0, (
                        f"Event Horizon seam regression: mean={seam_mean:.2f}, p95={seam_p95:.2f}"
                    )
        finally:
            r.close()

    def famous_math() -> None:
        from projection_mapping.famous_math import MATH_MODES, FamousMathRenderer

        r = FamousMathRenderer(240, 135)
        try:
            for i, mode in enumerate(MATH_MODES):
                frame = r.render(
                    t=0.29 + i * 0.17,
                    mode=mode,
                    intensity=1.0,
                    chaos=1.15,
                )
                assert frame.shape == (135, 240, 3)
                assert np.isfinite(frame).all()
                assert int(frame.max()) > 16, f"{mode} rendered suspiciously dark"
                print(
                    f"[visual-probe]   famous_math={mode} peak={int(frame.max())} "
                    f"mean={float(frame.mean()):.2f}",
                    flush=True,
                )
        finally:
            r.close()

    def reaction_diffusion() -> None:
        from projection_mapping.reaction_diffusion import REACTION_PRESETS, ReactionDiffusionRenderer

        r = ReactionDiffusionRenderer(192, 108, preset="coral", seed=11)
        try:
            frame = None
            for i, preset in enumerate(REACTION_PRESETS):
                r.reset(seed=11 + i)
                for step in range(8):
                    frame = r.render(
                        t=i + step / 30.0,
                        preset=preset,
                        intensity=1.0,
                        drive=0.45,
                        steps=4,
                    )
                assert frame is not None and frame.shape == (108, 192, 3)
                assert np.isfinite(frame).all()
                print(
                    f"[visual-probe]   reaction={preset} peak={int(frame.max())} "
                    f"mean={float(frame.mean()):.2f}",
                    flush=True,
                )
        finally:
            r.close()

    def particles() -> None:
        from projection_mapping.gpu_particles import GPUParticleField, ParticleEmitter

        field = GPUParticleField(320, 180, capacity=4096, palette="cyber")
        try:
            for material in field.MATERIALS:
                field.set_material(material)
                frame = None
                for i in range(12):
                    t = i / 60.0
                    emitters = [
                        ParticleEmitter(0.43, 0.50, 0.62, -0.16, 1.0, 0.78, 0.018),
                        ParticleEmitter(0.57, 0.50, -0.62, 0.16, 1.0, 0.96, 0.018),
                    ]
                    frame = field.render(
                        emitters,
                        t=t,
                        dt=1 / 60,
                        emission_rate=10000,
                        bloom=1.2,
                        energy=1.2,
                        strike=0.55 if material in {"spark", "shock_ring"} else 0.15,
                        drop=0.65 if material == "shock_ring" else 0.0,
                    )
                assert frame is not None and frame.shape == (180, 320, 3)
                print(
                    f"[visual-probe]   particles material={material} "
                    f"peak={int(frame.max())} mean={float(frame.mean()):.2f}",
                    flush=True,
                )
        finally:
            field.close()

    ok &= _probe("Polar Math all modes @ chaos=1.25", polar)
    ok &= _probe("Shader Scene Lab all modes + seam regression", scenes)
    ok &= _probe("Famous Math all modes", famous_math)
    ok &= _probe("Gray-Scott reaction diffusion presets", reaction_diffusion)
    ok &= _probe("GPU particle materials", particles)
    if not ok:
        raise SystemExit(2)
    print("[visual-probe] PASS", flush=True)


if __name__ == "__main__":
    main()

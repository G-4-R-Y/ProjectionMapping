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
    """Return mean/p95 two-pixel jump across the old negative-X atan branch cut.

    Event Horizon is deliberately rendered at an odd height for this check, so the rows around the
    horizontal centerline straddle the place where atan(y, x) used to jump from -pi to +pi. The
    metric excludes the singularity itself and outer vignette. It is not an aesthetic score; it is
    a regression sensor for the very visible hard seam observed on the projector.
    """
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
                frame = r.render(t=0.37 + i * 0.11, mode=mode, intensity=1.0)
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
                    # A real branch cut is a large step across much of the negative X axis.
                    # Keep thresholds intentionally loose so natural turbulent detail is allowed.
                    assert seam_mean < 38.0 and seam_p95 < 96.0, (
                        f"Event Horizon seam regression: mean={seam_mean:.2f}, p95={seam_p95:.2f}"
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

    ok &= _probe("Polar Math all modes", polar)
    ok &= _probe("Shader Scene Lab all modes + seam regression", scenes)
    ok &= _probe("GPU particle materials", particles)
    if not ok:
        raise SystemExit(2)
    print("[visual-probe] PASS", flush=True)


if __name__ == "__main__":
    main()

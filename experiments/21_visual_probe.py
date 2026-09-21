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
    print(f"[visual-probe] OK   {name}: {(time.perf_counter() - start) * 1000.0:.1f} ms", flush=True)
    return True


def _event_horizon_seam_metric(frame: np.ndarray) -> tuple[float, float]:
    h, w, _ = frame.shape
    mid_y = h // 2
    mid_x = w // 2
    lo = max(4, int(w * 0.08))
    hi = max(lo + 1, mid_x - int(w * 0.10))
    a = frame[mid_y - 1, lo:hi].astype(np.float32)
    b = frame[mid_y + 1, lo:hi].astype(np.float32)
    jump = np.mean(np.abs(a - b), axis=1)
    return float(np.mean(jump)), float(np.percentile(jump, 95))


def _assert_frame(frame: np.ndarray, shape: tuple[int, int, int], name: str, min_peak: int = 8) -> None:
    assert frame.shape == shape
    assert np.isfinite(frame).all()
    assert int(frame.max()) > min_peak, f"{name} rendered suspiciously dark"


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
                frame = r.render(t=0.37 + i * 0.11, mode=mode, intensity=1.0, chaos=1.25)
                _assert_frame(frame, (180, 320, 3), mode, 8)
                print(f"[visual-probe]   polar={mode} peak={int(frame.max())} mean={float(frame.mean()):.2f}", flush=True)
        finally:
            r.close()

    def scenes() -> None:
        from projection_mapping.shader_scenes import PALETTE_IDS, SCENE_IDS, SHADER_SCENE_PRESETS, ShaderSceneRenderer

        r = ShaderSceneRenderer(321, 181)
        try:
            for i, scene in enumerate(SCENE_IDS):
                frame = r.render(
                    scene,
                    t=0.43 + i * 0.13,
                    intensity=1.0,
                    chaos=1.25,
                    palette="cyan_magenta",
                    palette_shift=0.07,
                )
                _assert_frame(frame, (181, 321, 3), scene, 8)
                print(f"[visual-probe]   scene={scene} peak={int(frame.max())} mean={float(frame.mean()):.2f}", flush=True)
                if scene == "event_horizon":
                    seam_mean, seam_p95 = _event_horizon_seam_metric(frame)
                    print(f"[visual-probe]   event_horizon seam_mean={seam_mean:.2f} seam_p95={seam_p95:.2f}", flush=True)
                    assert seam_mean < 38.0 and seam_p95 < 96.0, (
                        f"Event Horizon seam regression: mean={seam_mean:.2f}, p95={seam_p95:.2f}"
                    )

            blend = r.render(
                "liquid_chrome",
                t=0.91,
                intensity=1.1,
                chaos=1.35,
                palette="cyan_magenta",
                palette_shift=0.13,
                scene_b="holographic_oil",
                scene_mix=0.42,
            )
            _assert_frame(blend, (181, 321, 3), "liquid_crossfade", 8)
            print(
                f"[visual-probe]   scene-crossfade peak={int(blend.max())} mean={float(blend.mean()):.2f}",
                flush=True,
            )
            for name, preset in SHADER_SCENE_PRESETS.items():
                assert preset.scene in SCENE_IDS and preset.scene_b in SCENE_IDS
                assert preset.palette in PALETTE_IDS
            print(
                f"[visual-probe]   presets={len(SHADER_SCENE_PRESETS)} palettes={len(PALETTE_IDS)}",
                flush=True,
            )
        finally:
            r.close()

    def famous_math() -> None:
        from projection_mapping.famous_math import MATH_MODES, FamousMathRenderer

        r = FamousMathRenderer(240, 135)
        try:
            for i, mode in enumerate(MATH_MODES):
                frame = r.render(t=0.29 + i * 0.17, mode=mode, intensity=1.0, chaos=1.15)
                _assert_frame(frame, (135, 240, 3), mode, 12)
                print(f"[visual-probe]   famous_math={mode} peak={int(frame.max())} mean={float(frame.mean()):.2f}", flush=True)
        finally:
            r.close()

    def wave_optics() -> None:
        from projection_mapping.wave_optics import OPTICS_MODES, WaveOpticsRenderer

        r = WaveOpticsRenderer(240, 135)
        try:
            for i, mode in enumerate(OPTICS_MODES):
                frame = r.render(t=0.41 + i * 0.19, mode=mode, intensity=1.0, chaos=1.1)
                _assert_frame(frame, (135, 240, 3), mode, 10)
                print(f"[visual-probe]   wave_optics={mode} peak={int(frame.max())} mean={float(frame.mean()):.2f}", flush=True)
        finally:
            r.close()

    def hyperbolic() -> None:
        from projection_mapping.hyperbolic_geometry import HYPERBOLIC_MODES, HyperbolicGeometryRenderer

        r = HyperbolicGeometryRenderer(220, 124)
        try:
            for i, mode in enumerate(HYPERBOLIC_MODES):
                frame = r.render(t=0.33 + i * 0.15, mode=mode, intensity=1.0, chaos=1.05)
                _assert_frame(frame, (124, 220, 3), mode, 8)
                print(f"[visual-probe]   hyperbolic={mode} peak={int(frame.max())} mean={float(frame.mean()):.2f}", flush=True)
        finally:
            r.close()

    def geometry_fields() -> None:
        from projection_mapping.geometry_fields import GEOMETRY_MODES, GeometryFieldRenderer

        r = GeometryFieldRenderer(220, 124, site_count=14)
        try:
            for i, mode in enumerate(GEOMETRY_MODES):
                frame = r.render(t=0.27 + i * 0.14, mode=mode, intensity=1.0, chaos=1.1, relax_strength=0.6)
                _assert_frame(frame, (124, 220, 3), mode, 8)
                print(f"[visual-probe]   geometry={mode} peak={int(frame.max())} mean={float(frame.mean()):.2f}", flush=True)
        finally:
            r.close()

    def topology() -> None:
        from projection_mapping.topology_worlds import TOPOLOGY_MODES, TopologyWorldRenderer

        r = TopologyWorldRenderer(192, 108)
        try:
            for i, mode in enumerate(TOPOLOGY_MODES):
                frame = r.render(t=0.31 + i * 0.16, mode=mode, intensity=1.0, chaos=1.0, param_a=0.55, param_b=0.42)
                _assert_frame(frame, (108, 192, 3), mode, 6)
                print(f"[visual-probe]   topology={mode} peak={int(frame.max())} mean={float(frame.mean()):.2f}", flush=True)
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
                    frame = r.render(t=i + step / 30.0, preset=preset, intensity=1.0, drive=0.45, steps=4)
                assert frame is not None
                _assert_frame(frame, (108, 192, 3), preset, 6)
                print(f"[visual-probe]   reaction={preset} peak={int(frame.max())} mean={float(frame.mean()):.2f}", flush=True)
        finally:
            r.close()

    def wave_equation() -> None:
        from projection_mapping.wave_equation import WAVE_MODES, WaveEquationRenderer

        r = WaveEquationRenderer(160, 90, mode="membrane_drop", seed=7)
        try:
            for i, mode in enumerate(WAVE_MODES):
                r.reset(seed=7 + i)
                frame = None
                for step in range(10):
                    frame = r.render(t=i + step / 24.0, mode=mode, intensity=1.0, drive=0.42, steps=2)
                assert frame is not None
                _assert_frame(frame, (90, 160, 3), mode, 4)
                print(f"[visual-probe]   wave_equation={mode} peak={int(frame.max())} mean={float(frame.mean()):.2f}", flush=True)
        finally:
            r.close()

    def cellular() -> None:
        from projection_mapping.cellular_worlds import CELLULAR_MODES, CellularWorldRenderer

        for i, mode in enumerate(CELLULAR_MODES):
            r = CellularWorldRenderer(160, 90, mode=mode, density=0.19, seed=31 + i)
            try:
                frame = None
                for step in range(12):
                    frame = r.render(t=i + step / 30.0, intensity=1.0, drive=0.08, steps=1)
                assert frame is not None
                _assert_frame(frame, (90, 160, 3), mode, 6)
                print(f"[visual-probe]   cellular={mode} peak={int(frame.max())} mean={float(frame.mean()):.2f}", flush=True)
            finally:
                r.close()

    def continuous_ca() -> None:
        from projection_mapping.continuous_ca import CONTINUOUS_CA_MODES, ContinuousCARenderer

        r = ContinuousCARenderer(128, 72, seed=29)
        try:
            for i, mode in enumerate(CONTINUOUS_CA_MODES):
                r.reset(seed=29 + i, density=0.23)
                frame = None
                for step in range(8):
                    frame = r.render(t=i + step / 20.0, mode=mode, intensity=1.0, drive=0.08, steps=1)
                assert frame is not None
                _assert_frame(frame, (72, 128, 3), mode, 3)
                print(f"[visual-probe]   continuous_ca={mode} peak={int(frame.max())} mean={float(frame.mean()):.2f}", flush=True)
        finally:
            r.close()

    def attractors() -> None:
        from projection_mapping.attractor_lab import AttractorRenderer

        for i, mode in enumerate(("lorenz", "clifford", "ikeda")):
            r = AttractorRenderer(192, 108, mode=mode, points=7000)
            try:
                frame = r.render(t=0.31 + i * 0.27, intensity=1.0, zoom=1.35, point_size=2.0, bloom=1.0)
                _assert_frame(frame, (108, 192, 3), mode, 6)
                print(f"[visual-probe]   attractor={mode} peak={int(frame.max())} mean={float(frame.mean()):.2f}", flush=True)
            finally:
                r.close()

    def optimal_transport() -> None:
        from projection_mapping.optimal_transport import TRANSPORT_MODES, OptimalTransportRenderer

        for i, mode in enumerate(TRANSPORT_MODES):
            r = OptimalTransportRenderer(192, 108, mode=mode, points=128, epsilon=0.08)
            try:
                frame = r.render(t=0.7 + i * 0.21, intensity=1.0, point_size=5.0, arc=0.12)
                _assert_frame(frame, (108, 192, 3), mode, 4)
                print(f"[visual-probe]   transport={mode} peak={int(frame.max())} mean={float(frame.mean()):.2f}", flush=True)
            finally:
                r.close()

    def particles() -> None:
        from projection_mapping.gpu_particles import GPUParticleField, ParticleEmitter

        field = GPUParticleField(320, 180, capacity=4096, palette="cyber")
        try:
            field_modes = tuple(field.FIELD_MODES)
            for material_index, material in enumerate(field.MATERIALS):
                field.set_material(material)
                field_mode = field_modes[material_index % len(field_modes)]
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
                        field_mode=field_mode,
                        field_strength=1.2,
                        field_scale=1.35,
                        field_spin=1.0,
                        well_strength=1.1,
                        nebula_mix=1.0,
                    )
                assert frame is not None
                _assert_frame(frame, (180, 320, 3), material, 4)
                print(f"[visual-probe]   particles material={material} field={field_mode} peak={int(frame.max())} mean={float(frame.mean()):.2f}", flush=True)
        finally:
            field.close()

    ok &= _probe("Polar Math all modes @ chaos=1.25", polar)
    ok &= _probe("Shader Scene Lab all modes + seam regression", scenes)
    ok &= _probe("Famous Math all modes", famous_math)
    ok &= _probe("Wave Optics all modes", wave_optics)
    ok &= _probe("Hyperbolic geometry all modes", hyperbolic)
    ok &= _probe("Voronoi/Lloyd/geometric fields", geometry_fields)
    ok &= _probe("Topology/minimal-surface worlds", topology)
    ok &= _probe("Gray-Scott reaction diffusion presets", reaction_diffusion)
    ok &= _probe("Stateful wave equation/cymatics", wave_equation)
    ok &= _probe("GPU cellular automata worlds", cellular)
    ok &= _probe("Continuous CA / Lenia-inspired worlds", continuous_ca)
    ok &= _probe("Classic attractor GPU point clouds", attractors)
    ok &= _probe("Sinkhorn optimal-transport morphs", optimal_transport)
    ok &= _probe("GPU particle materials", particles)
    if not ok:
        raise SystemExit(2)
    print("[visual-probe] PASS", flush=True)


if __name__ == "__main__":
    main()

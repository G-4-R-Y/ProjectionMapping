"""Compile/render smoke test for the high-end visual stack.

This is intentionally a hardware probe rather than a normal CI test: it creates real OpenGL
contexts, compiles every promoted shader family, renders tiny frames, and prints timings/errors.
Use it after graphics-driver or shader changes before debugging the TUI.
"""
from __future__ import annotations

import time
import traceback

import numpy as np


def _probe(name: str, fn) -> bool:
    start=time.perf_counter()
    try:
        fn()
    except Exception as exc:
        print(f"[visual-probe] FAIL {name}: {type(exc).__name__}: {exc}",flush=True)
        traceback.print_exc()
        return False
    print(f"[visual-probe] OK   {name}: {(time.perf_counter()-start)*1000.0:.1f} ms",flush=True)
    return True


def main() -> None:
    from projection_mapping.graphics_runtime import probe_graphics_runtime

    report=probe_graphics_runtime(require=330)
    if not report.available:
        raise SystemExit(f"OpenGL unavailable: {report.error}")
    print(
        f"[visual-probe] GL backend={report.backend} version={report.gl_version} "
        f"vendor={report.vendor} renderer={report.renderer}",
        flush=True,
    )

    ok=True

    def polar():
        from projection_mapping.polar_math import POLAR_MODES, PolarMathRenderer
        r=PolarMathRenderer(320,180)
        try:
            for i,mode in enumerate(POLAR_MODES):
                frame=r.render(t=.37+i*.11,mode=mode,intensity=1.0)
                assert frame.shape==(180,320,3)
                assert np.isfinite(frame).all()
                print(f"[visual-probe]   polar={mode} peak={int(frame.max())} mean={float(frame.mean()):.2f}",flush=True)
        finally:
            r.close()

    def scenes():
        from projection_mapping.shader_scenes import SCENE_IDS, ShaderSceneRenderer
        r=ShaderSceneRenderer(320,180)
        try:
            for i,scene in enumerate(SCENE_IDS):
                frame=r.render(scene,t=.43+i*.13,intensity=1.0)
                assert frame.shape==(180,320,3)
                print(f"[visual-probe]   scene={scene} peak={int(frame.max())} mean={float(frame.mean()):.2f}",flush=True)
        finally:
            r.close()

    def particles():
        from projection_mapping.gpu_particles import GPUParticleField, ParticleEmitter
        field=GPUParticleField(320,180,capacity=4096,palette="cyber")
        try:
            frame=None
            for i in range(10):
                t=i/60.0
                emitters=[
                    ParticleEmitter(.43,.50,.20,-.08,1.0,.78,.018),
                    ParticleEmitter(.57,.50,-.20,.08,1.0,.96,.018),
                ]
                frame=field.render(emitters,t=t,dt=1/60,emission_rate=9000,bloom=1.2,energy=1.2)
            assert frame is not None and frame.shape==(180,320,3)
            print(f"[visual-probe]   particles peak={int(frame.max())} mean={float(frame.mean()):.2f}",flush=True)
        finally:
            field.close()

    ok &= _probe("Polar Math all modes",polar)
    ok &= _probe("Shader Scene Lab all modes",scenes)
    ok &= _probe("GPU particle field",particles)
    if not ok:
        raise SystemExit(2)
    print("[visual-probe] PASS",flush=True)


if __name__=="__main__":
    main()

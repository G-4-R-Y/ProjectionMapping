"""Stateful cellular-automata projector lab.

Conway Life, Brian's Brain, cyclic 8-state automata and Seeds run entirely in ping-pong GPU
textures. F11 toggles fullscreen; ESC exits; R reseeds the selected world.
"""
from __future__ import annotations

import argparse
import time

import cv2

from projection_mapping.cellular_worlds import (
    CELLULAR_MODES,
    CELLULAR_PALETTES,
    CellularWorldRenderer,
)
from projection_mapping.runtime import FullscreenSink


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=CELLULAR_MODES,default="cyclic_8")
    ap.add_argument("--palette",choices=CELLULAR_PALETTES,default="cyan_magenta")
    ap.add_argument("--display",type=int,default=1)
    ap.add_argument("--render-width",type=int,default=512)
    ap.add_argument("--render-height",type=int,default=288)
    ap.add_argument("--projector-width",type=int,default=1920)
    ap.add_argument("--projector-height",type=int,default=1080)
    ap.add_argument("--density",type=float,default=0.18)
    ap.add_argument("--steps",type=int,default=1)
    ap.add_argument("--drive",type=float,default=0.12)
    ap.add_argument("--intensity",type=float,default=1.0)
    ap.add_argument("--seed",type=int,default=17)
    args=ap.parse_args()

    renderer=CellularWorldRenderer(
        args.render_width,args.render_height,
        mode=args.mode,palette=args.palette,density=args.density,seed=args.seed,
    )
    sink=FullscreenSink(
        window=f"ProjectionMapping-Cellular-{args.mode}",display=args.display,fullscreen=True,
    )
    print(
        f"[cellular] mode={args.mode} palette={args.palette} size={args.render_width}x{args.render_height} "
        f"backend={renderer.backend} gl={renderer.context_info.gl_version} "
        f"renderer={renderer.context_info.renderer}",flush=True,
    )
    t0=time.perf_counter()
    report=t0
    frames=0
    seed=args.seed
    try:
        while True:
            now=time.perf_counter()
            rgb=renderer.render(
                t=now-t0,intensity=args.intensity,drive=args.drive,steps=args.steps,
            )
            out=cv2.resize(
                rgb,(args.projector_width,args.projector_height),interpolation=cv2.INTER_NEAREST,
            )
            if sink(cv2.cvtColor(out,cv2.COLOR_RGB2BGR)) is False:
                break
            if sink.last_key in (ord("r"),ord("R")):
                seed+=1
                renderer.reset(seed=seed,density=args.density)
                print(f"[cellular] reseed={seed}",flush=True)
            frames+=1
            if now-report>=2.0:
                print(
                    f"[cellular] fps={frames/(now-report):.1f} mode={args.mode} steps={args.steps} "
                    f"drive={args.drive:.2f} R=reseed F11=fullscreen ESC=exit",flush=True,
                )
                frames=0
                report=now
    finally:
        renderer.close()
        sink.close()
        cv2.destroyAllWindows()


if __name__=="__main__":
    main()

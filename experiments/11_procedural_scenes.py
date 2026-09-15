"""Immediate-run procedural visuals distilled from the Visual Madness playbook.

These scenes intentionally require no camera, model download, or CUDA so they are useful
for projector bring-up and artistic iteration right now. F11 toggles fullscreen; ESC exits.
"""
from __future__ import annotations

import argparse
import math
import time

import cv2
import numpy as np

from projection_mapping.runtime import FullscreenSink


def _coords(width: int, height: int):
    y, x = np.mgrid[0:height, 0:width].astype(np.float32)
    aspect = width / max(height, 1)
    nx = (x / max(width - 1, 1) - 0.5) * 2.0 * aspect
    ny = (y / max(height - 1, 1) - 0.5) * 2.0
    return nx, ny


def _palette(v: np.ndarray, phase: float = 0.0) -> np.ndarray:
    r = 0.5 + 0.5 * np.sin(v * 2.7 + phase)
    g = 0.5 + 0.5 * np.sin(v * 2.9 + phase + 2.15)
    b = 0.5 + 0.5 * np.sin(v * 3.1 + phase + 4.25)
    return np.dstack([r, g, b])


def portal_architecture(nx, ny, t: float, intensity: float) -> np.ndarray:
    r = np.sqrt(nx * nx + ny * ny) + 1e-4
    a = np.arctan2(ny, nx)
    z = 1.0 / r
    # Angular harmonics MUST be integer-valued. The previous non-integer frequency
    # multiplied by atan2 created a visible branch-cut line at -pi/pi.
    spoke_count = 8 + int(round(6.0 * np.clip(intensity, 0.0, 2.0)))
    tunnel = np.sin(19.0 * z - t * (4.0 + intensity * 4.0) + np.sin(a * 6.0) * 1.2)
    ribs = np.cos(a * float(spoke_count) + z * 3.0)
    secondary = np.sin(a * float(max(3, spoke_count // 2)) - z * 1.7 + t * 0.35)
    horizon = np.exp(-np.abs(ny + 0.15) * (7.0 + 5.0 * intensity))
    core = np.exp(-r * (4.0 - intensity * 1.4))
    v = tunnel * 0.68 + ribs * 0.29 + secondary * 0.16 + horizon * 1.35 + core * 2.0
    rgb = _palette(v, t * 0.18)
    rgb *= np.clip(0.12 + 0.92 * core[..., None] + 0.55 * horizon[..., None], 0.0, 1.55)
    return np.clip(rgb, 0.0, 1.0)


def bioluminescent_infestation(nx, ny, t: float, intensity: float) -> np.ndarray:
    warp_x = nx + 0.18 * np.sin(ny * 7.0 + t * 0.9) + 0.08 * np.sin(ny * 19.0 - t * 1.7)
    warp_y = ny + 0.15 * np.sin(nx * 6.0 - t * 0.7)
    vein1 = np.abs(np.sin(warp_x * (8.0 + 8.0 * intensity) + np.sin(warp_y * 5.0 + t)))
    vein2 = np.abs(np.sin((warp_x + warp_y) * 10.0 - t * 1.3))
    veins = np.exp(-18.0 * np.minimum(vein1, vein2))
    membranes = 0.5 + 0.5 * np.sin(warp_x * 3.2 + np.sin(warp_y * 4.7 - t * 0.35) * 2.2)
    spores = np.power(np.clip(np.sin(nx * 41.0 + ny * 37.0 + t * 2.3), 0.0, 1.0), 18.0)
    glow = np.clip(veins * (1.2 + intensity) + spores * intensity * 1.5, 0.0, 1.8)
    return np.clip(np.dstack([0.12 + glow * 0.95, 0.04 + membranes * 0.22 + glow * 0.12, 0.18 + (1.0 - membranes) * 0.35 + glow * 0.85]), 0.0, 1.0)


def liquid_cathedral(nx, ny, t: float, intensity: float) -> np.ndarray:
    floor = ny + 0.36
    columns = np.cos(nx * math.pi * 3.5) ** 18
    arches_r = np.sqrt((np.mod(nx + 0.65, 1.3) - 0.65) ** 2 + (ny + 0.15) ** 2)
    arches = np.exp(-45.0 * np.abs(arches_r - (0.48 + 0.04 * np.sin(t * 0.5))))
    caustic_a = np.sin(nx * 13.0 + np.sin(ny * 7.0 + t * 0.8) * 2.3)
    caustic_b = np.sin(ny * 17.0 + np.sin(nx * 5.0 - t * 0.6) * 2.6)
    caustics = np.power(np.clip(0.5 + 0.5 * (caustic_a * caustic_b), 0.0, 1.0), 4.0)
    reflection = np.exp(-np.abs(floor) * 4.0) * (0.5 + 0.5 * np.sin(nx * 10.0 + t))
    structure = np.clip(columns * 0.9 + arches * 1.4, 0.0, 1.0)
    v = caustics * (0.8 + intensity * 1.6) + structure * 1.2 + reflection * 0.8
    return np.clip(np.dstack([0.03 + v * 0.16, 0.08 + v * 0.55, 0.12 + v * 0.95]), 0.0, 1.0)


def mechanical_possession(nx, ny, t: float, intensity: float) -> np.ndarray:
    r = np.sqrt(nx * nx + ny * ny)
    a = np.arctan2(ny, nx)
    teeth = 0.5 + 0.5 * np.sign(np.sin(a * 18.0 + t * (1.0 + intensity * 2.5)))
    gear = np.exp(-50.0 * np.abs(r - (0.48 + teeth * 0.055)))
    inner = np.exp(-70.0 * np.abs(r - 0.28))
    shafts = np.exp(-32.0 * np.abs(np.sin(nx * 7.0 + t * 0.7))) * np.exp(-ny * ny * 1.8)
    grid = np.power(0.5 + 0.5 * np.sin(nx * 17.0 + t) * np.sin(ny * 13.0 - t * 0.7), 5.0)
    sparks = np.power(np.clip(np.sin(nx * 53.0 + ny * 47.0 + t * 5.0), 0.0, 1.0), 22.0) * intensity
    metal = np.clip(gear * 1.4 + inner + shafts * 0.8 + grid * 0.35, 0.0, 1.4)
    return np.clip(np.dstack([0.05 + metal * 0.72 + sparks, 0.07 + metal * 0.25 + sparks * 0.22, 0.10 + metal * 0.08]), 0.0, 1.0)


def ancient_ruin_moss(nx, ny, t: float, intensity: float) -> np.ndarray:
    cracks = np.minimum(
        np.abs(np.sin(nx * 8.5 + np.sin(ny * 5.0) * 1.7)),
        np.abs(np.sin(ny * 10.0 + np.sin(nx * 3.7) * 1.4)),
    )
    crack_glow = np.exp(-24.0 * cracks)
    stone = 0.45 + 0.18 * np.sin(nx * 2.7 + ny * 3.1) + 0.12 * np.sin(nx * 7.0 - ny * 4.0)
    moss_noise = 0.5 + 0.5 * np.sin(nx * 5.0 + np.sin(ny * 6.0 + t * 0.08) * 2.0)
    moss = np.clip((moss_noise - 0.42) * 2.4, 0.0, 1.0) * np.clip(0.7 - ny * 0.25, 0.0, 1.0)
    roots = np.exp(-15.0 * np.abs(np.sin(nx * 4.0 + np.sin(ny * 5.0 + t * 0.12) * 2.5))) * (0.35 + 0.65 * intensity)
    dust = np.power(np.clip(np.sin(nx * 29.0 + ny * 31.0 + t * 0.18), 0.0, 1.0), 18.0) * 0.18
    return np.clip(np.dstack([
        0.12 + stone * 0.32 + crack_glow * 0.16,
        0.10 + stone * 0.26 + moss * (0.35 + 0.25 * intensity) + roots * 0.22,
        0.07 + stone * 0.18 + moss * 0.08 + dust,
    ]), 0.0, 1.0)


def ceiling_starfield(nx, ny, t: float, intensity: float) -> np.ndarray:
    r = np.sqrt(nx * nx + ny * ny) + 1e-4
    a = np.arctan2(ny, nx)
    warp = a * 9.0 + np.log(r) * 13.0 - t * (0.25 + intensity * 0.9)
    dust = 0.5 + 0.5 * np.sin(warp + np.sin(a * 5.0 + t * 0.11) * 2.2)
    nebula = np.power(np.clip(dust, 0.0, 1.0), 3.5)
    stars_a = np.power(np.clip(np.sin(nx * 43.0 + ny * 59.0), 0.0, 1.0), 28.0)
    stars_b = np.power(np.clip(np.sin(nx * 97.0 - ny * 71.0 + 1.7), 0.0, 1.0), 42.0)
    twinkle = 0.55 + 0.45 * np.sin(t * 2.0 + nx * 12.0 + ny * 8.0)
    stars = np.clip(stars_a + stars_b * twinkle, 0.0, 1.0)
    vortex = np.exp(-r * (1.5 + 1.0 * intensity))
    return np.clip(np.dstack([
        0.01 + nebula * 0.18 + stars * 0.95,
        0.015 + nebula * 0.10 + stars * 0.82,
        0.035 + nebula * 0.42 + stars + vortex * 0.12,
    ]), 0.0, 1.0)


SCENES = {
    "portal": portal_architecture,
    "infestation": bioluminescent_infestation,
    "cathedral": liquid_cathedral,
    "mechanical": mechanical_possession,
    "moss_ruin": ancient_ruin_moss,
    "starfield": ceiling_starfield,
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", choices=SCENES, default="portal")
    ap.add_argument("--display", type=int, default=1)
    ap.add_argument("--projector-width", type=int, default=1920)
    ap.add_argument("--projector-height", type=int, default=1080)
    ap.add_argument("--render-width", type=int, default=640)
    ap.add_argument("--render-height", type=int, default=360)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--intensity", type=float, default=0.75)
    args = ap.parse_args()

    nx, ny = _coords(args.render_width, args.render_height)
    render = SCENES[args.scene]
    sink = FullscreenSink(window=f"ProjectionMapping-{args.scene}", display=args.display)
    t0 = time.perf_counter()
    frames = 0
    report_t = t0
    try:
        while True:
            now = time.perf_counter()
            t = (now - t0) * args.speed
            rgb = render(nx, ny, t, float(np.clip(args.intensity, 0.0, 2.0)))
            small = (np.clip(rgb, 0.0, 1.0) * 255.0).astype(np.uint8)
            frame = cv2.resize(small, (args.projector_width, args.projector_height), interpolation=cv2.INTER_LINEAR)
            if sink(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)) is False:
                break
            frames += 1
            if now - report_t >= 2.0:
                print(f"scene={args.scene} fps={frames / (now - report_t):.1f} F11=fullscreen ESC=exit", flush=True)
                frames = 0
                report_t = now
    finally:
        sink.close()


if __name__ == "__main__":
    main()

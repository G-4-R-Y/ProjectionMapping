"""Capture projector emission -> camera observation pairs for appearance compensation.

The script sweeps grayscale and per-channel intensities plus reproducible random RGB
patch fields. Lock camera exposure/white-balance manually before collecting data.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import cv2
import numpy as np

from projection_mapping.capture import Camera


def patch_field(width: int, height: int, rng: np.random.Generator, grid: int = 12) -> np.ndarray:
    gh = max(1, height // grid)
    gw = max(1, width // grid)
    small = rng.integers(0, 256, size=(grid, grid, 3), dtype=np.uint8)
    return cv2.resize(small, (width, height), interpolation=cv2.INTER_NEAREST)


def show_and_capture(win: str, image: np.ndarray, cam: Camera, settle_ms: int) -> np.ndarray:
    cv2.imshow(win, image)
    cv2.waitKey(1)
    time.sleep(settle_ms / 1000.0)
    return cam.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--projector-width", type=int, default=1920)
    ap.add_argument("--projector-height", type=int, default=1080)
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--display", type=int, default=1)
    ap.add_argument("--levels", type=int, default=17)
    ap.add_argument("--random-fields", type=int, default=64)
    ap.add_argument("--settle-ms", type=int, default=140)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--output", default="calibration_data/radiometry")
    args = ap.parse_args()

    out = Path(args.output)
    emitted_dir = out / "emitted"
    observed_dir = out / "observed"
    emitted_dir.mkdir(parents=True, exist_ok=True)
    observed_dir.mkdir(parents=True, exist_ok=True)

    win = "ProjectionMapping-Radiometry"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(win, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    if args.display > 0:
        cv2.moveWindow(win, args.display * args.projector_width, 0)

    patterns: list[tuple[str, np.ndarray]] = []
    levels = np.linspace(0, 255, args.levels).astype(np.uint8)
    for value in levels:
        rgb = np.full((args.projector_height, args.projector_width, 3), value, np.uint8)
        patterns.append((f"gray_{int(value):03d}", rgb))
    for channel, name in enumerate(["r", "g", "b"]):
        for value in levels:
            rgb = np.zeros((args.projector_height, args.projector_width, 3), np.uint8)
            rgb[..., channel] = value
            patterns.append((f"{name}_{int(value):03d}", rgb))

    rng = np.random.default_rng(args.seed)
    for i in range(args.random_fields):
        patterns.append((f"random_{i:04d}", patch_field(args.projector_width, args.projector_height, rng)))

    manifest = []
    with Camera(args.camera) as cam:
        for i, (name, emitted_rgb) in enumerate(patterns):
            # OpenCV fullscreen expects BGR, but stored emitted arrays are canonical RGB.
            observed_bgr = show_and_capture(win, cv2.cvtColor(emitted_rgb, cv2.COLOR_RGB2BGR), cam, args.settle_ms)
            observed_rgb = cv2.cvtColor(observed_bgr, cv2.COLOR_BGR2RGB)
            emitted_path = emitted_dir / f"{i:04d}_{name}.png"
            observed_path = observed_dir / f"{i:04d}_{name}.png"
            cv2.imwrite(str(emitted_path), cv2.cvtColor(emitted_rgb, cv2.COLOR_RGB2BGR))
            cv2.imwrite(str(observed_path), cv2.cvtColor(observed_rgb, cv2.COLOR_RGB2BGR))
            manifest.append({
                "index": i,
                "name": name,
                "emitted": str(emitted_path.relative_to(out)),
                "observed": str(observed_path.relative_to(out)),
                "timestamp_ns": time.time_ns(),
            })
            print(f"[{i + 1}/{len(patterns)}] {name}")

    (out / "manifest.json").write_text(json.dumps({
        "projector": [args.projector_width, args.projector_height],
        "camera_device": args.camera,
        "levels": int(args.levels),
        "random_fields": int(args.random_fields),
        "settle_ms": int(args.settle_ms),
        "seed": int(args.seed),
        "frames": manifest,
    }, indent=2), encoding="utf-8")
    cv2.destroyAllWindows()
    print(f"saved dataset to {out.resolve()}")


if __name__ == "__main__":
    main()

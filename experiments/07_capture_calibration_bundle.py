"""Capture a reusable projector-camera calibration bundle.

Projects white/black references plus Gray-code and phase-shift sequences, captures the
camera after a configurable settle interval, and writes metadata required for later
dense correspondence/radiometric processing.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import cv2
import numpy as np

from projection_mapping.capture import Camera
from projection_mapping.patterns import graycode_sequence, phase_shift_sequence, PatternFrame
from projection_mapping.calibration_bundle import CalibrationBundle, save_capture_manifest


def constant_frame(width: int, height: int, value: int, name: str) -> PatternFrame:
    img = np.full((height, width, 3), value, dtype=np.uint8)
    return PatternFrame(img, name, {"value": value})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--projector-width", type=int, default=1920)
    ap.add_argument("--projector-height", type=int, default=1080)
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--display", type=int, default=1)
    ap.add_argument("--settle-ms", type=int, default=180)
    ap.add_argument("--phase-periods", type=int, default=16)
    ap.add_argument("--output", default="calibration_data/session")
    args = ap.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    projector_frames = [
        constant_frame(args.projector_width, args.projector_height, 0, "black"),
        constant_frame(args.projector_width, args.projector_height, 255, "white"),
        *graycode_sequence(args.projector_width, args.projector_height, include_inverse=True),
        *phase_shift_sequence(args.projector_width, args.projector_height, periods=args.phase_periods),
    ]

    win = "ProjectionMapping-Calibration"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(win, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    if args.display > 0:
        cv2.moveWindow(win, args.display * args.projector_width, 0)

    records: list[dict] = []
    with Camera(args.camera) as cam:
        first = cam.read()
        ch, cw = first.shape[:2]
        for i, pat in enumerate(projector_frames):
            cv2.imshow(win, pat.image)
            cv2.waitKey(1)
            time.sleep(args.settle_ms / 1000.0)
            captured = cam.read()
            ts_ns = time.time_ns()
            filename = f"{i:04d}_{pat.name}.png"
            cv2.imwrite(str(out / filename), captured)
            records.append({
                "index": i,
                "file": filename,
                "name": pat.name,
                "timestamp_ns": ts_ns,
                "metadata": pat.metadata,
            })
            print(f"[{i + 1}/{len(projector_frames)}] {filename}")

    bundle = CalibrationBundle(
        projector_width=args.projector_width,
        projector_height=args.projector_height,
        camera_width=cw,
        camera_height=ch,
        notes="Raw structured-light capture; dense decoding not yet applied.",
    )
    bundle.save(out)
    save_capture_manifest(out, {
        "projector": [args.projector_width, args.projector_height],
        "camera": [cw, ch],
        "settle_ms": args.settle_ms,
        "phase_periods": args.phase_periods,
        "camera_device": args.camera,
        "display": args.display,
    }, records)
    cv2.destroyAllWindows()
    print(json.dumps({"output": str(out.resolve()), "frames": len(records)}, indent=2))


if __name__ == "__main__":
    main()

"""Exercise the Spout sender with an animated diagnostic frame.

Use a TouchDesigner Syphon Spout In TOP named ``ProjectionMapping-Diagnostic``.
The visual encodes frame number and motion so dropped/repeated frames are obvious.
"""
from __future__ import annotations

import argparse
import time
import numpy as np

from projection_mapping.transport import SpoutSender


def frame_pattern(width: int, height: int, n: int) -> np.ndarray:
    y, x = np.mgrid[0:height, 0:width]
    phase = n * 0.08
    image = np.zeros((height, width, 3), dtype=np.uint8)
    image[..., 0] = ((x + n * 7) % 256).astype(np.uint8)
    image[..., 1] = ((y + n * 5) % 256).astype(np.uint8)
    image[..., 2] = (127.5 + 127.5 * np.sin((x + y) / 43.0 + phase)).astype(np.uint8)

    # high-contrast moving timing bar
    bar_x = (n * 13) % width
    image[:, max(0, bar_x - 3):min(width, bar_x + 4)] = 255
    return image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sender", default="ProjectionMapping-Diagnostic")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--fps", type=float, default=60.0)
    ap.add_argument("--seconds", type=float, default=30.0)
    args = ap.parse_args()

    sender = SpoutSender(args.sender)
    period = 1.0 / args.fps
    deadline = time.perf_counter()
    end = deadline + args.seconds
    frames = 0
    overruns = 0

    while time.perf_counter() < end:
        sender(frame_pattern(args.width, args.height, frames))
        frames += 1
        deadline += period
        sleep_s = deadline - time.perf_counter()
        if sleep_s > 0:
            time.sleep(sleep_s)
        else:
            overruns += 1
            deadline = time.perf_counter()

    elapsed = args.seconds
    print(f"sent={frames} avg_fps={frames / elapsed:.2f} schedule_overruns={overruns}")
    print("In TouchDesigner verify: stable sender discovery, no visible tearing, no growing delay, and expected frame motion.")


if __name__ == "__main__":
    main()

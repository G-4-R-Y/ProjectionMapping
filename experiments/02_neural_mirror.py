"""Realtime neural-mirror skeleton.

Starts with a temporally stable CV effect so the entire physical pipeline can be tested
before dropping in StreamDiffusion. Replace `stylize` with a StreamDiffusionGenerator.
"""
from __future__ import annotations
import argparse
import cv2, numpy as np
from projection_mapping.capture import Camera
from projection_mapping.perception import BackgroundMask
from projection_mapping.generation import blend_with_mask
from projection_mapping.runtime import FullscreenSink, run_loop


def stylize(bgr: np.ndarray) -> np.ndarray:
    # GPU diffusion can replace this function without touching capture/compositing/output.
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    smooth = cv2.bilateralFilter(rgb, 9, 80, 80)
    edges = cv2.Canny(bgr, 70, 140)
    glow = cv2.applyColorMap(255 - edges, cv2.COLORMAP_TURBO)
    return cv2.addWeighted(cv2.cvtColor(smooth, cv2.COLOR_RGB2BGR), 0.65, glow, 0.35, 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--camera', type=int, default=0)
    ap.add_argument('--display', type=int, default=1)
    args = ap.parse_args()
    cam = Camera(args.camera)
    mask_model = BackgroundMask()
    sink = FullscreenSink(display=args.display)

    def source(): return cam.read()
    def process(frame):
        mask = mask_model(frame)
        generated = stylize(frame)
        return blend_with_mask(frame, generated, mask)

    try:
        stats = run_loop(source, sink, processors=[process])
        print(stats)
    finally:
        cam.close(); sink.close()


if __name__ == '__main__':
    main()

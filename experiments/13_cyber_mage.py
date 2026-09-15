"""Cyber Mage: performer-anchored realtime spell FX.

Classical realtime baseline first: foreground segmentation -> persistent performer rig ->
body-owned sigils/arcs/trails/auras. Neural generation is intentionally not required for
spatial stability; a later neural style skin can decorate this renderer at lower FPS.

F11 toggles fullscreen; ESC exits.
"""
from __future__ import annotations

import argparse
import time

import cv2
import numpy as np

from projection_mapping.capture import Camera
from projection_mapping.cyber_mage_fx import CyberMageRenderer, PALETTES
from projection_mapping.perception import BackgroundMask, optical_flow
from projection_mapping.performer_rig import PerformerRig
from projection_mapping.runtime import FullscreenSink


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--display", type=int, default=1)
    ap.add_argument("--projector-width", type=int, default=1920)
    ap.add_argument("--projector-height", type=int, default=1080)
    ap.add_argument("--capture-width", type=int, default=640)
    ap.add_argument("--capture-height", type=int, default=360)
    ap.add_argument("--palette", choices=sorted(PALETTES), default="arcane")
    ap.add_argument("--intensity", type=float, default=1.0)
    ap.add_argument("--complexity", type=float, default=0.78)
    ap.add_argument("--trail-length", type=int, default=30)
    ap.add_argument("--feedback", type=float, default=0.90)
    ap.add_argument("--rig-smoothing", type=float, default=0.72)
    ap.add_argument("--mirror", action="store_true")
    ap.add_argument("--camera-mix", type=float, default=0.08)
    args = ap.parse_args()

    sink = FullscreenSink(window="ProjectionMapping-CyberMage", display=args.display)
    bg = BackgroundMask(history=240, threshold=19.0)
    rig = PerformerRig(smoothing=args.rig_smoothing)
    renderer = CyberMageRenderer(
        args.capture_width,
        args.capture_height,
        palette=args.palette,
        complexity=args.complexity,
        trail_length=args.trail_length,
        feedback=args.feedback,
    )

    previous = None
    t0 = time.perf_counter()
    report_t = t0
    frames = 0
    try:
        with Camera(args.camera, args.capture_width, args.capture_height) as cam:
            while True:
                now = time.perf_counter()
                frame = cam.read()
                frame = cv2.resize(frame, (args.capture_width, args.capture_height), interpolation=cv2.INTER_AREA)
                if args.mirror:
                    frame = cv2.flip(frame, 1)

                mask = bg(frame)
                mask = cv2.medianBlur(mask, 7)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))

                if previous is None:
                    flow_mag = np.zeros(mask.shape, dtype=np.float32)
                else:
                    flow = optical_flow(previous, frame)
                    flow_mag = np.sqrt(flow[..., 0] ** 2 + flow[..., 1] ** 2)
                previous = frame.copy()

                state = rig.update(mask, flow_mag)
                fx = renderer.render(mask, state, now - t0, args.intensity)

                camera_mix = float(np.clip(args.camera_mix, 0.0, 1.0))
                if camera_mix > 0.0:
                    camera_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    out_rgb = cv2.addWeighted(fx, 1.0, camera_rgb, camera_mix, 0)
                else:
                    out_rgb = fx

                out = cv2.resize(out_rgb, (args.projector_width, args.projector_height), interpolation=cv2.INTER_LINEAR)
                if sink(cv2.cvtColor(out, cv2.COLOR_RGB2BGR)) is False:
                    break

                frames += 1
                if now - report_t >= 2.0:
                    g = state.gestures
                    print(
                        f"fps={frames / (now - report_t):.1f} visible={state.visible} "
                        f"occupancy={state.occupancy:.3f} motion={g.motion_energy:.3f} "
                        f"spread={g.arms_spread} together={g.hands_together} raised={g.hands_raised} "
                        "F11=fullscreen ESC=exit",
                        flush=True,
                    )
                    frames = 0
                    report_t = now
    finally:
        sink.close()


if __name__ == "__main__":
    main()

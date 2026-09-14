"""Live camera -> async StreamDiffusion -> projector/Spout experiment.

The camera/display loop runs independently from diffusion inference. New camera frames replace
any stale pending inference request so latency stays bounded instead of building a queue.

Example:
    python experiments/04_streamdiffusion_live.py --display 1 --acceleration xformers

For Spout output:
    python experiments/04_streamdiffusion_live.py --spout --sender ProjectionMapping
"""

from __future__ import annotations

import argparse
import time

import cv2
import numpy as np

from projection_mapping.async_runtime import LatestFrameWorker
from projection_mapping.streamdiffusion_backend import DaydreamStreamConfig, DaydreamStreamDiffusion
from projection_mapping.transport import SpoutSender


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--camera", type=int, default=0)
    p.add_argument("--display", type=int, default=1)
    p.add_argument("--width", type=int, default=768)
    p.add_argument("--height", type=int, default=432)
    p.add_argument("--model", default="stabilityai/sd-turbo")
    p.add_argument("--prompt", default="bioluminescent living architecture, immersive projection art")
    p.add_argument("--negative-prompt", default="blurry, low quality, low resolution, text, watermark")
    p.add_argument("--acceleration", choices=["none", "xformers", "tensorrt"], default="xformers")
    p.add_argument("--spout", action="store_true")
    p.add_argument("--sender", default="ProjectionMapping")
    p.add_argument("--submit-fps", type=float, default=0.0, help="0 = submit every camera frame")
    p.add_argument("--show-input", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    config = DaydreamStreamConfig(
        model_id_or_path=args.model,
        prompt=args.prompt,
        negative_prompt=args.negative_prompt,
        width=args.width,
        height=args.height,
        acceleration=args.acceleration,
        guidance_scale=1.0,
        cfg_type="none",
        t_index_list=[32, 45],
    )
    generator = DaydreamStreamDiffusion(config)

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise RuntimeError(f"could not open camera {args.camera}")

    sender = SpoutSender(args.sender) if args.spout else None
    window = "ProjectionMapping — async StreamDiffusion"
    if sender is None:
        cv2.namedWindow(window, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(window, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        if args.display > 0:
            cv2.moveWindow(window, args.display * 1920, 0)

    last_submit = 0.0
    last_seq_seen = 0
    submitted_frame_rgb: np.ndarray | None = None
    display_rgb = np.zeros((args.height, args.width, 3), dtype=np.uint8)
    display_frames = 0
    report_t0 = time.perf_counter()

    try:
        with LatestFrameWorker(generator, name="streamdiffusion") as worker:
            while True:
                ok, camera_bgr = cap.read()
                if not ok:
                    raise RuntimeError("camera read failed")

                camera_rgb = cv2.cvtColor(camera_bgr, cv2.COLOR_BGR2RGB)
                camera_rgb = cv2.resize(camera_rgb, (args.width, args.height), interpolation=cv2.INTER_AREA)

                now = time.perf_counter()
                submit_interval = 1.0 / args.submit_fps if args.submit_fps > 0 else 0.0
                if now - last_submit >= submit_interval:
                    submitted_frame_rgb = camera_rgb.copy()
                    worker.submit(submitted_frame_rgb)
                    last_submit = now

                latest = worker.latest()
                if latest is not None and latest[0] != last_seq_seen:
                    last_seq_seen, generated, _completed = latest
                    display_rgb = np.asarray(generated, dtype=np.uint8)

                if args.show_input and submitted_frame_rgb is not None:
                    inset_w = max(args.width // 4, 1)
                    inset_h = max(args.height // 4, 1)
                    inset = cv2.resize(submitted_frame_rgb, (inset_w, inset_h))
                    display_rgb[:inset_h, :inset_w] = inset

                if sender is not None:
                    sender(display_rgb)
                    # Keep a tiny control window so ESC still works without owning projector output.
                    cv2.imshow("ProjectionMapping controls", cv2.cvtColor(display_rgb, cv2.COLOR_RGB2BGR))
                else:
                    cv2.imshow(window, cv2.cvtColor(display_rgb, cv2.COLOR_RGB2BGR))

                display_frames += 1
                elapsed = now - report_t0
                if elapsed >= 2.0:
                    display_fps = display_frames / elapsed
                    s = worker.stats
                    print(
                        f"display={display_fps:5.1f} fps | inference={s.inference_fps:5.1f} fps "
                        f"({s.last_inference_ms:6.1f} ms last, {s.ema_inference_ms:6.1f} ms EMA) | "
                        f"submitted={s.submitted} processed={s.processed} dropped={s.dropped} errors={s.errors}"
                    )
                    display_frames = 0
                    report_t0 = now

                error = worker.last_error()
                if error is not None:
                    raise RuntimeError("async inference failed") from error

                if (cv2.waitKey(1) & 0xFF) == 27:
                    break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

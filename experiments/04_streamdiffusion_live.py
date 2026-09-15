"""Live camera -> async StreamDiffusion -> projector/Spout.

Profiles keep the RTX 4050 6 GB path conservative while preserving larger modes for stronger GPUs.
F11 toggles fullscreen on the direct projector path; ESC exits.
"""
from __future__ import annotations

import argparse
import time

import cv2
import numpy as np

from projection_mapping.async_runtime import LatestFrameWorker
from projection_mapping.capture import Camera
from projection_mapping.runtime import FullscreenSink
from projection_mapping.streamdiffusion_backend import DaydreamStreamConfig, DaydreamStreamDiffusion
from projection_mapping.transport import SpoutSender


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--camera", type=int, default=0)
    p.add_argument("--display", type=int, default=1)
    p.add_argument("--profile", choices=["auto", "safe", "balanced", "quality", "custom"], default="auto")
    p.add_argument("--width", type=int, default=768)
    p.add_argument("--height", type=int, default=432)
    p.add_argument("--output-width", type=int, default=1920)
    p.add_argument("--output-height", type=int, default=1080)
    p.add_argument("--model", default="stabilityai/sd-turbo")
    p.add_argument("--prompt", default="bioluminescent living architecture, cyber ritual portrait, immersive projection art")
    p.add_argument("--negative-prompt", default="blurry, low quality, low resolution, text, watermark")
    p.add_argument("--acceleration", choices=["auto", "none", "xformers", "tensorrt"], default="auto")
    p.add_argument("--spout", action="store_true")
    p.add_argument("--sender", default="ProjectionMapping")
    p.add_argument("--submit-fps", type=float, default=0.0, help="0 = profile default")
    p.add_argument("--show-input", action="store_true")
    return p.parse_args()


def select_profile(args: argparse.Namespace) -> tuple[int, int, float, str]:
    profile = args.profile
    if profile == "auto":
        try:
            import torch
            total_gib = torch.cuda.get_device_properties(0).total_memory / 1024**3
        except Exception:
            total_gib = 0.0
        profile = "safe" if total_gib and total_gib < 8.0 else "balanced"
    presets = {
        "safe": (512, 288, 6.0),
        "balanced": (640, 360, 8.0),
        "quality": (768, 432, 8.0),
        "custom": (args.width, args.height, args.submit_fps if args.submit_fps > 0 else 0.0),
    }
    width, height, fps = presets[profile]
    if args.submit_fps > 0:
        fps = args.submit_fps
    return width, height, fps, profile


def main() -> None:
    args = parse_args()
    width, height, submit_fps, profile = select_profile(args)
    print(
        f"[neural] profile={profile} inference={width}x{height} output={args.output_width}x{args.output_height} "
        f"submit_fps={submit_fps or 'camera-rate'}",
        flush=True,
    )
    config = DaydreamStreamConfig(
        model_id_or_path=args.model,
        prompt=args.prompt,
        negative_prompt=args.negative_prompt,
        width=width,
        height=height,
        acceleration=args.acceleration,
        guidance_scale=1.0,
        cfg_type="none",
        t_index_list=[32, 45],
        warmup=6 if profile == "safe" else 10,
    )

    sender = SpoutSender(args.sender) if args.spout else None
    sink = None if sender is not None else FullscreenSink(
        window="ProjectionMapping-NeuralMirror",
        display=args.display,
        fullscreen=True,
    )
    generator = None
    last_submit = 0.0
    last_seq_seen = 0
    submitted_frame_rgb: np.ndarray | None = None
    display_rgb = np.zeros((height, width, 3), dtype=np.uint8)
    display_frames = 0
    report_t0 = time.perf_counter()

    try:
        print("[neural] stage=initializing-generator", flush=True)
        generator = DaydreamStreamDiffusion(config)
        print("[neural] stage=opening-camera", flush=True)
        with Camera(args.camera, width, height) as cam:
            with LatestFrameWorker(generator, name="streamdiffusion") as worker:
                print("[neural] stage=running", flush=True)
                while True:
                    camera_bgr = cam.read()
                    camera_rgb = cv2.cvtColor(camera_bgr, cv2.COLOR_BGR2RGB)
                    camera_rgb = cv2.resize(camera_rgb, (width, height), interpolation=cv2.INTER_AREA)
                    now = time.perf_counter()
                    submit_interval = 1.0 / submit_fps if submit_fps > 0 else 0.0
                    if now - last_submit >= submit_interval:
                        submitted_frame_rgb = camera_rgb.copy()
                        worker.submit(submitted_frame_rgb)
                        last_submit = now

                    latest = worker.latest()
                    if latest is not None and latest[0] != last_seq_seen:
                        last_seq_seen, generated, _completed = latest
                        display_rgb = np.asarray(generated, dtype=np.uint8)

                    composed = display_rgb.copy()
                    if args.show_input and submitted_frame_rgb is not None:
                        inset_w, inset_h = max(width // 4, 1), max(height // 4, 1)
                        composed[:inset_h, :inset_w] = cv2.resize(submitted_frame_rgb, (inset_w, inset_h))

                    output = cv2.resize(composed, (args.output_width, args.output_height), interpolation=cv2.INTER_CUBIC)
                    if sender is not None:
                        sender(output)
                        cv2.imshow("ProjectionMapping controls", cv2.cvtColor(composed, cv2.COLOR_RGB2BGR))
                        if (cv2.waitKey(1) & 0xFF) == 27:
                            break
                    else:
                        if sink(cv2.cvtColor(output, cv2.COLOR_RGB2BGR)) is False:
                            break

                    display_frames += 1
                    elapsed = now - report_t0
                    if elapsed >= 2.0:
                        s = worker.stats
                        print(
                            f"[neural] profile={profile} acceleration={generator.acceleration} "
                            f"display={display_frames / elapsed:5.1f}fps inference={s.inference_fps:5.1f}fps "
                            f"last={s.last_inference_ms:6.1f}ms ema={s.ema_inference_ms:6.1f}ms "
                            f"submitted={s.submitted} processed={s.processed} dropped={s.dropped} errors={s.errors}",
                            flush=True,
                        )
                        display_frames = 0
                        report_t0 = now
                    error = worker.last_error()
                    if error is not None:
                        raise RuntimeError("async inference failed") from error
    finally:
        if generator is not None:
            generator.close()
        if sink is not None:
            sink.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

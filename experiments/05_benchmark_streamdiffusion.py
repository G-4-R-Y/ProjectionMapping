"""Benchmark StreamDiffusion configurations on the local GPU.

This script deliberately separates inference latency from display latency. It writes a
JSON report that can be compared across model/resolution/acceleration choices.
"""
from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

import numpy as np

from projection_mapping.benchmark import BenchmarkReport


def make_test_frame(width: int, height: int, t: float) -> np.ndarray:
    y, x = np.mgrid[0:height, 0:width]
    r = (127.5 + 127.5 * np.sin(x / 37.0 + t)).astype(np.uint8)
    g = (127.5 + 127.5 * np.sin(y / 31.0 - t * 0.7)).astype(np.uint8)
    b = (127.5 + 127.5 * np.sin((x + y) / 53.0 + t * 1.3)).astype(np.uint8)
    return np.dstack([r, g, b])


def build_stream(args):
    try:
        import torch
        from streamdiffusion import StreamDiffusionWrapper
    except ImportError as exc:
        raise SystemExit(
            "Install StreamDiffusion first; see README.md / docs/RTX4080.md"
        ) from exc

    if not torch.cuda.is_available():
        raise SystemExit("CUDA is not available")

    stream = StreamDiffusionWrapper(
        model_id_or_path=args.model,
        t_index_list=[int(v) for v in args.t_index.split(",")],
        frame_buffer_size=1,
        width=args.width,
        height=args.height,
        warmup=args.warmup,
        acceleration=args.acceleration,
        mode="img2img",
        use_denoising_batch=True,
        cfg_type="none" if args.guidance <= 1.0 else args.cfg_type,
        seed=args.seed,
    )
    stream.prepare(
        prompt=args.prompt,
        negative_prompt=args.negative_prompt,
        num_inference_steps=args.num_inference_steps,
        guidance_scale=args.guidance,
        delta=args.delta,
    )
    return stream, torch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="stabilityai/sd-turbo")
    ap.add_argument("--width", type=int, default=768)
    ap.add_argument("--height", type=int, default=432)
    ap.add_argument("--acceleration", choices=["none", "xformers", "tensorrt"], default="xformers")
    ap.add_argument("--t-index", default="22,32,45")
    ap.add_argument("--prompt", default="bioluminescent alien cathedral, liquid light, impossible organic architecture")
    ap.add_argument("--negative-prompt", default="blurry, low quality, text, watermark")
    ap.add_argument("--guidance", type=float, default=1.0)
    ap.add_argument("--cfg-type", choices=["none", "full", "self", "initialize"], default="self")
    ap.add_argument("--num-inference-steps", type=int, default=50)
    ap.add_argument("--delta", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=2)
    ap.add_argument("--warmup", type=int, default=10)
    ap.add_argument("--frames", type=int, default=120)
    ap.add_argument("--output", default="benchmark_streamdiffusion.json")
    args = ap.parse_args()

    stream, torch = build_stream(args)
    report = BenchmarkReport()
    report.metadata.update({
        "model": args.model,
        "resolution": [args.width, args.height],
        "acceleration": args.acceleration,
        "t_index": args.t_index,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(0),
    })

    # Explicit warmup using changing frames to exercise img2img preprocessing.
    for i in range(args.warmup):
        frame = make_test_frame(args.width, args.height, i / 30.0)
        image_tensor = stream.preprocess_image(frame)
        _ = stream(image=image_tensor)
    torch.cuda.synchronize()

    inference = report.timer("inference")
    preprocess = report.timer("preprocess")
    end_to_end = report.timer("preprocess_plus_inference")

    for i in range(args.frames):
        frame = make_test_frame(args.width, args.height, i / 30.0)
        t0 = time.perf_counter()
        p0 = time.perf_counter()
        tensor = stream.preprocess_image(frame)
        torch.cuda.synchronize()
        preprocess.add((time.perf_counter() - p0) * 1000)

        i0 = time.perf_counter()
        out = stream(image=tensor)
        torch.cuda.synchronize()
        inference.add((time.perf_counter() - i0) * 1000)
        end_to_end.add((time.perf_counter() - t0) * 1000)
        if out is None:
            raise RuntimeError("StreamDiffusion returned None")

    report.save(args.output)
    print(json.dumps(report.to_dict(), indent=2))
    print(f"saved {Path(args.output).resolve()}")


if __name__ == "__main__":
    main()

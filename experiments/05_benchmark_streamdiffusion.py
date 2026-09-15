"""Benchmark the same StreamDiffusion backend used by Neural Mirror."""
from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

import numpy as np

from projection_mapping.benchmark import BenchmarkReport
from projection_mapping.streamdiffusion_backend import DaydreamStreamConfig, DaydreamStreamDiffusion, VramSafetyError


def make_test_frame(width: int, height: int, t: float) -> np.ndarray:
    y, x = np.mgrid[0:height, 0:width]
    r = (127.5 + 127.5 * np.sin(x / 37.0 + t)).astype(np.uint8)
    g = (127.5 + 127.5 * np.sin(y / 31.0 - t * 0.7)).astype(np.uint8)
    b = (127.5 + 127.5 * np.sin((x + y) / 53.0 + t * 1.3)).astype(np.uint8)
    return np.dstack([r, g, b])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="stabilityai/sd-turbo")
    ap.add_argument("--width", type=int, default=512)
    ap.add_argument("--height", type=int, default=288)
    ap.add_argument("--acceleration", choices=["auto", "none", "xformers", "tensorrt"], default="auto")
    ap.add_argument("--t-index", default="22,32,45")
    ap.add_argument("--prompt", default="bioluminescent alien cathedral, liquid light, impossible organic architecture")
    ap.add_argument("--negative-prompt", default="blurry, low quality, text, watermark")
    ap.add_argument("--guidance", type=float, default=1.0)
    ap.add_argument("--num-inference-steps", type=int, default=50)
    ap.add_argument("--delta", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=2)
    ap.add_argument("--warmup", type=int, default=6)
    ap.add_argument("--frames", type=int, default=80)
    ap.add_argument("--output", default="benchmark_streamdiffusion.json")
    args = ap.parse_args()

    try:
        import torch
    except ImportError as exc:
        raise SystemExit("PyTorch is required") from exc
    if not torch.cuda.is_available():
        raise SystemExit("CUDA is not available")

    config = DaydreamStreamConfig(
        model_id_or_path=args.model,
        prompt=args.prompt,
        negative_prompt=args.negative_prompt,
        width=args.width,
        height=args.height,
        acceleration=args.acceleration,
        t_index_list=[int(v) for v in args.t_index.split(",")],
        warmup=args.warmup,
        guidance_scale=args.guidance,
        delta=args.delta,
        seed=args.seed,
        num_inference_steps=args.num_inference_steps,
    )

    report = BenchmarkReport()
    backend = None
    try:
        backend = DaydreamStreamDiffusion(config)
        report.metadata.update({
            "model": args.model,
            "resolution": [args.width, args.height],
            "acceleration_requested": args.acceleration,
            "acceleration_selected": backend.acceleration,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0),
        })

        timer = report.timer("preprocess_plus_inference")
        print(f"[bench] timed run: {args.frames} frames", flush=True)
        for i in range(args.frames):
            frame = make_test_frame(args.width, args.height, i / 30.0)
            t0 = time.perf_counter()
            out = backend(frame)
            torch.cuda.synchronize()
            timer.add((time.perf_counter() - t0) * 1000.0)
            if out is None:
                raise RuntimeError("StreamDiffusion returned None")
            if (i + 1) % 10 == 0:
                print(f"[bench] frame {i + 1}/{args.frames}", flush=True)
    except VramSafetyError as exc:
        raise SystemExit(str(exc)) from exc
    finally:
        if backend is not None:
            backend.close()

    report.save(args.output)
    print(json.dumps(report.to_dict(), indent=2))
    print(f"saved {Path(args.output).resolve()}")


if __name__ == "__main__":
    main()

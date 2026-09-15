"""Benchmark StreamDiffusion configurations on the local GPU.

Separates preprocessing from inference latency, emits stage-by-stage progress, uses the
same conservative VRAM policy as the live backend, and writes a JSON report.
"""
from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

import numpy as np

from projection_mapping.benchmark import BenchmarkReport
from projection_mapping.vram import CudaVramGuard, VramSafetyError


def make_test_frame(width: int, height: int, t: float) -> np.ndarray:
    y, x = np.mgrid[0:height, 0:width]
    r = (127.5 + 127.5 * np.sin(x / 37.0 + t)).astype(np.uint8)
    g = (127.5 + 127.5 * np.sin(y / 31.0 - t * 0.7)).astype(np.uint8)
    b = (127.5 + 127.5 * np.sin((x + y) / 53.0 + t * 1.3)).astype(np.uint8)
    return np.dstack([r, g, b])


def _as_pil(frame: np.ndarray):
    from PIL import Image

    return Image.fromarray(np.asarray(frame, dtype=np.uint8), mode="RGB")


def build_stream(args):
    print("[bench] importing torch + StreamDiffusion...", flush=True)
    try:
        import torch
        from streamdiffusion import StreamDiffusionWrapper
    except ImportError as exc:
        raise SystemExit("Install StreamDiffusion first; see README.md / docs/RTX4080.md") from exc

    if not torch.cuda.is_available():
        raise SystemExit("CUDA is not available")

    guard = CudaVramGuard()
    snap = guard.arm(required_gib=3.0)
    print(
        f"[bench] GPU={torch.cuda.get_device_name(0)!r} free={snap.free_gib:.2f}GiB "
        f"safe_budget={snap.budget_gib:.2f}GiB reserve={snap.reserve_gib:.2f}GiB",
        flush=True,
    )
    print(
        f"[bench] constructing wrapper model={args.model!r} {args.width}x{args.height} "
        f"acceleration={args.acceleration}",
        flush=True,
    )
    try:
        stream = guard.run(
            StreamDiffusionWrapper,
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
        print("[bench] preparing stream/prompt...", flush=True)
        guard.run(
            stream.prepare,
            prompt=args.prompt,
            negative_prompt=args.negative_prompt,
            num_inference_steps=args.num_inference_steps,
            guidance_scale=args.guidance,
            delta=args.delta,
        )
    except VramSafetyError as exc:
        raise SystemExit(str(exc)) from exc
    print("[bench] model prepared", flush=True)
    return stream, torch, guard


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

    stream, torch, guard = build_stream(args)
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

    print(f"[bench] warmup: {args.warmup} frames", flush=True)
    try:
        for i in range(args.warmup):
            frame = _as_pil(make_test_frame(args.width, args.height, i / 30.0))
            image_tensor = stream.preprocess_image(frame)
            _ = guard.run(stream, image=image_tensor)
            if (i + 1) % max(1, args.warmup // 4) == 0:
                print(f"[bench] warmup {i + 1}/{args.warmup}", flush=True)
        torch.cuda.synchronize()

        inference = report.timer("inference")
        preprocess = report.timer("preprocess")
        end_to_end = report.timer("preprocess_plus_inference")

        print(f"[bench] timed run: {args.frames} frames", flush=True)
        for i in range(args.frames):
            frame = _as_pil(make_test_frame(args.width, args.height, i / 30.0))
            t0 = time.perf_counter()
            p0 = time.perf_counter()
            tensor = stream.preprocess_image(frame)
            torch.cuda.synchronize()
            preprocess.add((time.perf_counter() - p0) * 1000)

            i0 = time.perf_counter()
            out = guard.run(stream, image=tensor)
            torch.cuda.synchronize()
            inference.add((time.perf_counter() - i0) * 1000)
            end_to_end.add((time.perf_counter() - t0) * 1000)
            if out is None:
                raise RuntimeError("StreamDiffusion returned None")
            if (i + 1) % 20 == 0:
                print(f"[bench] frame {i + 1}/{args.frames}", flush=True)
    except VramSafetyError as exc:
        raise SystemExit(str(exc)) from exc
    finally:
        try:
            guard.cleanup()
        except Exception:
            pass

    report.save(args.output)
    print(json.dumps(report.to_dict(), indent=2))
    print(f"saved {Path(args.output).resolve()}")


if __name__ == "__main__":
    main()

from __future__ import annotations

from dataclasses import dataclass, field
import importlib.util
from typing import Literal

import numpy as np

from .vram import CudaVramGuard, VramSafetyError


Acceleration = Literal["auto", "none", "xformers", "tensorrt"]
CfgType = Literal["none", "full", "self", "initialize"]


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError, AttributeError):
        return False


def resolve_acceleration(requested: Acceleration) -> Literal["none", "xformers", "tensorrt"]:
    """Resolve an acceleration request without making an optional package a hard dependency."""
    if requested == "auto":
        if _module_available("xformers"):
            return "xformers"
        return "none"
    if requested == "xformers" and not _module_available("xformers"):
        print("[neural] xformers requested but not installed; using PyTorch/native attention", flush=True)
        return "none"
    if requested == "tensorrt" and not _module_available("tensorrt"):
        print("[neural] TensorRT requested but Python runtime is unavailable; using native attention", flush=True)
        return "none"
    return requested


@dataclass
class DaydreamStreamConfig:
    model_id_or_path: str = "stabilityai/sd-turbo"
    prompt: str = "bioluminescent living architecture, immersive projection art"
    negative_prompt: str = "blurry, low quality, low resolution, text, watermark"
    width: int = 512
    height: int = 288
    acceleration: Acceleration = "auto"
    t_index_list: list[int] = field(default_factory=lambda: [32, 45])
    frame_buffer_size: int = 1
    warmup: int = 6
    use_denoising_batch: bool = True
    guidance_scale: float = 1.0
    cfg_type: CfgType = "none"
    seed: int = 2
    delta: float = 0.5
    num_inference_steps: int = 50
    vram_device: int = 0
    vram_reserve_gib: float = 1.5
    vram_reserve_fraction: float = 0.15
    vram_minimum_budget_gib: float = 2.0


class DaydreamStreamDiffusion:
    """Numpy-friendly Daydream StreamDiffusion adapter with safe acceleration fallback."""

    def __init__(self, config: DaydreamStreamConfig | None = None) -> None:
        self.config = config or DaydreamStreamConfig()
        cfg = self.config
        print("[neural] stage=preflight", flush=True)
        self.vram_guard = CudaVramGuard(
            device=cfg.vram_device,
            reserve_gib=cfg.vram_reserve_gib,
            reserve_fraction=cfg.vram_reserve_fraction,
            minimum_budget_gib=cfg.vram_minimum_budget_gib,
        )
        # 512x288 SD-Turbo is the intended 6 GB-safe profile. Larger resolutions are
        # allowed, but only after the same live free-memory check.
        required = 2.5 if cfg.width * cfg.height <= 512 * 288 else 3.0
        self.vram_snapshot = self.vram_guard.arm(required_gib=required)
        print(
            f"[neural] VRAM free={self.vram_snapshot.free_gib:.2f}GiB "
            f"safe_budget={self.vram_snapshot.budget_gib:.2f}GiB reserve={self.vram_snapshot.reserve_gib:.2f}GiB",
            flush=True,
        )

        print("[neural] stage=import-streamdiffusion", flush=True)
        try:
            from streamdiffusion import StreamDiffusionWrapper
        except ImportError as exc:
            raise RuntimeError(
                "StreamDiffusion is not installed. Install the Daydream fork as documented "
                "in README.md / docs/RTX4080.md."
            ) from exc

        cfg_type: CfgType = cfg.cfg_type
        if cfg.guidance_scale <= 1.0:
            cfg_type = "none"

        requested = cfg.acceleration
        selected = resolve_acceleration(requested)
        self.acceleration = selected
        print(
            f"[neural] acceleration requested={requested} selected={selected}",
            flush=True,
        )

        def construct(acceleration: str):
            print(
                f"[neural] stage=model-load/download-if-needed model={cfg.model_id_or_path!r} "
                f"resolution={cfg.width}x{cfg.height} acceleration={acceleration}",
                flush=True,
            )
            return self.vram_guard.run(
                StreamDiffusionWrapper,
                model_id_or_path=cfg.model_id_or_path,
                t_index_list=list(cfg.t_index_list),
                frame_buffer_size=cfg.frame_buffer_size,
                width=cfg.width,
                height=cfg.height,
                warmup=cfg.warmup,
                acceleration=acceleration,
                mode="img2img",
                use_denoising_batch=cfg.use_denoising_batch,
                cfg_type=cfg_type,
                seed=cfg.seed,
            )

        try:
            self.stream = construct(selected)
        except Exception as exc:
            # Optional accelerators fail for many mundane environment reasons (missing
            # wheel, ABI mismatch, unsupported engine). A live visual should still run.
            if selected == "none":
                raise
            print(
                f"[neural] accelerator {selected!r} failed ({type(exc).__name__}: {exc}); "
                "cleaning CUDA cache and retrying with native PyTorch attention",
                flush=True,
            )
            self.vram_guard.cleanup()
            self.acceleration = "none"
            self.stream = construct("none")

        print("[neural] stage=prepare", flush=True)
        self.vram_guard.run(
            self.stream.prepare,
            prompt=cfg.prompt,
            negative_prompt=cfg.negative_prompt,
            num_inference_steps=cfg.num_inference_steps,
            guidance_scale=cfg.guidance_scale,
            delta=cfg.delta,
        )
        print("[neural] stage=warmup", flush=True)
        self._prime()
        print("[neural] stage=ready", flush=True)

    def _prime(self) -> None:
        from PIL import Image

        cfg = self.config
        neutral = Image.fromarray(np.full((cfg.height, cfg.width, 3), 127, dtype=np.uint8))
        image_tensor = self.vram_guard.run(self.stream.preprocess_image, neutral)
        for _ in range(max(int(getattr(self.stream, "batch_size", 1)) - 1, 0)):
            self.vram_guard.run(self.stream, image=image_tensor)

    def update_prompt(self, prompt: str, negative_prompt: str | None = None) -> None:
        self.config.prompt = prompt
        if negative_prompt is not None:
            self.config.negative_prompt = negative_prompt
        updater = getattr(self.stream, "update_stream_params", None)
        if callable(updater):
            kwargs = {"prompt": prompt}
            if negative_prompt is not None:
                kwargs["negative_prompt"] = negative_prompt
            self.vram_guard.run(updater, **kwargs)
            return
        self.vram_guard.run(
            self.stream.prepare,
            prompt=self.config.prompt,
            negative_prompt=self.config.negative_prompt,
            num_inference_steps=self.config.num_inference_steps,
            guidance_scale=self.config.guidance_scale,
            delta=self.config.delta,
        )

    def close(self) -> None:
        stream = getattr(self, "stream", None)
        self.stream = None
        if stream is not None:
            del stream
        try:
            self.vram_guard.cleanup()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()

    def __call__(self, frame_rgb: np.ndarray) -> np.ndarray:
        from PIL import Image

        frame = np.asarray(frame_rgb, dtype=np.uint8)
        if frame.ndim != 3 or frame.shape[2] != 3:
            raise ValueError("expected HxWx3 RGB uint8 frame")
        image = Image.fromarray(frame, mode="RGB")
        if image.size != (self.config.width, self.config.height):
            image = image.resize((self.config.width, self.config.height))
        image_tensor = self.vram_guard.run(self.stream.preprocess_image, image)
        output = self.vram_guard.run(self.stream, image=image_tensor)
        if hasattr(output, "convert"):
            return np.asarray(output.convert("RGB"), dtype=np.uint8)
        if hasattr(output, "detach"):
            tensor = output.detach().float().cpu()
            if tensor.ndim == 4:
                tensor = tensor[0]
            if tensor.ndim == 3 and tensor.shape[0] in (1, 3, 4):
                tensor = tensor.permute(1, 2, 0)
            array = tensor.numpy()
            if array.max(initial=0.0) <= 1.0:
                array = array * 255.0
            return np.clip(array[..., :3], 0, 255).astype(np.uint8)
        array = np.asarray(output)
        if array.ndim == 4:
            array = array[0]
        return np.clip(array[..., :3], 0, 255).astype(np.uint8)


__all__ = [
    "DaydreamStreamConfig",
    "DaydreamStreamDiffusion",
    "VramSafetyError",
    "resolve_acceleration",
]

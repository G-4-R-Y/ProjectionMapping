from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np


Acceleration = Literal["none", "xformers", "tensorrt"]
CfgType = Literal["none", "full", "self", "initialize"]


@dataclass
class DaydreamStreamConfig:
    model_id_or_path: str = "stabilityai/sd-turbo"
    prompt: str = "bioluminescent living architecture, immersive projection art"
    negative_prompt: str = "blurry, low quality, low resolution, text, watermark"
    width: int = 768
    height: int = 432
    acceleration: Acceleration = "xformers"
    t_index_list: list[int] = field(default_factory=lambda: [32, 45])
    frame_buffer_size: int = 1
    warmup: int = 10
    use_denoising_batch: bool = True
    guidance_scale: float = 1.0
    cfg_type: CfgType = "none"
    seed: int = 2
    delta: float = 0.5
    num_inference_steps: int = 50


class DaydreamStreamDiffusion:
    """Thin ndarray-friendly wrapper around daydreamlive/StreamDiffusion.

    Imports are lazy so the core package remains usable without the heavyweight diffusion
    stack. Input/output are RGB uint8 numpy arrays. The backend follows the current
    ``StreamDiffusionWrapper`` API used by the upstream img2img examples.
    """

    def __init__(self, config: DaydreamStreamConfig | None = None) -> None:
        self.config = config or DaydreamStreamConfig()
        try:
            from streamdiffusion import StreamDiffusionWrapper
        except ImportError as exc:
            raise RuntimeError(
                "StreamDiffusion is not installed. Install the Daydream fork as documented "
                "in README.md / docs/RTX4080.md."
            ) from exc

        cfg = self.config
        cfg_type: CfgType = cfg.cfg_type
        if cfg.guidance_scale <= 1.0:
            cfg_type = "none"

        self.stream = StreamDiffusionWrapper(
            model_id_or_path=cfg.model_id_or_path,
            t_index_list=list(cfg.t_index_list),
            frame_buffer_size=cfg.frame_buffer_size,
            width=cfg.width,
            height=cfg.height,
            warmup=cfg.warmup,
            acceleration=cfg.acceleration,
            mode="img2img",
            use_denoising_batch=cfg.use_denoising_batch,
            cfg_type=cfg_type,
            seed=cfg.seed,
        )
        self.stream.prepare(
            prompt=cfg.prompt,
            negative_prompt=cfg.negative_prompt,
            num_inference_steps=cfg.num_inference_steps,
            guidance_scale=cfg.guidance_scale,
            delta=cfg.delta,
        )
        self._prime()

    def _prime(self) -> None:
        """Warm the stream with a neutral frame so the first live frame is not special."""
        from PIL import Image

        cfg = self.config
        neutral = Image.fromarray(np.full((cfg.height, cfg.width, 3), 127, dtype=np.uint8))
        image_tensor = self.stream.preprocess_image(neutral)
        # Upstream examples prime ``batch_size - 1`` frames after wrapper warmup.
        for _ in range(max(int(getattr(self.stream, "batch_size", 1)) - 1, 0)):
            self.stream(image=image_tensor)

    def update_prompt(self, prompt: str, negative_prompt: str | None = None) -> None:
        self.config.prompt = prompt
        if negative_prompt is not None:
            self.config.negative_prompt = negative_prompt

        # Prefer the upstream live parameter updater if present; fall back to prepare.
        updater = getattr(self.stream, "update_stream_params", None)
        if callable(updater):
            kwargs = {"prompt": prompt}
            if negative_prompt is not None:
                kwargs["negative_prompt"] = negative_prompt
            updater(**kwargs)
            return

        self.stream.prepare(
            prompt=self.config.prompt,
            negative_prompt=self.config.negative_prompt,
            num_inference_steps=self.config.num_inference_steps,
            guidance_scale=self.config.guidance_scale,
            delta=self.config.delta,
        )

    def __call__(self, frame_rgb: np.ndarray) -> np.ndarray:
        from PIL import Image

        frame = np.asarray(frame_rgb, dtype=np.uint8)
        if frame.ndim != 3 or frame.shape[2] != 3:
            raise ValueError("expected HxWx3 RGB uint8 frame")

        image = Image.fromarray(frame, mode="RGB")
        if image.size != (self.config.width, self.config.height):
            image = image.resize((self.config.width, self.config.height))

        image_tensor = self.stream.preprocess_image(image)
        output = self.stream(image=image_tensor)

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

from __future__ import annotations

from dataclasses import dataclass
import numpy as np


class PassthroughGenerator:
    def __call__(self, frame: np.ndarray) -> np.ndarray:
        return frame


@dataclass
class StreamDiffusionConfig:
    prompt: str = "bioluminescent living architecture, immersive projection art"
    negative_prompt: str = "blurry, low quality"
    width: int = 512
    height: int = 512


class StreamDiffusionGenerator:
    """Lazy integration point for StreamDiffusion.

    StreamDiffusion's public API changes quickly; this wrapper accepts an already-built
    callable pipeline so the stable runtime in this repo does not depend on a specific fork.
    The callable should accept an RGB uint8 ndarray and return an RGB ndarray/PIL image.
    """
    def __init__(self, pipeline, config: StreamDiffusionConfig | None = None):
        self.pipeline = pipeline
        self.config = config or StreamDiffusionConfig()

    def __call__(self, frame_rgb: np.ndarray) -> np.ndarray:
        out = self.pipeline(frame_rgb)
        if hasattr(out, "convert"):
            out = np.asarray(out.convert("RGB"))
        return np.asarray(out, dtype=np.uint8)


def blend_with_mask(base: np.ndarray, generated: np.ndarray, mask: np.ndarray, feather: int = 9) -> np.ndarray:
    import cv2
    if generated.shape[:2] != base.shape[:2]:
        generated = cv2.resize(generated, (base.shape[1], base.shape[0]), interpolation=cv2.INTER_LINEAR)
    m = mask.astype(np.float32)
    if m.max() > 1:
        m /= 255.0
    if feather > 0:
        m = cv2.GaussianBlur(m, (feather | 1, feather | 1), 0)
    return np.clip(base * (1 - m[..., None]) + generated * m[..., None], 0, 255).astype(np.uint8)

from __future__ import annotations

import math
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class PatternFrame:
    image: np.ndarray
    name: str
    metadata: dict


def checkerboard(width: int, height: int, cell: int = 64) -> np.ndarray:
    y, x = np.indices((height, width))
    board = ((x // cell + y // cell) & 1) * 255
    return np.repeat(board[..., None].astype(np.uint8), 3, axis=2)


def grid(width: int, height: int, spacing: int = 80, thickness: int = 2) -> np.ndarray:
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:, ::spacing] = 255
    img[::spacing, :] = 255
    if thickness > 1:
        for d in range(1, thickness):
            img[:, d::spacing] = 255
            img[d::spacing, :] = 255
    img[:, max(0, width // 2 - 1): width // 2 + 2, 1] = 255
    img[max(0, height // 2 - 1): height // 2 + 2, :, 2] = 255
    return img


def color_ramp(width: int, height: int, channel: int | None = None) -> np.ndarray:
    ramp = np.linspace(0, 255, width, dtype=np.uint8)
    img = np.zeros((height, width, 3), dtype=np.uint8)
    if channel is None:
        img[:] = ramp[None, :, None]
    else:
        img[..., channel] = ramp[None, :]
    return img


def gray_encode(values: np.ndarray) -> np.ndarray:
    values = values.astype(np.uint32, copy=False)
    return values ^ (values >> 1)


def graycode_sequence(width: int, height: int, include_inverse: bool = True) -> list[PatternFrame]:
    frames: list[PatternFrame] = []
    for axis, size in (("x", width), ("y", height)):
        bits = max(1, math.ceil(math.log2(size)))
        coords = np.arange(size, dtype=np.uint32)
        codes = gray_encode(coords)
        for bit in reversed(range(bits)):
            line = (((codes >> bit) & 1) * 255).astype(np.uint8)
            plane = np.tile(line[None, :], (height, 1)) if axis == "x" else np.tile(line[:, None], (1, width))
            img = np.repeat(plane[..., None], 3, axis=2)
            meta = {"axis": axis, "bit": bit, "inverse": False, "bits": bits}
            frames.append(PatternFrame(img, f"gray_{axis}_b{bit}", meta))
            if include_inverse:
                frames.append(PatternFrame(255 - img, f"gray_{axis}_b{bit}_inv", {**meta, "inverse": True}))
    return frames


def phase_shift_sequence(width: int, height: int, periods: int = 16, phases: int = 4) -> list[PatternFrame]:
    out: list[PatternFrame] = []
    for axis, n in (("x", width), ("y", height)):
        coord = np.arange(n, dtype=np.float32)
        for k in range(phases):
            phi = 2 * np.pi * k / phases
            signal = 0.5 + 0.5 * np.cos(2 * np.pi * periods * coord / n + phi)
            line = np.clip(signal * 255, 0, 255).astype(np.uint8)
            plane = np.tile(line[None, :], (height, 1)) if axis == "x" else np.tile(line[:, None], (1, width))
            out.append(PatternFrame(np.repeat(plane[..., None], 3, 2), f"phase_{axis}_{k}", {"axis": axis, "phase": k, "phases": phases, "periods": periods}))
    return out

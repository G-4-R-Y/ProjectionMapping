from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class ChannelLUT:
    emitted: np.ndarray
    observed: np.ndarray

    def inverse(self, desired: np.ndarray) -> np.ndarray:
        order = np.argsort(self.observed)
        obs = self.observed[order]
        emit = self.emitted[order]
        obs, idx = np.unique(obs, return_index=True)
        emit = emit[idx]
        return np.interp(desired, obs, emit, left=emit[0], right=emit[-1])


@dataclass
class RGBRadiometricCalibration:
    channels: tuple[ChannelLUT, ChannelLUT, ChannelLUT]

    @classmethod
    def fit(cls, emitted_levels: np.ndarray, observed_rgb: np.ndarray) -> "RGBRadiometricCalibration":
        levels = np.asarray(emitted_levels, np.float32)
        obs = np.asarray(observed_rgb, np.float32)
        if obs.shape != (len(levels), 3):
            raise ValueError("observed_rgb must have shape [levels, 3]")
        return cls(tuple(ChannelLUT(levels, obs[:, c]) for c in range(3)))

    def compensate(self, target_rgb: np.ndarray) -> np.ndarray:
        target = np.asarray(target_rgb, np.float32)
        out = np.empty_like(target)
        for c, lut in enumerate(self.channels):
            out[..., c] = lut.inverse(target[..., c])
        return np.clip(out, 0, 255)

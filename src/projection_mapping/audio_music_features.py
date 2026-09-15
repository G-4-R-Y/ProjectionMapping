from __future__ import annotations

import math
import time

import numpy as np

from .audio_reactive import AudioFeatures


class RollingMusicFeatureExtractor:
    """Music-oriented feature extractor with a longer FFT than the capture block.

    Capture can stay at 128/256 samples for latency while spectral analysis uses a rolling
    2048-sample window (~42.7 ms at 48 kHz). This avoids the old 256-sample failure mode
    where FFT spacing is 187.5 Hz and the nominal 35-180 Hz bass band can contain zero bins.

    Band controls are based on spectral power fractions multiplied by an adaptive loudness
    envelope, so inactive bands do not self-normalize into fake energy. Spectral novelty is
    normalized by previous spectral mass, making onset evidence much less dependent on the
    absolute recording level.
    """

    def __init__(
        self,
        sample_rate: int = 48_000,
        analysis_size: int = 2048,
        attack_ms: float = 7.0,
        release_ms: float = 125.0,
        sensitivity: float = 1.25,
    ) -> None:
        if analysis_size < 512:
            raise ValueError("analysis_size must be >= 512")
        self.sample_rate = int(sample_rate)
        self.analysis_size = int(analysis_size)
        self.attack_ms = float(attack_ms)
        self.release_ms = float(release_ms)
        self.sensitivity = float(max(sensitivity, 0.05))

        self._buffer = np.zeros(self.analysis_size, dtype=np.float32)
        self._filled = 0
        self._window = np.hanning(self.analysis_size).astype(np.float32)
        self._freqs = np.fft.rfftfreq(self.analysis_size, d=1.0 / self.sample_rate)
        self._previous_spectrum: np.ndarray | None = None
        self._last_time: float | None = None
        self._smoothed = np.zeros(7, dtype=np.float32)
        self._rms_peak = 0.02
        self._previous_rms = 0.0

    @staticmethod
    def _mono(block: np.ndarray) -> np.ndarray:
        x = np.asarray(block, dtype=np.float32)
        if x.ndim == 1:
            return x
        if x.ndim != 2:
            raise ValueError("audio block must be [frames] or [frames, channels]")
        if x.shape[1] == 0:
            return np.empty(0, dtype=np.float32)
        return x.mean(axis=1, dtype=np.float32)

    def _append(self, mono: np.ndarray) -> None:
        n = int(mono.size)
        if n >= self.analysis_size:
            self._buffer[:] = mono[-self.analysis_size :]
            self._filled = self.analysis_size
            return
        if n <= 0:
            return
        self._buffer[:-n] = self._buffer[n:]
        self._buffer[-n:] = mono
        self._filled = min(self.analysis_size, self._filled + n)

    def _envelope(self, previous: float, target: float, dt: float) -> float:
        tau_ms = self.attack_ms if target > previous else self.release_ms
        tau = max(tau_ms / 1000.0, 1e-4)
        alpha = 1.0 - math.exp(-max(dt, 1e-5) / tau)
        return previous + alpha * (target - previous)

    def _band_power(self, power: np.ndarray, lo: float, hi: float) -> float:
        mask = (self._freqs >= lo) & (self._freqs < hi)
        if not np.any(mask):
            return 0.0
        return float(np.sum(power[mask]))

    def process(self, block: np.ndarray, timestamp: float | None = None) -> AudioFeatures:
        now = float(timestamp if timestamp is not None else time.perf_counter())
        mono = self._mono(block)
        if mono.size < 8:
            return AudioFeatures(timestamp=now)
        mono = mono - float(np.mean(mono))
        self._append(mono)

        rms_raw = float(np.sqrt(np.mean(np.square(mono)) + 1e-12))
        dt = 1.0 / 120.0 if self._last_time is None else max(now - self._last_time, 1e-5)
        self._last_time = now

        # Peak reference falls slowly, rises instantly. This gives natural automatic gain
        # without turning silence/noise into full-scale visuals.
        self._rms_peak *= math.exp(-dt / 3.0)
        self._rms_peak = max(self._rms_peak, rms_raw, 0.012)
        loud = float(np.clip((rms_raw / max(self._rms_peak * 0.82, 0.012)) * self.sensitivity, 0.0, 1.0))

        analysis = self._buffer
        spectrum = np.abs(np.fft.rfft(analysis * self._window)).astype(np.float32)
        power = np.square(spectrum, dtype=np.float32)
        audible_mask = (self._freqs >= 35.0) & (self._freqs < 10_000.0)
        total_power = float(np.sum(power[audible_mask])) + 1e-12

        bass_fraction = self._band_power(power, 35.0, 180.0) / total_power
        mid_fraction = self._band_power(power, 180.0, 2_000.0) / total_power
        treble_fraction = self._band_power(power, 2_000.0, 10_000.0) / total_power

        # sqrt softens the huge dynamic range of power while preserving spectral ownership.
        bass_raw = loud * min(math.sqrt(max(bass_fraction, 0.0)) * 1.55, 1.0)
        mid_raw = loud * min(math.sqrt(max(mid_fraction, 0.0)) * 1.35, 1.0)
        treble_raw = loud * min(math.sqrt(max(treble_fraction, 0.0)) * 1.55, 1.0)

        spec_sum = float(np.sum(spectrum[audible_mask])) + 1e-12
        centroid = float(np.sum(self._freqs[audible_mask] * spectrum[audible_mask]) / spec_sum)
        centroid_raw = float(np.clip(centroid / 10_000.0, 0.0, 1.0))

        if self._previous_spectrum is None:
            flux_raw = 0.0
        else:
            positive = np.maximum(spectrum - self._previous_spectrum, 0.0)
            denom = float(np.sum(self._previous_spectrum[audible_mask])) + 1e-9
            flux_raw = float(np.sum(positive[audible_mask]) / denom)
        self._previous_spectrum = spectrum

        rms_rise = max(rms_raw - self._previous_rms, 0.0) / max(self._rms_peak, 1e-4)
        self._previous_rms = rms_raw
        flux = float(np.clip(flux_raw * 3.0, 0.0, 1.0))
        onset = float(np.clip(flux * 0.78 + min(rms_rise * 3.0, 1.0) * 0.22, 0.0, 1.0))

        targets = np.asarray(
            [loud, bass_raw, mid_raw, treble_raw, centroid_raw, flux, onset], dtype=np.float32
        )
        for i, target in enumerate(targets):
            self._smoothed[i] = self._envelope(float(self._smoothed[i]), float(target), dt)

        return AudioFeatures(
            timestamp=now,
            rms=float(np.clip(self._smoothed[0], 0.0, 1.0)),
            bass=float(np.clip(self._smoothed[1], 0.0, 1.0)),
            mid=float(np.clip(self._smoothed[2], 0.0, 1.0)),
            treble=float(np.clip(self._smoothed[3], 0.0, 1.0)),
            centroid=float(np.clip(self._smoothed[4], 0.0, 1.0)),
            flux=float(np.clip(self._smoothed[5], 0.0, 1.0)),
            onset=float(np.clip(self._smoothed[6], 0.0, 1.0)),
        )


__all__ = ["RollingMusicFeatureExtractor"]

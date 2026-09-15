from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import math

import numpy as np

from .audio_reactive import AudioFeatures


@dataclass(frozen=True)
class MusicalSignals:
    loudness: float
    bass: float
    mids: float
    highs: float
    color: float
    strike: float
    beat: float
    ascension: float
    tempo_bpm: float = 0.0
    beat_phase: float = 0.0
    bar_phase: float = 0.0
    beat_confidence: float = 0.0
    section_energy: float = 0.0
    drop: float = 0.0


_REACTIVITY = {
    "smooth": dict(gain=0.80, onset=0.72, beat=0.58, refractory=0.30, release=4.5, adaptive=1.45),
    "balanced": dict(gain=1.00, onset=0.62, beat=0.50, refractory=0.22, release=6.0, adaptive=1.25),
    "punchy": dict(gain=1.15, onset=0.54, beat=0.42, refractory=0.17, release=7.5, adaptive=1.05),
    "chaotic": dict(gain=1.35, onset=0.42, beat=0.34, refractory=0.11, release=9.5, adaptive=0.85),
}


def _smoothstep(lo: float, hi: float, x: float) -> float:
    if hi <= lo:
        return float(x >= hi)
    t = float(np.clip((x - lo) / (hi - lo), 0.0, 1.0))
    return t * t * (3.0 - 2.0 * t)


def _adaptive_gate(history: deque[float], floor: float, sigma: float) -> float:
    if len(history) < 12:
        return float(floor)
    values = np.asarray(history, dtype=np.float32)
    # Robust centre/spread: dense mixes can contain many peaks, so median/MAD behaves
    # much better than mean/std for deciding what is actually exceptional.
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median))) * 1.4826
    return float(np.clip(max(floor, median + sigma * max(mad, 0.015)), floor, 0.94))


class MusicalEventMapper:
    """Turn low-level audio features into stable musical controls and sparse events.

    Continuous envelopes drive motion. Visible accents use adaptive robust thresholds,
    minimum spacing and one-trigger-per-audio-block semantics. Accepted bass events also
    feed a lightweight tempo/phase tracker so periodic animation can move *with* the music
    instead of jittering on every FFT update.
    """

    def __init__(
        self,
        mode: str = "balanced",
        event_threshold: float | None = None,
        beat_threshold: float | None = None,
        madness: float = 0.45,
    ) -> None:
        if mode not in _REACTIVITY:
            raise ValueError(f"unknown reactivity mode: {mode}")
        self.mode = mode
        self.params = dict(_REACTIVITY[mode])
        if event_threshold is not None:
            self.params["onset"] = float(event_threshold)
        if beat_threshold is not None:
            self.params["beat"] = float(beat_threshold)
        self.madness = float(np.clip(madness, 0.0, 1.0))

        self._last_t: float | None = None
        self._last_feature_timestamp = -math.inf
        self._last_strike = -999.0
        self._last_beat = -999.0
        self._last_ascension = -999.0
        self._last_drop = -999.0
        self._strike_energy = 0.0
        self._beat_energy = 0.0
        self._ascension_energy = 0.0
        self._drop_energy = 0.0
        self._bass_slow = 0.0
        self._section_energy = 0.0
        self._fast_energy = 0.0

        self._onset_history: deque[float] = deque(maxlen=96)
        self._beat_history: deque[float] = deque(maxlen=96)
        self._beat_times: deque[float] = deque(maxlen=12)
        self._beat_period = 0.0
        self._beat_confidence = 0.0
        self._beat_counter = 0

    def _update_tempo(self, now: float) -> None:
        self._beat_times.append(now)
        if len(self._beat_times) < 3:
            return
        intervals = np.diff(np.asarray(self._beat_times, dtype=np.float64))
        # Common musical range. Half/double-time ambiguity is fine for visual phase; reject
        # pathological refractory/noise intervals instead of forcing a BPM estimate.
        valid = intervals[(intervals >= 0.30) & (intervals <= 1.05)]
        if valid.size < 2:
            return
        period = float(np.median(valid))
        mad = float(np.median(np.abs(valid - period)))
        confidence = float(np.clip(1.0 - mad / max(period * 0.18, 1e-3), 0.0, 1.0))
        if self._beat_period <= 0.0:
            self._beat_period = period
        else:
            # Avoid visible phase jumps from one imperfect beat observation.
            self._beat_period = self._beat_period * 0.82 + period * 0.18
        self._beat_confidence = self._beat_confidence * 0.75 + confidence * 0.25

    def update(self, f: AudioFeatures, now: float) -> MusicalSignals:
        if self._last_t is None:
            dt = 1.0 / 60.0
        else:
            dt = float(np.clip(now - self._last_t, 1e-4, 0.2))
        self._last_t = now

        # The display loop often samples the same latest audio block several times. Never let
        # one captured transient create several musical events simply because rendering is fast.
        new_feature = float(f.timestamp) > self._last_feature_timestamp + 1e-9
        if new_feature:
            self._last_feature_timestamp = float(f.timestamp)

        p = self.params
        gain = float(p["gain"])
        rms = _smoothstep(0.08, 0.78, f.rms * gain)
        bass = _smoothstep(0.10, 0.78, f.bass * gain)
        mids = _smoothstep(0.10, 0.82, f.mid * gain)
        # High-frequency information is detail, not the main animation clock.
        highs = _smoothstep(0.34, 0.88, f.treble * gain) if f.treble >= 0.30 else 0.0

        slow_alpha = 1.0 - math.exp(-dt / 0.24)
        self._bass_slow += slow_alpha * (float(f.bass) - self._bass_slow)
        bass_punch = max(float(f.bass) - self._bass_slow, 0.0)

        # Two time scales give us a crude but useful macro-dynamics descriptor. It is not song
        # segmentation; it is a stable control for scene brightness and rare "drop" accents.
        section_alpha = 1.0 - math.exp(-dt / 3.2)
        fast_alpha = 1.0 - math.exp(-dt / 0.18)
        self._section_energy += section_alpha * (rms - self._section_energy)
        self._fast_energy += fast_alpha * (rms - self._fast_energy)

        beat_evidence = 0.68 * float(f.bass) + 0.32 * min(bass_punch * 5.5, 1.0)
        if new_feature:
            self._onset_history.append(float(f.onset))
            self._beat_history.append(float(beat_evidence))

        selectivity = float(p["adaptive"])
        onset_gate = _adaptive_gate(self._onset_history, float(p["onset"]), selectivity)
        beat_gate = _adaptive_gate(self._beat_history, float(p["beat"]), selectivity * 0.82)
        refractory = float(p["refractory"])

        strike = 0.0
        if (
            new_feature
            and f.onset >= onset_gate
            and f.rms >= 0.13
            and now - self._last_strike >= refractory
        ):
            strike = _smoothstep(onset_gate, 0.98, f.onset)
            self._strike_energy = max(self._strike_energy, strike)
            self._last_strike = now

        beat = 0.0
        if (
            new_feature
            and beat_evidence >= beat_gate
            and f.rms >= 0.11
            and now - self._last_beat >= max(0.13, refractory * 0.82)
        ):
            beat = _smoothstep(beat_gate, 0.98, beat_evidence)
            self._beat_energy = max(self._beat_energy, beat)
            self._last_beat = now
            self._beat_counter += 1
            self._update_tempo(now)

        ascension = 0.0
        if (
            new_feature
            and f.onset >= max(0.80, onset_gate + 0.13)
            and f.bass >= max(0.50, beat_gate - 0.02)
            and f.rms >= 0.23
            and now - self._last_ascension >= 0.70
        ):
            ascension = 1.0
            self._ascension_energy = 1.0
            self._last_ascension = now

        drop = 0.0
        dynamic_jump = self._fast_energy - self._section_energy
        if (
            new_feature
            and dynamic_jump >= 0.18
            and f.onset >= max(0.64, onset_gate - 0.04)
            and f.bass >= 0.46
            and now - self._last_drop >= 2.2
        ):
            drop = float(np.clip(0.65 + dynamic_jump * 1.6, 0.0, 1.0))
            self._drop_energy = max(self._drop_energy, drop)
            self._last_drop = now

        release = float(p["release"])
        self._strike_energy *= math.exp(-dt * release)
        self._beat_energy *= math.exp(-dt * release * 0.72)
        self._ascension_energy *= math.exp(-dt * 2.2)
        self._drop_energy *= math.exp(-dt * 1.45)

        beat_phase = 0.0
        bar_phase = 0.0
        tempo_bpm = 0.0
        if self._beat_period > 0.0 and self._last_beat > -100.0:
            beat_phase = float(((now - self._last_beat) / self._beat_period) % 1.0)
            bar_phase = float(((self._beat_counter % 4) + beat_phase) / 4.0)
            tempo_bpm = float(60.0 / self._beat_period)

        m = self.madness
        return MusicalSignals(
            loudness=float(np.clip(rms * (0.80 + 0.35 * m), 0.0, 1.0)),
            bass=float(np.clip(bass * (0.85 + 0.30 * m), 0.0, 1.0)),
            mids=float(np.clip(mids * (0.85 + 0.35 * m), 0.0, 1.0)),
            highs=float(np.clip(highs * (0.65 + 0.55 * m), 0.0, 1.0)),
            color=float(np.clip(f.centroid, 0.0, 1.0)),
            strike=float(np.clip(max(strike, self._strike_energy), 0.0, 1.0)),
            beat=float(np.clip(max(beat, self._beat_energy), 0.0, 1.0)),
            ascension=float(np.clip(max(ascension, self._ascension_energy), 0.0, 1.0)),
            tempo_bpm=tempo_bpm,
            beat_phase=beat_phase,
            bar_phase=bar_phase,
            beat_confidence=float(np.clip(self._beat_confidence, 0.0, 1.0)),
            section_energy=float(np.clip(self._section_energy, 0.0, 1.0)),
            drop=float(np.clip(max(drop, self._drop_energy), 0.0, 1.0)),
        )


__all__ = ["MusicalSignals", "MusicalEventMapper"]

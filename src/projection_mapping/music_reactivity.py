from __future__ import annotations

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


_REACTIVITY = {
    "smooth": dict(gain=0.80, onset=0.72, beat=0.58, refractory=0.28, release=5.0),
    "balanced": dict(gain=1.00, onset=0.62, beat=0.50, refractory=0.20, release=6.5),
    "punchy": dict(gain=1.15, onset=0.54, beat=0.42, refractory=0.16, release=8.0),
    "chaotic": dict(gain=1.35, onset=0.42, beat=0.34, refractory=0.10, release=10.0),
}


def _smoothstep(lo: float, hi: float, x: float) -> float:
    if hi <= lo:
        return float(x >= hi)
    t = float(np.clip((x - lo) / (hi - lo), 0.0, 1.0))
    return t * t * (3.0 - 2.0 * t)


class MusicalEventMapper:
    """Turn noisy spectral features into continuous musical controls + sparse events.

    Small fluctuations affect only slow/continuous modulation. Strong visible events are
    gated by onset, RMS and bass evidence plus a refractory period, avoiding the common
    'everything flickers all the time' audio-visualizer failure mode.
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
        self._last_strike = -999.0
        self._last_beat = -999.0
        self._last_ascension = -999.0
        self._strike_energy = 0.0
        self._beat_energy = 0.0
        self._ascension_energy = 0.0
        self._bass_slow = 0.0

    def update(self, f: AudioFeatures, now: float) -> MusicalSignals:
        if self._last_t is None:
            dt = 1.0 / 60.0
        else:
            dt = float(np.clip(now - self._last_t, 1e-4, 0.2))
        self._last_t = now

        p = self.params
        gain = float(p["gain"])
        rms = _smoothstep(0.10, 0.72, f.rms * gain)
        bass = _smoothstep(0.13, 0.75, f.bass * gain)
        mids = _smoothstep(0.12, 0.78, f.mid * gain)
        # Highs are deliberately gated. Below the gate they do nothing visible.
        highs = _smoothstep(0.30, 0.85, f.treble * gain) if f.treble >= 0.28 else 0.0

        # Track a slower bass envelope and use positive excess as kick evidence.
        slow_alpha = 1.0 - math.exp(-dt / 0.22)
        self._bass_slow += slow_alpha * (float(f.bass) - self._bass_slow)
        bass_punch = max(float(f.bass) - self._bass_slow, 0.0)

        strike = 0.0
        onset_gate = float(p["onset"])
        refractory = float(p["refractory"])
        if (
            f.onset >= onset_gate
            and f.rms >= 0.14
            and now - self._last_strike >= refractory
        ):
            strike = _smoothstep(onset_gate, 0.96, f.onset)
            self._strike_energy = max(self._strike_energy, strike)
            self._last_strike = now

        beat = 0.0
        beat_gate = float(p["beat"])
        beat_evidence = 0.72 * float(f.bass) + 0.28 * min(bass_punch * 5.0, 1.0)
        if (
            beat_evidence >= beat_gate
            and f.rms >= 0.12
            and now - self._last_beat >= max(0.12, refractory * 0.8)
        ):
            beat = _smoothstep(beat_gate, 0.95, beat_evidence)
            self._beat_energy = max(self._beat_energy, beat)
            self._last_beat = now

        ascension = 0.0
        if (
            f.onset >= max(0.80, onset_gate + 0.16)
            and f.bass >= max(0.52, beat_gate)
            and f.rms >= 0.24
            and now - self._last_ascension >= 0.65
        ):
            ascension = 1.0
            self._ascension_energy = 1.0
            self._last_ascension = now

        release = float(p["release"])
        self._strike_energy *= math.exp(-dt * release)
        self._beat_energy *= math.exp(-dt * release * 0.75)
        self._ascension_energy *= math.exp(-dt * 2.4)

        # Madness increases continuous range and event tail, not raw noise sensitivity.
        m = self.madness
        return MusicalSignals(
            loudness=float(np.clip(rms * (0.80 + 0.35 * m), 0.0, 1.0)),
            bass=float(np.clip(bass * (0.85 + 0.30 * m), 0.0, 1.0)),
            mids=float(np.clip(mids * (0.85 + 0.35 * m), 0.0, 1.0)),
            highs=float(np.clip(highs * (0.70 + 0.55 * m), 0.0, 1.0)),
            color=float(np.clip(f.centroid, 0.0, 1.0)),
            strike=float(np.clip(max(strike, self._strike_energy), 0.0, 1.0)),
            beat=float(np.clip(max(beat, self._beat_energy), 0.0, 1.0)),
            ascension=float(np.clip(max(ascension, self._ascension_energy), 0.0, 1.0)),
        )


__all__ = ["MusicalSignals", "MusicalEventMapper"]

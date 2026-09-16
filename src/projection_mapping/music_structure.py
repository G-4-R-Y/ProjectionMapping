from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import math

import numpy as np

from .music_reactivity import MusicalSignals


@dataclass(frozen=True)
class MusicStructure:
    section: str
    confidence: float
    phrase_phase: float
    energy_fast: float
    energy_slow: float
    energy_slope: float
    bars_seen: int


class MusicStructureTracker:
    """Transparent multi-second musical-structure heuristic for realtime choreography.

    This is intentionally not sold as semantic song understanding. It supplies stable section
    evidence (breakdown/build/drop/release/steady) from dynamics + the existing beat/bar clock so
    visuals can change at musical times without a heavyweight model or per-frame randomness.
    """

    def __init__(self, *, bars_per_phrase: int = 8, minimum_dwell: float = 2.0) -> None:
        self.bars_per_phrase = max(1, int(bars_per_phrase))
        self.minimum_dwell = float(max(minimum_dwell, 0.25))
        self._last_t: float | None = None
        self._fast = 0.0
        self._slow = 0.0
        self._section = "steady"
        self._section_since = -999.0
        self._drop_time = -999.0
        self._bars_seen = 0
        self._last_bar_phase: float | None = None
        self._energy_history: deque[tuple[float, float]] = deque(maxlen=240)

    def _phrase_phase(self, s: MusicalSignals) -> float:
        phase = float(np.clip(s.bar_phase, 0.0, 0.999999))
        if s.beat_confidence >= 0.18:
            if self._last_bar_phase is not None and self._last_bar_phase > 0.78 and phase < 0.22:
                self._bars_seen += 1
            self._last_bar_phase = phase
        return float(((self._bars_seen % self.bars_per_phrase) + phase) / self.bars_per_phrase)

    def update(self, s: MusicalSignals, now: float) -> MusicStructure:
        if self._last_t is None:
            dt = 1.0 / 60.0
        else:
            dt = float(np.clip(now - self._last_t, 1e-4, 0.25))
        self._last_t = float(now)

        energy = float(np.clip(0.66 * s.loudness + 0.24 * s.bass + 0.10 * s.mids, 0.0, 1.0))
        fast_alpha = 1.0 - math.exp(-dt / 0.85)
        slow_alpha = 1.0 - math.exp(-dt / 6.0)
        self._fast += fast_alpha * (energy - self._fast)
        self._slow += slow_alpha * (energy - self._slow)
        slope = self._fast - self._slow
        self._energy_history.append((float(now), energy))
        phrase_phase = self._phrase_phase(s)

        candidate = "steady"
        confidence = 0.35
        if s.drop >= 0.58:
            candidate = "drop"
            confidence = float(np.clip(0.55 + s.drop * 0.45, 0.0, 1.0))
            self._drop_time = float(now)
        elif now - self._drop_time <= 3.5 and self._fast >= max(self._slow * 0.85, 0.30):
            candidate = "release"
            confidence = float(np.clip(0.55 + self._fast * 0.35, 0.0, 1.0))
        elif self._slow < 0.26 and self._fast < 0.32:
            candidate = "breakdown"
            confidence = float(np.clip(0.58 + (0.32 - self._fast), 0.0, 1.0))
        elif slope >= 0.085 and self._fast >= 0.32:
            candidate = "build"
            confidence = float(np.clip(0.52 + slope * 2.4 + s.strike * 0.12, 0.0, 1.0))
        elif self._fast >= 0.52:
            candidate = "steady"
            confidence = float(np.clip(0.52 + self._fast * 0.30, 0.0, 1.0))

        # Drops override dwell. Other labels need persistence so choreography does not chatter.
        if candidate == "drop":
            if self._section != "drop":
                self._section_since = float(now)
            self._section = "drop"
        elif candidate != self._section and now - self._section_since >= self.minimum_dwell:
            self._section = candidate
            self._section_since = float(now)

        return MusicStructure(
            section=self._section,
            confidence=confidence,
            phrase_phase=phrase_phase,
            energy_fast=float(np.clip(self._fast, 0.0, 1.0)),
            energy_slow=float(np.clip(self._slow, 0.0, 1.0)),
            energy_slope=float(np.clip(slope, -1.0, 1.0)),
            bars_seen=self._bars_seen,
        )


class ParticleJourneyController:
    """Select particle choreography at section boundaries without resetting particle state."""

    _SECTION_BANK = {
        "breakdown": "constellation_bloom",
        "build": "vortex_gate",
        "drop": "dual_comet",
        "release": "orbit_reactor",
        "steady": "orbit_reactor",
    }

    def __init__(self, *, initial: str = "orbit_reactor", minimum_dwell: float = 6.0) -> None:
        self.bank = initial
        self.minimum_dwell = float(max(minimum_dwell, 1.0))
        self._last_switch = -999.0

    def update(self, structure: MusicStructure, now: float) -> str:
        desired = self._SECTION_BANK.get(structure.section, "orbit_reactor")
        urgent = structure.section == "drop" and desired != self.bank
        phrase_edge = structure.phrase_phase < 0.06 or structure.phrase_phase > 0.94
        if desired != self.bank and (
            urgent
            or (now - self._last_switch >= self.minimum_dwell and phrase_edge and structure.confidence >= 0.48)
        ):
            self.bank = desired
            self._last_switch = float(now)
        return self.bank


__all__ = ["MusicStructure", "MusicStructureTracker", "ParticleJourneyController"]

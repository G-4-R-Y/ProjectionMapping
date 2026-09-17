from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from typing import ClassVar

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
    """Select choreography at section/phrase boundaries without resetting particle state."""

    _SECTION_BANK: ClassVar[dict[str, str]] = {
        "breakdown": "nebula_bloom",
        "build": "polar_gate",
        "drop": "techno_lattice",
        "release": "reactor_bloom",
        "steady": "helix_fountain",
    }

    def __init__(self, *, initial: str = "helix_fountain", minimum_dwell: float = 6.0) -> None:
        self.bank = initial
        self.minimum_dwell = float(max(minimum_dwell, 1.0))
        self._last_switch = -999.0

    def update(self, structure: MusicStructure, now: float) -> str:
        desired = self._SECTION_BANK.get(structure.section, "reactor_bloom")
        urgent = structure.section == "drop" and desired != self.bank
        phrase_edge = structure.phrase_phase < 0.06 or structure.phrase_phase > 0.94
        if desired != self.bank and (
            urgent
            or (
                now - self._last_switch >= self.minimum_dwell
                and phrase_edge
                and structure.confidence >= 0.48
            )
        ):
            self.bank = desired
            self._last_switch = float(now)
        return self.bank


@dataclass(frozen=True)
class JourneyTransition:
    """A smooth, deterministic transition between two Journey bank identities."""

    source_bank: str
    target_bank: str
    mix: float

    @property
    def active(self) -> bool:
        return self.source_bank != self.target_bank and self.mix < 1.0


class ParticleJourneyCrossfade:
    """Turn discrete Journey bank changes into a time-based smoothstep transition.

    The Journey controller already decides *when* a musical change is allowed. This class only
    shapes that accepted change, so phrase/drop timing remains owned by ``ParticleJourneyController``.
    """

    def __init__(self, *, initial: str, duration: float = 2.4) -> None:
        self.source_bank = initial
        self.target_bank = initial
        self.duration = float(max(duration, 0.05))
        self._transition_start: float | None = None

    def update(self, bank: str, now: float) -> JourneyTransition:
        now = float(now)
        if bank != self.target_bank:
            # Journey changes are normally sparse. If a new change arrives mid-transition, retain
            # whichever endpoint currently dominates rather than jumping back to stale state.
            if self._transition_start is not None:
                raw = float(np.clip((now - self._transition_start) / self.duration, 0.0, 1.0))
                dominant = self.target_bank if raw >= 0.5 else self.source_bank
            else:
                dominant = self.target_bank
            self.source_bank = dominant
            self.target_bank = bank
            self._transition_start = now

        if self._transition_start is None or self.source_bank == self.target_bank:
            return JourneyTransition(self.target_bank, self.target_bank, 1.0)

        raw = float(np.clip((now - self._transition_start) / self.duration, 0.0, 1.0))
        mix = raw * raw * (3.0 - 2.0 * raw)
        if raw >= 1.0:
            self.source_bank = self.target_bank
            self._transition_start = None
            return JourneyTransition(self.target_bank, self.target_bank, 1.0)
        return JourneyTransition(self.source_bank, self.target_bank, mix)


__all__ = [
    "JourneyTransition",
    "MusicStructure",
    "MusicStructureTracker",
    "ParticleJourneyController",
    "ParticleJourneyCrossfade",
]

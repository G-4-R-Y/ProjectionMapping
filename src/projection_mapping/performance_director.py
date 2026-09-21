from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from .music_reactivity import MusicalSignals
from .music_structure import MusicStructure
from .particle_choreography import BANKS
from .shader_scenes import SHADER_SCENE_PRESETS


@dataclass(frozen=True)
class PerformanceCue:
    """A coordinated shader + particle identity used by the live director."""

    shader_preset: str
    particle_bank: str
    madness: float
    shader_mix: float = 0.56


@dataclass(frozen=True)
class PerformanceMacro:
    """Smoothed shared macro values consumed by shader and particle renderers."""

    energy: float
    madness: float
    shader_chaos: float
    shader_intensity: float
    palette_rate: float
    particle_emission: float
    particle_turbulence: float
    particle_bloom: float
    field_force: float
    composite_mix: float


@dataclass(frozen=True)
class PerformanceState:
    source_cue: str
    target_cue: str
    mix: float
    macro: PerformanceMacro

    @property
    def active_transition(self) -> bool:
        return self.source_cue != self.target_cue and self.mix < 1.0


PERFORMANCE_CUES: dict[str, PerformanceCue] = {
    "liquid_intro": PerformanceCue("liquid_neon", "nebula_bloom", 0.22, 0.48),
    "membrane_drift": PerformanceCue("membrane_flux", "cosmic_roam", 0.34, 0.54),
    "data_build": PerformanceCue("data_tide", "techno_lattice", 0.52, 0.50),
    "mercury_rise": PerformanceCue("mercury_bloom", "lissajous_storm", 0.58, 0.52),
    "cathedral_release": PerformanceCue("cathedral_dream", "cathedral_rain", 0.38, 0.60),
    "reactor_release": PerformanceCue("liquid_neon", "reactor_bloom", 0.46, 0.50),
    "singularity_drop": PerformanceCue("singularity_choir", "supernova_nebula", 0.88, 0.44),
    "afterglow": PerformanceCue("oil_afterglow", "constellation_bloom", 0.28, 0.62),
}

PERFORMANCE_JOURNEYS: dict[str, tuple[str, ...]] = {
    "liquid_arc": (
        "liquid_intro",
        "membrane_drift",
        "data_build",
        "singularity_drop",
        "reactor_release",
        "afterglow",
    ),
    "neon_ritual": (
        "cathedral_release",
        "mercury_rise",
        "data_build",
        "singularity_drop",
        "reactor_release",
        "liquid_intro",
    ),
    "cosmic_rave": (
        "membrane_drift",
        "mercury_rise",
        "data_build",
        "singularity_drop",
        "afterglow",
        "liquid_intro",
    ),
}

_SECTION_CUE = {
    "breakdown": "liquid_intro",
    "build": "data_build",
    "drop": "singularity_drop",
    "release": "reactor_release",
}


def _smoothstep(x: float) -> float:
    x = float(np.clip(x, 0.0, 1.0))
    return x * x * (3.0 - 2.0 * x)


class PerformanceDirector:
    """Coordinate shader presets and particle banks from one musical/timed state machine.

    Timed mode advances through a curated journey at a fixed maximum cue duration.
    Musical mode follows detected breakdown/build/drop/release identities.
    Hybrid mode keeps the curated journey but accepts confident section changes and urgent drops.

    The director only chooses identities and continuous macro values. It never owns GPU state, so
    shader/particle renderers stay reusable and persistent simulations do not reset on cue changes.
    """

    def __init__(
        self,
        *,
        journey: str = "liquid_arc",
        mode: str = "hybrid",
        base_madness: float = 0.45,
        cue_seconds: float = 24.0,
        transition_seconds: float = 3.0,
        minimum_dwell: float = 5.0,
    ) -> None:
        if journey not in PERFORMANCE_JOURNEYS:
            raise ValueError(f"unknown performance journey: {journey}")
        if mode not in {"timed", "musical", "hybrid"}:
            raise ValueError(f"unknown performance director mode: {mode}")
        self.journey = journey
        self.mode = mode
        self.base_madness = float(np.clip(base_madness, 0.0, 1.0))
        self.cue_seconds = float(max(cue_seconds, 2.0))
        self.transition_seconds = float(max(transition_seconds, 0.05))
        self.minimum_dwell = float(max(minimum_dwell, 1.0))

        sequence = PERFORMANCE_JOURNEYS[journey]
        self._index = 0
        self._source = sequence[0]
        self._target = sequence[0]
        self._transition_start: float | None = None
        self._last_switch = -999.0
        self._last_phrase = -1
        self._last_t: float | None = None
        self._macro = self.base_madness

    @property
    def current_cue(self) -> str:
        return self._target

    def _sequence_next(self) -> str:
        sequence = PERFORMANCE_JOURNEYS[self.journey]
        try:
            current_index = sequence.index(self._target)
        except ValueError:
            current_index = self._index
        self._index = (current_index + 1) % len(sequence)
        return sequence[self._index]

    def _accept(self, cue: str, now: float, *, urgent: bool = False) -> None:
        if cue not in PERFORMANCE_CUES or cue == self._target:
            return
        if not urgent and now - self._last_switch < self.minimum_dwell:
            return

        if self._transition_start is not None:
            raw = float(np.clip((now - self._transition_start) / self.transition_seconds, 0.0, 1.0))
            dominant = self._target if raw >= 0.5 else self._source
        else:
            dominant = self._target
        self._source = dominant
        self._target = cue
        self._transition_start = float(now)
        self._last_switch = float(now)

    def _select_cue(self, structure: MusicStructure, signals: MusicalSignals, now: float) -> None:
        phrase = int(structure.bars_seen // 8)
        new_phrase = phrase != self._last_phrase
        if new_phrase:
            self._last_phrase = phrase

        if self.mode == "timed":
            if now - self._last_switch >= self.cue_seconds:
                self._accept(self._sequence_next(), now)
            return

        section_cue = _SECTION_CUE.get(structure.section)
        urgent_drop = structure.section == "drop" and signals.drop >= 0.52
        if urgent_drop:
            self._accept("singularity_drop", now, urgent=True)
            return

        if self.mode == "musical":
            if section_cue and structure.confidence >= 0.48:
                self._accept(section_cue, now)
            elif new_phrase and now - self._last_switch >= self.cue_seconds:
                self._accept(self._sequence_next(), now)
            return

        if section_cue and structure.confidence >= 0.58:
            self._accept(section_cue, now)
        elif (
            (new_phrase and now - self._last_switch >= self.minimum_dwell)
            or now - self._last_switch >= self.cue_seconds
        ):
            self._accept(self._sequence_next(), now)

    def _transition_mix(self, now: float) -> float:
        if self._transition_start is None or self._source == self._target:
            self._source = self._target
            return 1.0
        raw = float(np.clip((now - self._transition_start) / self.transition_seconds, 0.0, 1.0))
        if raw >= 1.0:
            self._source = self._target
            self._transition_start = None
            return 1.0
        return _smoothstep(raw)

    def _macro_state(
        self,
        source: PerformanceCue,
        target: PerformanceCue,
        mix: float,
        signals: MusicalSignals,
        now: float,
    ) -> PerformanceMacro:
        if self._last_t is None:
            dt = 1.0 / 60.0
        else:
            dt = float(np.clip(now - self._last_t, 1e-4, 0.25))
        self._last_t = float(now)

        cue_madness = source.madness + (target.madness - source.madness) * mix
        audio_energy = float(
            np.clip(
                0.44 * signals.section_energy
                + 0.18 * signals.loudness
                + 0.14 * signals.bass
                + 0.10 * signals.strike
                + 0.14 * signals.drop,
                0.0,
                1.0,
            )
        )
        target_macro = float(
            np.clip(
                self.base_madness * 0.34 + cue_madness * 0.50 + audio_energy * 0.42,
                0.0,
                1.0,
            )
        )
        tau = 0.14 if target_macro > self._macro else 0.72
        alpha = 1.0 - math.exp(-dt / tau)
        self._macro += alpha * (target_macro - self._macro)
        m = float(np.clip(self._macro, 0.0, 1.0))

        shader_mix = source.shader_mix + (target.shader_mix - source.shader_mix) * mix
        return PerformanceMacro(
            energy=audio_energy,
            madness=m,
            shader_chaos=0.78 + 1.42 * m + 0.32 * signals.drop,
            shader_intensity=0.78 + 0.68 * m + 0.28 * signals.loudness,
            palette_rate=0.008 + 0.060 * m + 0.028 * signals.highs,
            particle_emission=0.72 + 1.18 * m + 0.28 * signals.drop,
            particle_turbulence=0.76 + 0.82 * m + 0.22 * signals.highs,
            particle_bloom=0.82 + 0.62 * m + 0.20 * signals.strike,
            field_force=0.78 + 0.72 * m + 0.32 * signals.bass,
            composite_mix=float(np.clip(shader_mix * (0.78 + 0.32 * m), 0.0, 1.0)),
        )

    def update(
        self,
        structure: MusicStructure,
        signals: MusicalSignals,
        now: float,
    ) -> PerformanceState:
        now = float(now)
        if self._last_switch < -900.0:
            self._last_switch = now

        self._select_cue(structure, signals, now)
        mix = self._transition_mix(now)
        source = PERFORMANCE_CUES[self._source]
        target = PERFORMANCE_CUES[self._target]
        macro = self._macro_state(source, target, mix, signals, now)
        return PerformanceState(self._source, self._target, mix, macro)


def validate_performance_catalog() -> None:
    for name, cue in PERFORMANCE_CUES.items():
        if cue.shader_preset not in SHADER_SCENE_PRESETS:
            raise ValueError(f"cue {name!r} references unknown shader preset {cue.shader_preset!r}")
        if cue.particle_bank not in BANKS:
            raise ValueError(f"cue {name!r} references unknown particle bank {cue.particle_bank!r}")
    for name, journey in PERFORMANCE_JOURNEYS.items():
        if not journey:
            raise ValueError(f"journey {name!r} is empty")
        missing = [cue for cue in journey if cue not in PERFORMANCE_CUES]
        if missing:
            raise ValueError(f"journey {name!r} references unknown cues: {missing}")


validate_performance_catalog()


__all__ = [
    "PERFORMANCE_CUES",
    "PERFORMANCE_JOURNEYS",
    "PerformanceCue",
    "PerformanceDirector",
    "PerformanceMacro",
    "PerformanceState",
    "validate_performance_catalog",
]

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from .gpu_particles import ParticleEmitter
from .music_reactivity import MusicalSignals


BANKS = ("orbit_reactor", "dual_comet", "cathedral_rain", "vortex_gate", "constellation_bloom")


@dataclass(frozen=True)
class ParticleChoreography:
    emitters: tuple[ParticleEmitter, ...]
    emission_rate: float
    turbulence: float
    drag: float
    feedback: float
    bloom: float
    palette: str


def _phase_angle(s: MusicalSignals, t: float, multiplier: float = 1.0) -> float:
    if s.beat_confidence > 0.18:
        return (s.bar_phase * math.tau * 4.0) * multiplier
    return t * 0.7 * multiplier


def choreography(bank: str, s: MusicalSignals, t: float, madness: float = 0.45) -> ParticleChoreography:
    if bank not in BANKS:
        raise ValueError(f"unknown particle choreography bank: {bank}")
    m = float(np.clip(madness, 0.0, 1.0))
    angle = _phase_angle(s, t)
    beat = float(np.clip(s.beat, 0.0, 1.0))
    strike = float(np.clip(s.strike, 0.0, 1.0))
    drop = float(np.clip(s.drop, 0.0, 1.0))
    loud = float(np.clip(s.loudness, 0.0, 1.0))

    if bank == "orbit_reactor":
        radius = 0.16 + 0.12 * s.bass + 0.04 * math.sin(angle * 0.5)
        emitters = []
        for i in range(4):
            a = angle + i * math.pi * 0.5
            x = 0.5 + math.cos(a) * radius
            y = 0.5 + math.sin(a) * radius * 0.78
            vx = -math.sin(a) * (0.24 + 0.20 * s.mids)
            vy = math.cos(a) * (0.24 + 0.20 * s.mids)
            emitters.append(ParticleEmitter(x, y, vx, vy, 0.55 + 0.45 * loud, (i / 4.0 + s.color * 0.22) % 1.0, 0.010 + 0.012 * beat))
        return ParticleChoreography(tuple(emitters), 4200 + 7600 * loud + 5200 * drop, 0.18 + 0.24 * m, 1.15, 0.935, 1.15, "cyber")

    if bank == "dual_comet":
        swing = 0.22 + 0.08 * s.bass
        x1 = 0.5 + math.sin(angle) * swing
        x2 = 0.5 - math.sin(angle) * swing
        y1 = 0.46 + math.cos(angle * 0.5) * 0.18
        y2 = 0.54 - math.cos(angle * 0.5) * 0.18
        speed = 0.40 + 0.55 * s.mids + 0.45 * strike
        emitters = (
            ParticleEmitter(x1, y1, math.cos(angle) * speed, math.sin(angle) * speed, 0.65 + 0.35 * loud, 0.04 + s.color * 0.12, 0.018),
            ParticleEmitter(x2, y2, -math.cos(angle) * speed, -math.sin(angle) * speed, 0.65 + 0.35 * loud, 0.62 + s.color * 0.12, 0.018),
        )
        return ParticleChoreography(emitters, 5200 + 9000 * loud + 8000 * strike, 0.10 + 0.20 * m, 0.92, 0.945, 1.30, "prismatic")

    if bank == "cathedral_rain":
        emitters = []
        columns = 6
        for i in range(columns):
            x = (i + 0.5) / columns
            pulse = 0.55 + 0.45 * math.sin(angle + i * 1.7)
            emitters.append(ParticleEmitter(x, 0.05, 0.0, 0.22 + 0.34 * s.bass, 0.30 + 0.55 * loud * pulse, 0.45 + i * 0.025, 0.008))
        return ParticleChoreography(tuple(emitters), 3500 + 6500 * loud + 4500 * beat, 0.06 + 0.12 * m, 0.72, 0.955, 0.95, "bio")

    if bank == "vortex_gate":
        emitters = []
        radius = 0.27 + 0.04 * s.bass
        for i in range(6):
            a = angle * 0.45 + i * math.tau / 6.0
            x = 0.5 + math.cos(a) * radius
            y = 0.5 + math.sin(a) * radius
            tangent = 0.36 + 0.32 * s.mids + 0.30 * drop
            emitters.append(ParticleEmitter(x, y, -math.sin(a) * tangent, math.cos(a) * tangent, 0.44 + 0.48 * loud, (0.78 + i * 0.045) % 1.0, 0.014))
        return ParticleChoreography(tuple(emitters), 4800 + 7600 * loud + 10000 * drop, 0.30 + 0.34 * m, 0.88, 0.948, 1.25, "solar")

    # constellation_bloom: deliberately sparse until meaningful events happen.
    emitters = []
    count = 3 if loud < 0.45 else 5
    for i in range(count):
        a = i * math.tau / max(count, 1) + angle * 0.12
        radius = 0.22 + 0.08 * math.sin(angle * 0.25 + i)
        emitters.append(ParticleEmitter(0.5 + math.cos(a) * radius, 0.5 + math.sin(a) * radius, 0.02 * math.cos(a), 0.02 * math.sin(a), 0.22 + 0.55 * loud + 0.4 * strike, (s.color + i / max(count, 1)) % 1.0, 0.006 + 0.016 * strike))
    return ParticleChoreography(tuple(emitters), 900 + 3200 * loud + 9000 * strike + 12000 * drop, 0.12 + 0.24 * m, 1.32, 0.965, 1.35, "cyber")


__all__ = ["BANKS", "ParticleChoreography", "choreography"]

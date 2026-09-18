from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .gpu_particles import ParticleEmitter
from .music_reactivity import MusicalSignals

BANKS = (
    "orbit_reactor",
    "dual_comet",
    "cathedral_rain",
    "vortex_gate",
    "constellation_bloom",
    "reactor_bloom",
    "polar_gate",
    "ritual_rain",
    "helix_fountain",
    "nebula_bloom",
    "techno_lattice",
    "lissajous_storm",
    "singularity_crown",
    "prism_shards",
    "cosmic_roam",
    "binary_star",
    "event_horizon_drift",
    "accretion_storm",
    "supernova_nebula",
)


@dataclass(frozen=True)
class ParticleChoreography:
    emitters: tuple[ParticleEmitter, ...]
    emission_rate: float
    turbulence: float
    drag: float
    feedback: float
    bloom: float
    palette: str
    material: str = "plasma"
    field_mode: str = "flow"
    field_strength: float = 1.0
    field_scale: float = 1.0
    field_spin: float = 1.0
    well_strength: float = 0.0
    nebula_mix: float = 0.0


def _lerp(a: float, b: float, mix: float) -> float:
    return a + (b - a) * mix


def _blend_hue(a: float, b: float, mix: float) -> float:
    delta = (b - a + 0.5) % 1.0 - 0.5
    return (a + delta * mix) % 1.0


def blend_choreographies(
    source: ParticleChoreography,
    target: ParticleChoreography,
    mix: float,
) -> ParticleChoreography:
    """Morph two banks without resetting the persistent GPU particle simulation.

    The particle shader supports eight emitters, so emitters are paired by stable index. Missing
    endpoints fade in/out in place instead of concatenating two banks and silently truncating one.
    """

    m = float(np.clip(mix, 0.0, 1.0))
    if m <= 0.0:
        return source
    if m >= 1.0:
        return target
    count = min(max(len(source.emitters), len(target.emitters)), 8)
    emitters: list[ParticleEmitter] = []
    for index in range(count):
        a = source.emitters[index] if index < len(source.emitters) else target.emitters[index]
        b = target.emitters[index] if index < len(target.emitters) else source.emitters[index]
        a_energy = a.energy if index < len(source.emitters) else 0.0
        b_energy = b.energy if index < len(target.emitters) else 0.0
        emitters.append(
            ParticleEmitter(
                _lerp(a.x, b.x, m),
                _lerp(a.y, b.y, m),
                _lerp(a.vx, b.vx, m),
                _lerp(a.vy, b.vy, m),
                _lerp(a_energy, b_energy, m),
                _blend_hue(a.hue, b.hue, m),
                _lerp(a.radius, b.radius, m),
            )
        )

    # Palette/material are global shader state, not per-emitter attributes. Switch them at the
    # midpoint while geometry, energy and the persistent feedback field continue to morph.
    style = target if m >= 0.5 else source
    return ParticleChoreography(
        tuple(emitters),
        _lerp(source.emission_rate, target.emission_rate, m),
        _lerp(source.turbulence, target.turbulence, m),
        _lerp(source.drag, target.drag, m),
        _lerp(source.feedback, target.feedback, m),
        _lerp(source.bloom, target.bloom, m),
        style.palette,
        style.material,
        style.field_mode,
        _lerp(source.field_strength, target.field_strength, m),
        _lerp(source.field_scale, target.field_scale, m),
        _lerp(source.field_spin, target.field_spin, m),
        _lerp(source.well_strength, target.well_strength, m),
        _lerp(source.nebula_mix, target.nebula_mix, m),
    )


def _phase_angle(s: MusicalSignals, t: float, multiplier: float = 1.0) -> float:
    if s.beat_confidence > 0.18:
        return (s.bar_phase * math.tau * 4.0) * multiplier
    return t * 0.7 * multiplier


def choreography(
    bank: str,
    s: MusicalSignals,
    t: float,
    madness: float = 0.45,
) -> ParticleChoreography:
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
            emitters.append(
                ParticleEmitter(
                    x,
                    y,
                    vx,
                    vy,
                    0.55 + 0.45 * loud,
                    (i / 4.0 + s.color * 0.22) % 1.0,
                    0.010 + 0.012 * beat,
                )
            )
        return ParticleChoreography(
            tuple(emitters),
            4200 + 7600 * loud + 5200 * drop,
            0.18 + 0.24 * m,
            1.15,
            0.935,
            1.15,
            "cyber",
            "plasma",
        )

    if bank == "dual_comet":
        swing = 0.22 + 0.08 * s.bass
        x1 = 0.5 + math.sin(angle) * swing
        x2 = 0.5 - math.sin(angle) * swing
        y1 = 0.46 + math.cos(angle * 0.5) * 0.18
        y2 = 0.54 - math.cos(angle * 0.5) * 0.18
        speed = 0.40 + 0.55 * s.mids + 0.45 * strike
        emitters = (
            ParticleEmitter(
                x1,
                y1,
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                0.65 + 0.35 * loud,
                0.04 + s.color * 0.12,
                0.018,
            ),
            ParticleEmitter(
                x2,
                y2,
                -math.cos(angle) * speed,
                -math.sin(angle) * speed,
                0.65 + 0.35 * loud,
                0.62 + s.color * 0.12,
                0.018,
            ),
        )
        return ParticleChoreography(
            emitters,
            5200 + 9000 * loud + 8000 * strike,
            0.10 + 0.20 * m,
            0.92,
            0.945,
            1.30,
            "prismatic",
            "comet",
        )

    if bank == "cathedral_rain":
        emitters = []
        columns = 6
        for i in range(columns):
            x = (i + 0.5) / columns
            pulse = 0.55 + 0.45 * math.sin(angle + i * 1.7)
            emitters.append(
                ParticleEmitter(
                    x,
                    0.05,
                    0.0,
                    0.22 + 0.34 * s.bass,
                    0.30 + 0.55 * loud * pulse,
                    0.45 + i * 0.025,
                    0.008,
                )
            )
        return ParticleChoreography(
            tuple(emitters),
            3500 + 6500 * loud + 4500 * beat,
            0.06 + 0.12 * m,
            0.72,
            0.955,
            0.95,
            "bio",
            "spark",
        )

    if bank == "vortex_gate":
        emitters = []
        radius = 0.27 + 0.04 * s.bass
        for i in range(6):
            a = angle * 0.45 + i * math.tau / 6.0
            x = 0.5 + math.cos(a) * radius
            y = 0.5 + math.sin(a) * radius
            tangent = 0.36 + 0.32 * s.mids + 0.30 * drop
            emitters.append(
                ParticleEmitter(
                    x,
                    y,
                    -math.sin(a) * tangent,
                    math.cos(a) * tangent,
                    0.44 + 0.48 * loud,
                    (0.78 + i * 0.045) % 1.0,
                    0.014,
                )
            )
        return ParticleChoreography(
            tuple(emitters),
            4800 + 7600 * loud + 10000 * drop,
            0.30 + 0.34 * m,
            0.88,
            0.948,
            1.25,
            "solar",
            "comet",
        )

    if bank == "constellation_bloom":
        emitters = []
        count = 3 if loud < 0.45 else 5
        for i in range(count):
            a = i * math.tau / max(count, 1) + angle * 0.12
            radius = 0.22 + 0.08 * math.sin(angle * 0.25 + i)
            emitters.append(
                ParticleEmitter(
                    0.5 + math.cos(a) * radius,
                    0.5 + math.sin(a) * radius,
                    0.02 * math.cos(a),
                    0.02 * math.sin(a),
                    0.22 + 0.55 * loud + 0.4 * strike,
                    (s.color + i / max(count, 1)) % 1.0,
                    0.006 + 0.016 * strike,
                )
            )
        return ParticleChoreography(
            tuple(emitters),
            900 + 3200 * loud + 9000 * strike + 12000 * drop,
            0.12 + 0.24 * m,
            1.32,
            0.965,
            1.35,
            "cyber",
            "mote",
        )

    if bank == "reactor_bloom":
        emitters = []
        pulse = 0.04 + 0.13 * s.bass + 0.10 * beat
        for ring in range(2):
            count = 4
            radius = 0.08 + ring * 0.12 + pulse * (0.45 + 0.25 * ring)
            for i in range(count):
                a = angle * (0.42 + 0.16 * ring) + i * math.tau / count + ring * 0.39
                radial = 0.11 + 0.32 * drop + 0.18 * strike
                tangent = 0.19 + 0.21 * s.mids
                vx = math.cos(a) * radial - math.sin(a) * tangent
                vy = math.sin(a) * radial + math.cos(a) * tangent
                hue = (0.78 + ring * 0.16 + i * 0.045 + s.color * 0.10) % 1.0
                emitters.append(
                    ParticleEmitter(
                        0.5 + math.cos(a) * radius,
                        0.5 + math.sin(a) * radius,
                        vx,
                        vy,
                        0.52 + 0.48 * loud + 0.30 * drop,
                        hue,
                        0.010 + 0.010 * beat,
                    )
                )
        material = "shock_ring" if drop > 0.48 else "plasma"
        return ParticleChoreography(
            tuple(emitters[:8]),
            5200 + 9200 * loud + 15000 * drop,
            0.14 + 0.28 * m + 0.12 * strike,
            0.98,
            0.948,
            1.48,
            "cyber",
            material,
        )

    if bank == "polar_gate":
        emitters = []
        radius = 0.23 + 0.055 * s.bass + 0.08 * drop
        for i in range(8):
            a = angle * 0.31 + i * math.tau / 8.0
            direction = 1.0 if i % 2 == 0 else -1.0
            tangent = (0.24 + 0.38 * s.mids + 0.22 * beat) * direction
            radial = 0.03 + 0.28 * drop
            vx = -math.sin(a) * tangent + math.cos(a) * radial
            vy = math.cos(a) * tangent + math.sin(a) * radial
            emitters.append(
                ParticleEmitter(
                    0.5 + math.cos(a) * radius,
                    0.5 + math.sin(a) * radius,
                    vx,
                    vy,
                    0.45 + 0.50 * loud + 0.32 * drop,
                    (0.57 + i * 0.055 + s.color * 0.16) % 1.0,
                    0.010 + 0.010 * strike,
                )
            )
        return ParticleChoreography(
            tuple(emitters),
            4600 + 8400 * loud + 13000 * drop,
            0.22 + 0.30 * m,
            1.02,
            0.952,
            1.38,
            "prismatic",
            "comet",
        )

    if bank == "ritual_rain":
        emitters = []
        for i in range(8):
            x = (i + 0.5) / 8.0 + 0.018 * math.sin(angle * 0.25 + i)
            downward = 0.18 + 0.34 * s.bass + 0.18 * beat
            drift = 0.035 * math.sin(angle * 0.4 + i * 0.91)
            hue = (0.32 + i * 0.028 + s.color * 0.08) % 1.0
            energy = 0.22 + 0.50 * loud + (0.34 if i % 2 == 0 else 0.12) * strike
            emitters.append(
                ParticleEmitter(x, 0.03, drift, downward, energy, hue, 0.006 + 0.005 * beat)
            )
        return ParticleChoreography(
            tuple(emitters),
            2600 + 5600 * loud + 7000 * strike,
            0.035 + 0.10 * m,
            0.68,
            0.958,
            1.12,
            "bio",
            "spark",
        )

    if bank == "helix_fountain":
        emitters = []
        for i in range(8):
            lane = -1.0 if i % 2 == 0 else 1.0
            phase = angle * 0.46 + i * 0.73
            y = 0.72 - 0.055 * (i // 2) + 0.035 * math.sin(phase * 0.7)
            x = 0.5 + lane * (0.07 + 0.12 * math.sin(phase))
            vx = lane * (0.10 + 0.24 * s.mids) + 0.08 * math.cos(phase)
            vy = -(0.20 + 0.32 * s.bass + 0.18 * beat)
            hue = (0.80 + lane * 0.10 + i * 0.032 + s.color * 0.12) % 1.0
            emitters.append(
                ParticleEmitter(x, y, vx, vy, 0.42 + 0.55 * loud, hue, 0.009 + 0.006 * strike)
            )
        return ParticleChoreography(
            tuple(emitters),
            4000 + 7800 * loud + 8000 * beat,
            0.10 + 0.22 * m,
            0.86,
            0.950,
            1.30,
            "cyber",
            "comet",
        )

    if bank == "nebula_bloom":
        emitters = []
        for i in range(6):
            a = angle * 0.08 + i * math.tau / 6.0
            radius = 0.13 + 0.17 * (0.5 + 0.5 * math.sin(t * 0.11 + i * 1.27))
            vx = 0.025 * math.cos(a) + 0.055 * math.cos(a + math.pi * 0.5) * s.mids
            vy = 0.025 * math.sin(a) + 0.055 * math.sin(a + math.pi * 0.5) * s.mids
            emitters.append(
                ParticleEmitter(
                    0.5 + math.cos(a) * radius,
                    0.5 + math.sin(a) * radius,
                    vx,
                    vy,
                    0.16 + 0.42 * loud + 0.55 * drop,
                    (s.color + i * 0.14) % 1.0,
                    0.016 + 0.012 * drop,
                )
            )
        return ParticleChoreography(
            tuple(emitters),
            650 + 2300 * loud + 11000 * drop,
            0.08 + 0.16 * m,
            1.42,
            0.972,
            1.42,
            "prismatic",
            "mote",
            "nebula",
            1.05 + 0.25 * m,
            1.35,
            0.72,
            0.18 + 0.28 * s.bass,
            0.88 + 0.42 * s.mids,
        )

    if bank == "cosmic_roam":
        emitters = []
        for i in range(6):
            p = t * (0.045 + i * 0.003) + i * math.tau / 6.0
            x = 0.5 + 0.29 * math.sin(p * 1.7 + i * 0.31)
            y = 0.5 + 0.22 * math.sin(p * 2.3 + i * 0.83)
            vx = 0.035 * math.cos(p * 1.7) + 0.045 * s.mids * math.sin(p * 0.7 + i)
            vy = 0.035 * math.cos(p * 2.3) - 0.045 * s.mids * math.cos(p * 0.9 + i)
            emitters.append(
                ParticleEmitter(
                    x, y, vx, vy,
                    0.20 + 0.42 * loud + 0.32 * s.section_energy,
                    (s.color + i * 0.137) % 1.0,
                    0.010 + 0.008 * s.highs,
                )
            )
        return ParticleChoreography(
            tuple(emitters),
            1500 + 4600 * loud + 5000 * strike + 9000 * drop,
            0.34 + 0.38 * m + 0.18 * s.mids,
            0.78,
            0.970,
            1.38,
            "prismatic",
            "mote",
            "cosmic_roam",
            1.20 + 0.45 * s.section_energy,
            1.15 + 0.55 * s.mids,
            0.82 + 0.45 * s.highs,
            0.65 + 0.75 * s.bass + 0.55 * drop,
            0.90 + 0.55 * s.mids,
        )

    if bank == "binary_star":
        orbit = angle * 0.23 + t * 0.055
        radius = 0.16 + 0.035 * s.bass
        c1 = (0.5 + math.cos(orbit) * radius, 0.5 + math.sin(orbit) * radius)
        c2 = (0.5 - math.cos(orbit) * radius, 0.5 - math.sin(orbit) * radius)
        emitters = [
            ParticleEmitter(c1[0], c1[1], -math.sin(orbit) * 0.16, math.cos(orbit) * 0.16, 0.70 + 0.30 * loud, 0.08, 0.019),
            ParticleEmitter(c2[0], c2[1], math.sin(orbit) * 0.16, -math.cos(orbit) * 0.16, 0.70 + 0.30 * loud, 0.62, 0.019),
        ]
        for i in range(4):
            a = orbit + math.pi * 0.25 + i * math.pi * 0.5
            rr = 0.25 + 0.04 * math.sin(t * 0.13 + i)
            emitters.append(
                ParticleEmitter(
                    0.5 + math.cos(a) * rr,
                    0.5 + math.sin(a) * rr,
                    -math.sin(a) * (0.12 + 0.22 * s.mids),
                    math.cos(a) * (0.12 + 0.22 * s.mids),
                    0.28 + 0.42 * loud,
                    (0.15 + i * 0.18 + s.color * 0.08) % 1.0,
                    0.008,
                )
            )
        return ParticleChoreography(
            tuple(emitters),
            3600 + 7600 * loud + 9200 * strike,
            0.26 + 0.26 * m,
            0.62,
            0.965,
            1.46,
            "solar",
            "comet",
            "binary_star",
            1.25 + 0.55 * s.bass,
            1.0,
            0.92 + 0.35 * s.mids,
            1.15 + 1.05 * s.bass + 0.60 * drop,
            0.18,
        )

    if bank == "event_horizon_drift":
        emitters = []
        radius = 0.31 - 0.08 * s.bass + 0.025 * math.sin(t * 0.17)
        for i in range(8):
            a = angle * 0.11 + i * math.tau / 8.0
            inward = -(0.05 + 0.16 * s.bass + 0.26 * drop)
            tangent = (0.15 + 0.26 * s.mids) * (1.0 if i % 3 else -0.65)
            emitters.append(
                ParticleEmitter(
                    0.5 + math.cos(a) * radius,
                    0.5 + math.sin(a) * radius,
                    math.cos(a) * inward - math.sin(a) * tangent,
                    math.sin(a) * inward + math.cos(a) * tangent,
                    0.30 + 0.52 * loud + 0.32 * drop,
                    (0.72 + i * 0.045 + s.color * 0.10) % 1.0,
                    0.008 + 0.008 * strike,
                )
            )
        return ParticleChoreography(
            tuple(emitters),
            3100 + 7200 * loud + 14500 * drop,
            0.24 + 0.32 * m,
            0.52,
            0.969,
            1.50,
            "cyber",
            "shock_ring" if drop > 0.58 else "comet",
            "event_horizon",
            1.32 + 0.70 * s.bass + 0.55 * drop,
            1.0,
            1.08 + 0.55 * s.mids,
            1.25 + 1.20 * s.bass + 0.85 * drop,
            0.08,
        )

    if bank == "accretion_storm":
        emitters = []
        for i in range(8):
            a = t * 0.10 + i * math.tau / 8.0 + 0.16 * math.sin(t * 0.21 + i * 1.4)
            rr = 0.12 + 0.20 * ((i % 4) / 3.0) + 0.035 * math.sin(t * 0.16 + i)
            tangent = 0.22 + 0.42 * s.mids + 0.16 * strike
            inward = -(0.03 + 0.10 * s.bass + 0.16 * drop)
            emitters.append(
                ParticleEmitter(
                    0.5 + math.cos(a) * rr,
                    0.5 + math.sin(a) * rr * 0.72,
                    math.cos(a) * inward - math.sin(a) * tangent,
                    math.sin(a) * inward + math.cos(a) * tangent,
                    0.34 + 0.52 * loud + 0.30 * strike,
                    (0.02 + i * 0.107 + s.color * 0.12) % 1.0,
                    0.006 + 0.009 * strike,
                )
            )
        return ParticleChoreography(
            tuple(emitters),
            5200 + 9200 * loud + 11000 * strike + 12000 * drop,
            0.42 + 0.48 * m + 0.16 * s.highs,
            0.58,
            0.963,
            1.58,
            "prismatic",
            "comet",
            "event_horizon",
            1.55 + 0.55 * s.section_energy,
            1.25 + 0.45 * s.mids,
            1.35 + 0.55 * s.mids,
            0.95 + 1.10 * s.bass + 0.75 * drop,
            0.35 + 0.40 * s.highs,
        )

    if bank == "supernova_nebula":
        emitters = []
        burst = 0.10 + 0.65 * drop + 0.36 * strike
        for i in range(8):
            a = i * math.tau / 8.0 + t * 0.035
            rr = 0.035 + 0.10 * (i % 2) + 0.05 * s.bass
            radial = burst * (0.34 + 0.12 * (i % 3))
            emitters.append(
                ParticleEmitter(
                    0.5 + math.cos(a) * rr,
                    0.5 + math.sin(a) * rr,
                    math.cos(a) * radial,
                    math.sin(a) * radial,
                    0.18 + 0.42 * loud + 0.72 * drop,
                    (0.82 + i * 0.073 + s.color * 0.08) % 1.0,
                    0.012 + 0.018 * drop,
                )
            )
        return ParticleChoreography(
            tuple(emitters),
            700 + 2300 * loud + 15000 * strike + 28000 * drop,
            0.26 + 0.34 * m + 0.25 * drop,
            0.88,
            0.976,
            1.72,
            "prismatic",
            "shock_ring" if drop > 0.35 else "mote",
            "nebula",
            1.05 + 0.85 * drop,
            1.55,
            0.72,
            0.20 + 0.55 * s.bass,
            1.28 + 0.65 * s.mids + 0.45 * drop,
        )

    if bank == "lissajous_storm":
        # Eight phase-offset emitters ride a 3:2 Lissajous field. It looks chaotic at a glance but
        # remains exactly periodic and musically phase-locked, so it can become dense without
        # devolving into random confetti.
        emitters = []
        ax = 0.25 + 0.055 * s.bass
        ay = 0.20 + 0.050 * s.mids
        omega = 0.075 + 0.11 * s.mids + 0.065 * beat
        for i in range(8):
            p = angle * 0.18 + t * 0.12 + i * math.tau / 8.0
            px = 3.0 * p + i * 0.17
            py = 2.0 * p + math.pi * 0.5 + i * 0.11
            x = 0.5 + ax * math.sin(px)
            y = 0.5 + ay * math.sin(py)
            vx = 3.0 * ax * math.cos(px) * omega
            vy = 2.0 * ay * math.cos(py) * omega
            emitters.append(
                ParticleEmitter(
                    x,
                    y,
                    vx,
                    vy,
                    0.42 + 0.48 * loud + 0.26 * strike,
                    (0.04 + i * 0.105 + s.color * 0.15) % 1.0,
                    0.008 + 0.009 * strike,
                )
            )
        material = "shock_ring" if drop > 0.62 else "comet"
        return ParticleChoreography(
            tuple(emitters),
            4800 + 8200 * loud + 8500 * strike + 9500 * drop,
            0.22 + 0.42 * m + 0.10 * s.highs,
            0.88,
            0.952,
            1.42,
            "prismatic",
            material,
        )

    if bank == "singularity_crown":
        # Alternating inward/outward velocities around an uneven crown create a breathing implosion
        # / explosion field. Drops flip the material to shock rings for a sparse macro accent.
        emitters = []
        radius = 0.18 + 0.075 * s.bass + 0.035 * math.sin(t * 0.23)
        for i in range(8):
            a = angle * 0.22 + i * math.tau / 8.0 + 0.12 * math.sin(t * 0.17 + i)
            crown = radius * (1.0 + 0.18 * math.sin(3.0 * a + t * 0.31))
            direction = -1.0 if i % 2 == 0 else 1.0
            radial = direction * (0.10 + 0.24 * s.bass + 0.32 * drop)
            tangent = (0.20 + 0.34 * s.mids + 0.12 * strike) * (1.0 if i % 3 else -1.0)
            vx = math.cos(a) * radial - math.sin(a) * tangent
            vy = math.sin(a) * radial + math.cos(a) * tangent
            emitters.append(
                ParticleEmitter(
                    0.5 + math.cos(a) * crown,
                    0.5 + math.sin(a) * crown,
                    vx,
                    vy,
                    0.50 + 0.45 * loud + 0.35 * drop,
                    (0.74 + i * 0.052 + s.color * 0.10) % 1.0,
                    0.010 + 0.010 * beat,
                )
            )
        material = "shock_ring" if drop > 0.46 else "plasma"
        return ParticleChoreography(
            tuple(emitters),
            5400 + 9000 * loud + 14500 * drop,
            0.28 + 0.38 * m + 0.12 * strike,
            1.00,
            0.946,
            1.52,
            "cyber",
            material,
        )

    if bank == "prism_shards":
        # Radial shard emitters deliberately leave lots of black space, then explode outward on
        # sparse accents. The alternating angular offsets stop it reading as a static starburst.
        emitters = []
        base_radius = 0.095 + 0.085 * s.bass
        for i in range(8):
            a = angle * 0.13 + i * math.tau / 8.0 + 0.20 * math.sin(t * 0.19 + i * 1.7)
            radius = base_radius + 0.055 * math.sin(angle * 0.41 + i * 1.31)
            radial = 0.18 + 0.34 * beat + 0.42 * strike + 0.38 * drop
            tangent = (0.05 + 0.16 * s.mids) * (1.0 if i % 2 == 0 else -1.0)
            vx = math.cos(a) * radial - math.sin(a) * tangent
            vy = math.sin(a) * radial + math.cos(a) * tangent
            emitters.append(
                ParticleEmitter(
                    0.5 + math.cos(a) * radius,
                    0.5 + math.sin(a) * radius,
                    vx,
                    vy,
                    0.28 + 0.52 * loud + 0.42 * strike,
                    (s.color + i * 0.118) % 1.0,
                    0.005 + 0.011 * strike,
                )
            )
        return ParticleChoreography(
            tuple(emitters),
            2300 + 4800 * loud + 12000 * strike + 9000 * drop,
            0.10 + 0.26 * m,
            0.76,
            0.942,
            1.46,
            "prismatic",
            "spark",
        )

    # techno_lattice
    emitters = []
    phase = angle * 0.25
    points = (
        (0.24, 0.24),
        (0.50, 0.20),
        (0.76, 0.24),
        (0.80, 0.50),
        (0.76, 0.76),
        (0.50, 0.80),
        (0.24, 0.76),
        (0.20, 0.50),
    )
    for i, (bx, by) in enumerate(points):
        wobble = 0.018 * math.sin(phase + i * 0.79)
        x = 0.5 + (bx - 0.5) * (1.0 + 0.10 * s.bass) + wobble
        y = 0.5 + (by - 0.5) * (1.0 + 0.10 * s.bass) - wobble
        dx = x - 0.5
        dy = y - 0.5
        norm = max(math.hypot(dx, dy), 1e-5)
        tangent = 0.13 + 0.28 * s.mids
        radial = 0.08 + 0.34 * beat + 0.38 * drop
        vx = dx / norm * radial - dy / norm * tangent
        vy = dy / norm * radial + dx / norm * tangent
        emitters.append(
            ParticleEmitter(
                x,
                y,
                vx,
                vy,
                0.36 + 0.52 * loud + 0.40 * beat,
                (0.02 + i * 0.10 + s.color * 0.08) % 1.0,
                0.008 + 0.012 * strike,
            )
        )
    material = "shock_ring" if drop > 0.55 else "spark"
    return ParticleChoreography(
        tuple(emitters),
        3800 + 7200 * loud + 10500 * beat + 9000 * drop,
        0.09 + 0.20 * m,
        1.05,
        0.944,
        1.36,
        "solar",
        material,
    )


__all__ = ["BANKS", "ParticleChoreography", "blend_choreographies", "choreography"]

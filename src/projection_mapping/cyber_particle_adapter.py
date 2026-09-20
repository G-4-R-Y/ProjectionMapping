from __future__ import annotations

from dataclasses import dataclass
import math

from .gpu_particles import ParticleEmitter
from .point_tracker import TrackedPoint


CYBER_PARTICLE_MODES = (
    "data_swarm",
    "circuit_grid",
    "orbit_core",
    "event_horizon",
    "cosmic_roam",
)


@dataclass(frozen=True)
class CyberParticleProfile:
    field_mode: str
    material: str
    emission_rate: float
    turbulence: float
    drag: float
    feedback: float
    bloom: float
    field_strength: float = 1.0
    field_scale: float = 1.0
    field_spin: float = 1.0
    well_strength: float = 0.0
    nebula_mix: float = 0.0


_PROFILES = {
    "data_swarm": CyberParticleProfile(
        "flow", "data_point", 10500.0, 0.18, 1.05, 0.946, 1.15, 0.92, 1.30, 0.85, 0.10, 0.16
    ),
    "circuit_grid": CyberParticleProfile(
        "circuit", "data_point", 9200.0, 0.12, 1.18, 0.938, 1.05, 1.12, 1.45, 0.90, 0.08, 0.08
    ),
    "orbit_core": CyberParticleProfile(
        "binary_star", "data_point", 9800.0, 0.16, 1.00, 0.948, 1.18, 1.04, 1.20, 1.35, 1.20, 0.10
    ),
    "event_horizon": CyberParticleProfile(
        "event_horizon", "comet", 11200.0, 0.20, 0.92, 0.952, 1.28, 1.18, 1.08, 1.45, 1.55, 0.12
    ),
    "cosmic_roam": CyberParticleProfile(
        "cosmic_roam", "mote", 8400.0, 0.22, 0.86, 0.956, 1.25, 1.04, 0.92, 0.82, 1.05, 0.95
    ),
}


def profile_for_mode(mode: str) -> CyberParticleProfile:
    try:
        return _PROFILES[mode]
    except KeyError as exc:
        raise ValueError(f"unknown Cyber Mage particle mode: {mode}") from exc


def tracked_point_emitters(
    points: list[TrackedPoint],
    width: int,
    height: int,
    *,
    intensity: float = 1.0,
    limit: int = 8,
) -> list[ParticleEmitter]:
    """Turn generic LK tracks into a small, spatially diverse GPU emitter rig.

    The tracked points remain measurements, not pretend semantic hands. A low-energy centroid
    emitter gives the cloud a coherent body/core while the remaining emitters are selected for
    persistence, quality, motion, and spatial coverage.
    """

    if not points or width <= 0 or height <= 0 or limit <= 0:
        return []

    intensity = max(float(intensity), 0.0)
    limit = max(1, min(int(limit), 8))

    def norm_point(p: TrackedPoint) -> tuple[float, float]:
        return (
            min(max(float(p.x) / float(width), 0.0), 1.0),
            min(max(float(p.y) / float(height), 0.0), 1.0),
        )

    def base_score(p: TrackedPoint) -> float:
        age = min(max(p.age, 0) / 24.0, 1.0)
        motion = min(max(p.speed, 0.0) / 10.0, 1.0)
        quality = min(max(p.quality, 0.0), 1.0)
        return 0.35 + 0.28 * age + 0.22 * quality + 0.36 * motion

    ranked = sorted(points, key=base_score, reverse=True)
    chosen: list[TrackedPoint] = []
    if limit > 1:
        chosen.append(ranked[0])
        while len(chosen) < min(limit - 1, len(ranked)):
            best = None
            best_value = -1.0
            for candidate in ranked:
                if candidate in chosen:
                    continue
                cx, cy = norm_point(candidate)
                nearest = min(
                    math.hypot(cx - norm_point(other)[0], cy - norm_point(other)[1])
                    for other in chosen
                )
                value = base_score(candidate) * (0.35 + 1.65 * nearest)
                if value > best_value:
                    best = candidate
                    best_value = value
            if best is None:
                break
            chosen.append(best)

    mean_x = sum(p.x for p in points) / len(points)
    mean_y = sum(p.y for p in points) / len(points)
    mean_vx = sum(p.vx for p in points) / len(points)
    mean_vy = sum(p.vy for p in points) / len(points)
    mean_speed = sum(p.speed for p in points) / len(points)
    core_energy = (0.42 + 0.34 * min(mean_speed / 8.0, 1.0)) * intensity

    emitters = [
        ParticleEmitter(
            min(max(mean_x / width, 0.0), 1.0),
            min(max(mean_y / height, 0.0), 1.0),
            mean_vx / width * 30.0,
            mean_vy / height * 30.0,
            core_energy,
            0.93,
            0.032,
        )
    ]

    slots = max(limit - 1, 1)
    for i, p in enumerate(chosen[:slots]):
        x, y = norm_point(p)
        speed_energy = min(max(p.speed, 0.0) / 12.0, 1.0)
        quality = min(max(p.quality, 0.0), 1.0)
        age = min(max(p.age, 0) / 30.0, 1.0)
        energy = (0.34 + 0.54 * speed_energy + 0.16 * quality + 0.10 * age) * intensity
        hue = (0.06 + i * 0.137 + p.id * 0.017) % 1.0
        radius = 0.008 + 0.010 * (1.0 - quality) + 0.006 * speed_energy
        emitters.append(
            ParticleEmitter(
                x,
                y,
                p.vx / width * 30.0,
                p.vy / height * 30.0,
                energy,
                hue,
                radius,
            )
        )
        if len(emitters) >= limit:
            break

    return emitters[:limit]


__all__ = [
    "CYBER_PARTICLE_MODES",
    "CyberParticleProfile",
    "profile_for_mode",
    "tracked_point_emitters",
]

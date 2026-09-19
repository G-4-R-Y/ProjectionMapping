from __future__ import annotations

from dataclasses import dataclass

from .shader_scenes import SCENE_IDS


@dataclass(frozen=True)
class ShaderScenePreset:
    label: str
    scene: str
    speed: float
    intensity: float
    chaos: float
    preview_time: float
    description: str


SHADER_PRESETS: dict[str, ShaderScenePreset] = {
    "mercury_temple": ShaderScenePreset(
        "Mercury Temple", "liquid_chrome", 0.72, 1.08, 1.18, 1.7,
        "Slow silver-blue caustic marble with restrained crimson veins.",
    ),
    "black_sun_corona": ShaderScenePreset(
        "Black Sun Corona", "event_horizon", 0.68, 1.12, 1.30, 2.3,
        "Dark gravitational core, cyan-violet corona and organized filaments.",
    ),
    "aurora_silk": ShaderScenePreset(
        "Aurora Silk", "aurora_void", 0.58, 1.05, 0.92, 3.1,
        "Broad luminous curtains with slow drift and sparse electrical detail.",
    ),
    "neon_reliquary": ShaderScenePreset(
        "Neon Reliquary", "neon_cathedral", 0.64, 1.12, 1.08, 2.6,
        "Breathing cyber-vault, stained caustics and a white-hot oculus.",
    ),
    "choir_of_depth": ShaderScenePreset(
        "Choir of Depth", "wormhole_choir", 0.78, 1.08, 1.42, 1.9,
        "Layered log-radius harmonic voices descending into a portal.",
    ),
    "plasma_orchid": ShaderScenePreset(
        "Plasma Orchid", "plasma_singularity", 0.74, 1.08, 1.24, 2.2,
        "Nested magenta-blue plasma folds with precise white energy seams.",
    ),
    "vortex_coronation": ShaderScenePreset(
        "Vortex Coronation", "vortex_crown", 0.82, 1.10, 1.34, 2.8,
        "Five orbiting harmonic crowns and a restrained central field.",
    ),
    "collapse_ritual": ShaderScenePreset(
        "Collapse Ritual", "collapse_flower", 0.70, 1.14, 1.16, 1.5,
        "Layered petals fracture inward around a compact hot core.",
    ),
    "amethyst_cavern": ShaderScenePreset(
        "Amethyst Cavern", "crystal_cavern", 0.62, 1.08, 1.08, 2.0,
        "Faceted cyan-amethyst crystal vault with travelling internal light.",
    ),
    "solar_tapestry": ShaderScenePreset(
        "Solar Tapestry", "solar_loom", 0.66, 1.08, 1.12, 2.4,
        "Crimson-gold magnetic threads woven around a white solar heart.",
    ),
    "abyssal_bloom": ShaderScenePreset(
        "Abyssal Bloom", "abyssal_garden", 0.54, 1.12, 1.02, 3.0,
        "Emerald and cobalt bioluminescent growth rising through dark water.",
    ),
    "prismatic_altar": ShaderScenePreset(
        "Prismatic Altar", "prism_mirage", 0.60, 1.06, 1.14, 1.8,
        "Folded spectral architecture with crystalline blades and a dark floor.",
    ),
}

PRESET_IDS = ("custom", *SHADER_PRESETS)


def resolve_shader_preset(
    preset: str,
    *,
    scene: str,
    speed: float,
    intensity: float,
    chaos: float,
) -> tuple[str, float, float, float]:
    if preset == "custom":
        if scene not in SCENE_IDS:
            raise ValueError(f"unknown shader scene: {scene}")
        return scene, float(speed), float(intensity), float(chaos)
    try:
        selected = SHADER_PRESETS[preset]
    except KeyError as exc:
        raise ValueError(f"unknown shader preset: {preset}") from exc
    return selected.scene, selected.speed, selected.intensity, selected.chaos


__all__ = ["PRESET_IDS", "SHADER_PRESETS", "ShaderScenePreset", "resolve_shader_preset"]

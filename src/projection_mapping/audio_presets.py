from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AudioPerformancePreset:
    scene: str
    palette: str
    reactivity: str
    madness: float
    event_threshold: float
    beat_threshold: float
    sensitivity: float = 1.20
    analysis_size: int = 2048
    transition_seconds: float = 2.4
    auto_scene_seconds: float = 28.0


PRESETS: dict[str, AudioPerformancePreset] = {
    "journey_balanced": AudioPerformancePreset(
        scene="journey",
        palette="neon_aurora",
        reactivity="balanced",
        madness=0.42,
        event_threshold=0.64,
        beat_threshold=0.50,
    ),
    "techno_pulse": AudioPerformancePreset(
        scene="pulse",
        palette="solar_flare",
        reactivity="punchy",
        madness=0.60,
        event_threshold=0.58,
        beat_threshold=0.42,
        sensitivity=1.18,
    ),
    "ambient_void": AudioPerformancePreset(
        scene="void",
        palette="bioluminescent",
        reactivity="smooth",
        madness=0.28,
        event_threshold=0.74,
        beat_threshold=0.62,
        sensitivity=1.10,
        transition_seconds=4.0,
    ),
    "liquid_melodic": AudioPerformancePreset(
        scene="liquid",
        palette="prismatic",
        reactivity="balanced",
        madness=0.38,
        event_threshold=0.66,
        beat_threshold=0.52,
        sensitivity=1.18,
    ),
    "cathedral_installation": AudioPerformancePreset(
        scene="cathedral",
        palette="intelli",
        reactivity="balanced",
        madness=0.32,
        event_threshold=0.68,
        beat_threshold=0.54,
        sensitivity=1.12,
        transition_seconds=3.2,
    ),
    "acid_afterhours": AudioPerformancePreset(
        scene="journey",
        palette="prismatic",
        reactivity="punchy",
        madness=0.72,
        event_threshold=0.56,
        beat_threshold=0.40,
        sensitivity=1.22,
        transition_seconds=1.6,
        auto_scene_seconds=20.0,
    ),
}


__all__ = ["AudioPerformancePreset", "PRESETS"]

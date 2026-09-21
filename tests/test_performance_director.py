from projection_mapping.music_reactivity import MusicalSignals
from projection_mapping.music_structure import MusicStructure
from projection_mapping.performance_director import (
    PERFORMANCE_CUES,
    PERFORMANCE_JOURNEYS,
    PerformanceDirector,
    validate_performance_catalog,
)


def _signals(**overrides):
    values = dict(
        loudness=0.20,
        bass=0.18,
        mids=0.16,
        highs=0.10,
        color=0.50,
        strike=0.0,
        beat=0.0,
        ascension=0.0,
        tempo_bpm=120.0,
        beat_phase=0.0,
        bar_phase=0.0,
        beat_confidence=0.8,
        section_energy=0.20,
        drop=0.0,
    )
    values.update(overrides)
    return MusicalSignals(**values)


def _structure(section="steady", confidence=0.8, bars_seen=0):
    return MusicStructure(
        section=section,
        confidence=confidence,
        phrase_phase=0.0,
        energy_fast=0.3,
        energy_slow=0.3,
        energy_slope=0.0,
        bars_seen=bars_seen,
    )


def test_performance_catalog_references_real_shader_and_particle_assets():
    validate_performance_catalog()
    assert {"liquid_arc", "neon_ritual", "cosmic_rave"} <= set(PERFORMANCE_JOURNEYS)
    assert "singularity_drop" in PERFORMANCE_CUES


def test_timed_director_advances_and_crossfades():
    director = PerformanceDirector(
        journey="liquid_arc",
        mode="timed",
        cue_seconds=4.0,
        transition_seconds=2.0,
        minimum_dwell=1.0,
    )
    first = director.update(_structure(), _signals(), 100.0)
    assert first.target_cue == "liquid_intro"
    assert not first.active_transition

    started = director.update(_structure(), _signals(), 104.1)
    assert started.source_cue == "liquid_intro"
    assert started.target_cue == "membrane_drift"
    assert started.active_transition
    assert started.mix == 0.0

    middle = director.update(_structure(), _signals(), 105.1)
    assert 0.45 < middle.mix < 0.55

    done = director.update(_structure(), _signals(), 106.2)
    assert done.target_cue == "membrane_drift"
    assert not done.active_transition


def test_hybrid_director_uses_drop_as_urgent_override():
    director = PerformanceDirector(
        journey="liquid_arc",
        mode="hybrid",
        transition_seconds=1.0,
        minimum_dwell=20.0,
    )
    director.update(_structure(), _signals(), 10.0)
    state = director.update(
        _structure(section="drop", confidence=0.95),
        _signals(drop=0.92, loudness=0.9, bass=0.9),
        10.2,
    )
    assert state.target_cue == "singularity_drop"
    assert state.active_transition


def test_shared_macro_rises_with_music_and_drop_energy():
    calm = PerformanceDirector(journey="liquid_arc", mode="timed", base_madness=0.25)
    hot = PerformanceDirector(journey="liquid_arc", mode="timed", base_madness=0.25)

    calm_state = None
    hot_state = None
    for i in range(90):
        now = 20.0 + i / 60.0
        calm_state = calm.update(
            _structure(section="breakdown"),
            _signals(loudness=0.05, bass=0.03, section_energy=0.05),
            now,
        )
        hot_state = hot.update(
            _structure(section="drop"),
            _signals(
                loudness=0.95,
                bass=0.90,
                mids=0.75,
                highs=0.70,
                strike=0.85,
                drop=0.95,
                section_energy=0.92,
            ),
            now,
        )

    assert calm_state is not None and hot_state is not None
    assert hot_state.macro.madness > calm_state.macro.madness
    assert hot_state.macro.particle_emission > calm_state.macro.particle_emission
    assert hot_state.macro.shader_chaos > calm_state.macro.shader_chaos
    assert hot_state.macro.composite_mix > 0.0

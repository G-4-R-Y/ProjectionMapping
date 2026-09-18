from projection_mapping.music_reactivity import MusicalSignals
from projection_mapping.music_structure import (
    MusicStructure,
    MusicStructureTracker,
    ParticleJourneyController,
    ParticleJourneyCrossfade,
)


def sig(**updates):
    values = {
        "loudness": 0.25,
        "bass": 0.20,
        "mids": 0.20,
        "highs": 0.10,
        "color": 0.4,
        "strike": 0.0,
        "beat": 0.0,
        "ascension": 0.0,
        "tempo_bpm": 120.0,
        "beat_phase": 0.1,
        "bar_phase": 0.1,
        "beat_confidence": 0.9,
        "section_energy": 0.25,
        "drop": 0.0,
    }
    values.update(updates)
    return MusicalSignals(**values)


def test_structure_tracker_detects_explicit_drop_immediately():
    tracker = MusicStructureTracker(minimum_dwell=0.1)
    tracker.update(sig(), 0.0)
    state = tracker.update(sig(loudness=0.9, bass=0.9, strike=1.0, drop=1.0), 0.1)
    assert state.section == "drop"
    assert state.confidence > 0.7


def test_particle_journey_uses_new_section_banks():
    controller = ParticleJourneyController(initial="helix_fountain", minimum_dwell=1.0)
    drop = MusicStructure("drop", 1.0, 0.5, 0.8, 0.4, 0.4, 4)
    assert controller.update(drop, 2.0) == "techno_lattice"

    # A non-urgent section waits for phrase edge + dwell.
    breakdown = MusicStructure("breakdown", 0.9, 0.03, 0.15, 0.20, -0.05, 8)
    assert controller.update(breakdown, 3.2) == "nebula_bloom"


def test_particle_journey_crossfade_uses_smoothstep_and_settles():
    transition = ParticleJourneyCrossfade(initial="helix_fountain", duration=2.0)
    start = transition.update("techno_lattice", 10.0)
    middle = transition.update("techno_lattice", 11.0)
    end = transition.update("techno_lattice", 12.0)

    assert start.source_bank == "helix_fountain"
    assert start.target_bank == "techno_lattice"
    assert start.mix == 0.0
    assert middle.mix == 0.5
    assert not end.active
    assert end.source_bank == end.target_bank == "techno_lattice"

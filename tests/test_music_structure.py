from projection_mapping.music_reactivity import MusicalSignals
from projection_mapping.music_structure import MusicStructure, MusicStructureTracker, ParticleJourneyController


def sig(**updates):
    values=dict(
        loudness=.25,bass=.20,mids=.20,highs=.10,color=.4,strike=0.0,beat=0.0,ascension=0.0,
        tempo_bpm=120.0,beat_phase=.1,bar_phase=.1,beat_confidence=.9,section_energy=.25,drop=0.0,
    )
    values.update(updates)
    return MusicalSignals(**values)


def test_structure_tracker_detects_explicit_drop_immediately():
    tracker=MusicStructureTracker(minimum_dwell=.1)
    tracker.update(sig(),0.0)
    state=tracker.update(sig(loudness=.9,bass=.9,strike=1.0,drop=1.0),.1)
    assert state.section == "drop"
    assert state.confidence > .7


def test_particle_journey_uses_new_section_banks():
    controller=ParticleJourneyController(initial="helix_fountain",minimum_dwell=1.0)
    drop=MusicStructure("drop",1.0,.5,.8,.4,.4,4)
    assert controller.update(drop,2.0) == "techno_lattice"

    # A non-urgent section waits for phrase edge + dwell.
    breakdown=MusicStructure("breakdown",.9,.03,.15,.20,-.05,8)
    assert controller.update(breakdown,3.2) == "nebula_bloom"

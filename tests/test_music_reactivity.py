from projection_mapping.audio_reactive import AudioFeatures
from projection_mapping.music_reactivity import MusicalEventMapper


def feat(**kwargs):
    values = dict(timestamp=0.0, rms=0.0, bass=0.0, mid=0.0, treble=0.0, centroid=0.5, flux=0.0, onset=0.0)
    values.update(kwargs)
    return AudioFeatures(**values)


def test_quiet_noise_does_not_trigger_events():
    mapper = MusicalEventMapper(mode="balanced")
    s = mapper.update(feat(rms=0.08, bass=0.12, treble=0.20, onset=0.25), 1.0)
    assert s.strike == 0.0
    assert s.beat == 0.0
    assert s.highs == 0.0


def test_strong_onset_triggers_strike():
    mapper = MusicalEventMapper(mode="balanced", event_threshold=0.6)
    s = mapper.update(feat(rms=0.5, bass=0.4, onset=0.85), 1.0)
    assert s.strike > 0.0


def test_strike_refractory_period_blocks_immediate_retrigger():
    mapper = MusicalEventMapper(mode="balanced", event_threshold=0.6)
    first = mapper.update(feat(rms=0.5, bass=0.4, onset=0.9), 1.0)
    second = mapper.update(feat(rms=0.5, bass=0.4, onset=0.9), 1.05)
    assert first.strike > 0.0
    assert second.strike <= first.strike


def test_ascension_requires_bass_and_onset():
    mapper = MusicalEventMapper(mode="balanced")
    no_bass = mapper.update(feat(rms=0.6, bass=0.2, onset=0.95), 1.0)
    assert no_bass.ascension == 0.0
    mapper = MusicalEventMapper(mode="balanced")
    strong = mapper.update(feat(rms=0.6, bass=0.8, onset=0.95), 1.0)
    assert strong.ascension > 0.0

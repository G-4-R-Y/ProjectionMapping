import numpy as np

from projection_mapping.audio_music_features import RollingMusicFeatureExtractor
from projection_mapping.audio_reactive import AudioFeatures
from projection_mapping.music_reactivity import MusicalEventMapper


def _tone_block(freq: float, start: int, n: int = 256, sr: int = 48_000, amp: float = 0.7):
    samples = np.arange(start, start + n, dtype=np.float32)
    return amp * np.sin(2 * np.pi * freq * samples / sr)


def test_rolling_analysis_resolves_bass_with_256_sample_capture_blocks():
    ex = RollingMusicFeatureExtractor(
        sample_rate=48_000,
        analysis_size=2048,
        attack_ms=0.1,
        release_ms=0.1,
        sensitivity=1.0,
    )
    out = None
    for i in range(12):
        out = ex.process(_tone_block(90.0, i * 256), timestamp=1.0 + i * 256 / 48_000)
    assert out is not None
    assert out.bass > 0.45
    assert out.bass > out.mid
    assert out.bass > out.treble


def test_rolling_analysis_resolves_treble():
    ex = RollingMusicFeatureExtractor(
        sample_rate=48_000,
        analysis_size=2048,
        attack_ms=0.1,
        release_ms=0.1,
        sensitivity=1.0,
    )
    out = None
    for i in range(12):
        out = ex.process(_tone_block(6000.0, i * 256), timestamp=1.0 + i * 256 / 48_000)
    assert out is not None
    assert out.treble > out.bass
    assert out.treble > out.mid


def _beat_feature(ts: float) -> AudioFeatures:
    return AudioFeatures(
        timestamp=ts,
        rms=0.82,
        bass=0.92,
        mid=0.30,
        treble=0.10,
        centroid=0.34,
        flux=0.80,
        onset=0.92,
    )


def test_tempo_tracker_locks_near_120_bpm():
    mapper = MusicalEventMapper(mode="balanced", beat_threshold=0.45)
    signal = None
    for i in range(8):
        t = 1.0 + i * 0.5
        signal = mapper.update(_beat_feature(ts=t), t)
    assert signal is not None
    assert 116.0 <= signal.tempo_bpm <= 124.0
    assert signal.beat_confidence > 0.4


def test_same_audio_block_cannot_create_a_second_event():
    mapper = MusicalEventMapper(mode="punchy", event_threshold=0.5)
    f = _beat_feature(ts=1.0)
    first = mapper.update(f, 1.0)
    second = mapper.update(f, 1.25)
    assert first.strike > 0.0
    # Energy may still be decaying, but the same capture timestamp cannot inject a new peak.
    assert second.strike < first.strike

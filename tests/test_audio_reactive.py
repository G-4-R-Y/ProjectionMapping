import numpy as np

from projection_mapping.audio_reactive import AudioFeatureExtractor


def tone(freq: float, sample_rate: int = 48_000, n: int = 2048, amp: float = 0.7):
    t = np.arange(n, dtype=np.float32) / sample_rate
    return amp * np.sin(2 * np.pi * freq * t)


def test_bass_tone_prefers_bass_band():
    ex = AudioFeatureExtractor(sample_rate=48_000, attack_ms=0.1, release_ms=0.1, sensitivity=1.0)
    f = ex.process(tone(90.0), timestamp=1.0)
    assert f.bass > f.treble


def test_treble_tone_prefers_treble_band():
    ex = AudioFeatureExtractor(sample_rate=48_000, attack_ms=0.1, release_ms=0.1, sensitivity=1.0)
    f = ex.process(tone(6000.0), timestamp=1.0)
    assert f.treble > f.bass


def test_features_are_bounded():
    ex = AudioFeatureExtractor(sample_rate=48_000, attack_ms=1.0, release_ms=1.0, sensitivity=10.0)
    f = ex.process(tone(440.0, amp=1.0), timestamp=1.0)
    for value in (f.rms, f.bass, f.mid, f.treble, f.centroid, f.flux, f.onset):
        assert 0.0 <= value <= 1.0

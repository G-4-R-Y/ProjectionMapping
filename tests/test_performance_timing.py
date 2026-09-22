from projection_mapping.music_reactivity import MusicalSignals
from projection_mapping.music_structure import MusicStructure
from projection_mapping.performance_control import ControlEvent
from projection_mapping.performance_timing import PerformanceCueLooper, PerformanceQuantizer


def signals(**overrides):
    values = dict(
        loudness=0.2,
        bass=0.2,
        mids=0.2,
        highs=0.2,
        color=0.5,
        strike=0.0,
        beat=0.0,
        ascension=0.0,
        tempo_bpm=120.0,
        beat_phase=0.25,
        bar_phase=0.25,
        beat_confidence=0.9,
        section_energy=0.2,
        drop=0.0,
    )
    values.update(overrides)
    return MusicalSignals(**values)


def structure(bars_seen=2):
    return MusicStructure(
        section="steady",
        confidence=0.8,
        phrase_phase=0.0,
        energy_fast=0.2,
        energy_slow=0.2,
        energy_slope=0.0,
        bars_seen=bars_seen,
    )


def test_beat_quantizer_delays_scene_change_to_next_beat():
    q = PerformanceQuantizer("beat")
    event = ControlEvent("cue", ("data_build",))
    assert q.submit(event, 10.0, signals(tempo_bpm=120.0, beat_phase=0.25)) is False
    assert q.pop_due(10.36) == []
    assert q.pop_due(10.38) == [event]


def test_non_scene_controls_remain_immediate_under_quantization():
    q = PerformanceQuantizer("bar")
    event = ControlEvent("madness", (0.8,))
    assert q.submit(event, 10.0, signals()) is True
    assert q.pending_count == 0


def test_quantizer_replaces_stale_pending_scene_intent():
    q = PerformanceQuantizer("beat")
    first = ControlEvent("cue", ("liquid_intro",))
    second = ControlEvent("cue", ("afterglow",))
    assert not q.submit(first, 1.0, signals(beat_phase=0.4))
    assert not q.submit(second, 1.1, signals(beat_phase=0.5))
    assert q.pending_count == 1
    assert q.pop_due(1.4) == [second]


def test_looper_records_sparse_actions_and_replays_by_bar_length():
    loop = PerformanceCueLooper()
    start = 8.0
    loop.start_record(start)
    a = ControlEvent("cue", ("data_build",))
    b = ControlEvent("cue", ("afterglow",))
    loop.record(a, 8.5)
    loop.record(b, 10.0)
    loop.stop_record(11.2, auto_play=True)

    assert loop.length_beats == 4.0
    assert loop.playing
    assert len(loop.events) == 2

    origin = 11.2
    assert loop.tick(origin) == []
    assert loop.tick(origin + 0.51) == [a]
    assert loop.tick(origin + 2.01) == [b]
    assert loop.tick(origin + 4.51) == [a]


def test_beat_position_uses_bar_counter_and_phase():
    pos = PerformanceCueLooper.beat_position(structure(bars_seen=3), signals(bar_phase=0.5))
    assert pos == 14.0

import time

from projection_mapping.ableton_link import AbletonLinkClock, AbletonLinkState
from projection_mapping.performance_dashboard import LivePerformanceState, LiveStateHub


def test_link_clock_interpolates_phase_between_sync_pulses():
    clock = AbletonLinkClock(120.0)
    clock._state = AbletonLinkState(enabled=True, beat=8.0, phase=0.0, bpm=120.0, pulses=4)
    clock._period = 0.5
    clock._last_pulse_time = 10.0

    state = clock.state(now=10.125)
    assert state.enabled
    assert abs(state.phase - 0.25) < 1e-9
    assert abs(state.beat - 8.25) < 1e-9
    assert abs(state.bpm - 120.0) < 1e-9


def test_live_state_hub_round_trips_piano_and_clock_telemetry():
    hub = LiveStateHub()
    state = LivePerformanceState(
        cue="data_build",
        journey="liquid_arc",
        macro=0.71,
        bpm=128.0,
        clock="link",
        chord="minor7",
        notes=4,
        sustain=0.9,
    )
    hub.set(state)
    loaded = hub.get()
    assert loaded.cue == "data_build"
    assert loaded.clock == "link"
    assert loaded.chord == "minor7"
    assert loaded.notes == 4

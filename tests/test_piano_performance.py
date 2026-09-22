from types import SimpleNamespace

from projection_mapping.piano_performance import PianoMIDIInterpreter


def note_on(note: int, velocity: int = 100):
    return SimpleNamespace(type="note_on", note=note, velocity=velocity)


def note_off(note: int):
    return SimpleNamespace(type="note_off", note=note, velocity=0)


def cc(control: int, value: int):
    return SimpleNamespace(type="control_change", control=control, value=value)


def test_piano_expression_tracks_velocity_pitch_density_and_spread():
    piano = PianoMIDIInterpreter()
    piano.feed(note_on(48, 64), now=10.0)
    piano.feed(note_on(60, 100), now=10.1)
    piano.feed(note_on(72, 120), now=10.2)

    state = piano.expression(now=10.2)
    assert state.active_notes == (48, 60, 72)
    assert 0.0 < state.pitch < 1.0
    assert state.velocity > 0.5
    assert state.density > 0.0
    assert state.spread >= 0.5
    assert state.strike > 0.9


def test_sustain_latches_released_notes_until_pedal_release():
    piano = PianoMIDIInterpreter()
    piano.feed(note_on(60, 100), now=1.0)
    piano.feed(cc(64, 127), now=1.1)
    piano.feed(note_off(60), now=1.2)

    sustained = piano.expression(now=1.3)
    assert sustained.active_notes == (60,)
    assert sustained.sustain == 1.0

    piano.feed(cc(64, 0), now=1.4)
    released = piano.expression(now=1.5)
    assert released.active_notes == ()
    assert released.sustain == 0.0


def test_chord_classifier_distinguishes_consonance_and_tension():
    major = PianoMIDIInterpreter()
    for note in (60, 64, 67):
        major.feed(note_on(note, 90), now=2.0)
    major_state = major.expression(now=2.1)
    assert major_state.chord == "major"

    diminished = PianoMIDIInterpreter()
    for note in (60, 63, 66):
        diminished.feed(note_on(note, 90), now=2.0)
    dim_state = diminished.expression(now=2.1)
    assert dim_state.chord == "diminished"
    assert dim_state.tension > major_state.tension


def test_strike_transient_decays_after_note_attack():
    piano = PianoMIDIInterpreter()
    piano.feed(note_on(64, 127), now=4.0)
    early = piano.expression(now=4.0)
    late = piano.expression(now=5.0)
    assert early.strike > 0.99
    assert late.strike < early.strike


def test_optional_low_key_hot_cues_emit_without_being_mandatory():
    class Bus:
        def __init__(self):
            self.events = []

        def emit(self, action, *args):
            self.events.append((action, args))

    bus = Bus()
    piano = PianoMIDIInterpreter(bus, hot_cues=True, cue_note_base=21)
    piano.feed(note_on(21, 80), now=1.0)
    piano.feed(note_on(28, 80), now=1.1)
    assert bus.events[0] == ("cue", ("liquid_intro",))
    assert bus.events[1] == ("cue", ("afterglow",))

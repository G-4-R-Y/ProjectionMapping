from types import SimpleNamespace

from projection_mapping.performance_control import (
    HOT_CUES,
    MIDIControlInput,
    MIDIStateOutput,
    PerformanceControlBus,
    PerformanceSnapshot,
    PerformanceStateStore,
    keyboard_events,
)


def test_control_bus_is_fifo_and_bounded_by_drain_limit():
    bus = PerformanceControlBus()
    bus.emit("madness", 0.2)
    bus.emit("cue", "data_build")
    bus.emit("next")

    first = bus.drain(limit=2)
    assert [(event.action, event.args) for event in first] == [
        ("madness", (0.2,)),
        ("cue", ("data_build",)),
    ]
    assert [event.action for event in bus.drain()] == ["next"]


def test_keyboard_hot_cues_and_ab_snapshots():
    assert keyboard_events(ord("1"))[0].args == (HOT_CUES[0],)
    assert keyboard_events(ord("8"))[0].args == (HOT_CUES[7],)
    assert keyboard_events(ord("n"))[0].action == "next"
    assert keyboard_events(ord("]"))[0].args == (0.05,)
    assert keyboard_events(ord("["))[0].args == (-0.05,)
    assert keyboard_events(ord("a"))[0].action == "snapshot_save"
    assert keyboard_events(ord("A"))[0].action == "snapshot_load"
    assert keyboard_events(ord("b"))[0].args == ("B",)
    assert keyboard_events(ord("B"))[0].args == ("B",)


def test_state_store_round_trips_snapshots_and_user_journeys(tmp_path):
    store = PerformanceStateStore(tmp_path / "states.json")
    store.save_journey("my_set", ("liquid_intro", "data_build", "afterglow"))
    store.save_snapshot(
        PerformanceSnapshot(
            name="A",
            cue="data_build",
            journey="my_set",
            mode="hybrid",
            madness=0.67,
        )
    )

    assert store.journeys()["my_set"] == ("liquid_intro", "data_build", "afterglow")
    loaded = store.get_snapshot("A")
    assert loaded is not None
    assert loaded.cue == "data_build"
    assert loaded.journey == "my_set"
    assert loaded.mode == "hybrid"
    assert loaded.madness == 0.67


def test_midi_mapping_emits_madness_hot_cues_next_and_snapshots():
    bus = PerformanceControlBus()
    midi = MIDIControlInput(
        bus,
        madness_cc=7,
        note_base=40,
        journey_names=("liquid_arc", "cosmic_rave"),
    )

    midi._callback(SimpleNamespace(type="control_change", control=7, value=96))
    midi._callback(SimpleNamespace(type="note_on", note=40, velocity=100))
    midi._callback(SimpleNamespace(type="note_on", note=48, velocity=100))
    midi._callback(SimpleNamespace(type="note_on", note=49, velocity=100))
    midi._callback(SimpleNamespace(type="note_on", note=50, velocity=100))
    midi._callback(SimpleNamespace(type="note_on", note=51, velocity=100))
    midi._callback(SimpleNamespace(type="note_on", note=52, velocity=100))
    midi._callback(SimpleNamespace(type="program_change", program=1))

    events = bus.drain()
    assert events[0].action == "madness"
    assert abs(events[0].args[0] - 96 / 127.0) < 1e-9
    assert events[1].action == "cue" and events[1].args == (HOT_CUES[0],)
    assert [event.action for event in events[2:7]] == [
        "next",
        "snapshot_save",
        "snapshot_load",
        "snapshot_save",
        "snapshot_load",
    ]
    assert events[7].action == "journey"
    assert events[7].args == ("cosmic_rave",)



def test_piano_midi_mode_interprets_notes_instead_of_treating_them_as_hot_cues():
    bus = PerformanceControlBus()
    midi = MIDIControlInput(bus, mode="piano", piano_hot_cues=False)
    midi._callback(SimpleNamespace(type="note_on", note=60, velocity=110))
    assert bus.drain() == []
    state = midi.piano_expression(now=10.0)
    assert state is not None
    assert state.active_notes == (60,)
    assert state.velocity > 0.8


def test_midi_state_output_sends_cc_only_feedback(monkeypatch):
    sent = []

    class FakePort:
        def send(self, message):
            sent.append(message)

    class FakeMessage:
        def __init__(self, kind, **kwargs):
            self.type = kind
            self.kwargs = kwargs

    import sys
    monkeypatch.setitem(sys.modules, "mido", SimpleNamespace(Message=FakeMessage))

    out = MIDIStateOutput(cc_base=20)
    out._port = FakePort()
    out.send(
        madness=0.5,
        cue="data_build",
        section="drop",
        energy=0.75,
        quantize="bar",
    )

    assert len(sent) == 5
    assert all(message.type == "control_change" for message in sent)
    assert [message.kwargs["control"] for message in sent] == [20, 21, 22, 23, 24]
    assert sent[0].kwargs["value"] in {63, 64}
    assert sent[2].kwargs["value"] == 127

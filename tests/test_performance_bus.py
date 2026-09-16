from projection_mapping.performance_bus import (
    AnchorState,
    GestureEvent,
    PerformanceState,
    TrackingState,
    Vec3,
    merge_gestures,
)


def test_anchor_lookup_and_prefix():
    left = AnchorState("left_palm", Vec3(0.2, 0.3), confidence=0.9)
    right = AnchorState("right_palm", Vec3(0.8, 0.3), confidence=0.8)
    state = TrackingState(1.0, (640, 360), anchors=(left, right), source="test")
    assert state.anchor("left_palm", 0.5) == left
    assert state.anchor("right_palm", 0.85) is None
    assert state.anchors_with_prefix("left_") == (left,)


def test_merge_gestures_preserves_tracking_payload():
    state = TrackingState(2.0, (320, 240), performer_confidence=0.7, source="test")
    event = GestureEvent("slash_trail", 0.8, phase="impulse")
    merged = merge_gestures(state, [event])
    assert merged.gestures == (event,)
    assert merged.frame_size == state.frame_size
    assert merged.performer_confidence == state.performer_confidence


def test_performance_state_serializes_nested_dataclasses():
    state = TrackingState(3.0, (1280, 720), source="test")
    payload = PerformanceState(3.0, state, controls={"madness": 0.5}).to_dict()
    assert payload["tracking"]["frame_size"] == (1280, 720)
    assert payload["controls"]["madness"] == 0.5

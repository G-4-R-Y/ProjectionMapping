import numpy as np

from projection_mapping.performer_rig import PerformerRig


def test_performer_rig_detects_visible_body_and_anchors():
    mask = np.zeros((200, 300), dtype=np.uint8)
    mask[30:180, 120:180] = 255
    mask[65:95, 60:240] = 255
    flow = np.zeros_like(mask, dtype=np.float32)
    state = PerformerRig(smoothing=0.0).update(mask, flow)
    assert state.visible
    assert {"head", "chest", "core", "left_hand", "right_hand", "left_foot", "right_foot"} <= set(state.anchors)
    assert state.gestures.arms_spread


def test_performer_rig_handles_empty_mask():
    state = PerformerRig().update(np.zeros((64, 64), dtype=np.uint8))
    assert not state.visible
    assert state.bbox is None

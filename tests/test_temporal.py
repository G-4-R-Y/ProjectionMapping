import numpy as np

from projection_mapping.temporal import FlowTemporalStabilizer


def test_temporal_ingest_initial_keyframe():
    frame = np.full((20, 30, 3), 100, dtype=np.uint8)
    stabilizer = FlowTemporalStabilizer(30, 20)
    out = stabilizer.ingest_keyframe(frame)
    assert out.shape == frame.shape
    assert np.array_equal(out, frame)


def test_zero_flow_keeps_frame_stable():
    frame = np.zeros((20, 30, 3), dtype=np.uint8)
    frame[:, 10:15] = 255
    stabilizer = FlowTemporalStabilizer(30, 20)
    stabilizer.ingest_keyframe(frame)
    flow = np.zeros((20, 30, 2), dtype=np.float32)
    out = stabilizer.warp(flow)
    assert out is not None
    assert np.array_equal(out, frame)


def test_keyframe_blend_reduces_jump():
    stabilizer = FlowTemporalStabilizer(10, 10, keyframe_blend=0.5)
    stabilizer.ingest_keyframe(np.zeros((10, 10, 3), dtype=np.uint8))
    out = stabilizer.ingest_keyframe(np.full((10, 10, 3), 200, dtype=np.uint8))
    assert 90 <= int(out.mean()) <= 110
    assert stabilizer.stats.blend_residual > 0

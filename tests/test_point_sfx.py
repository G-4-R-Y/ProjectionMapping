import cv2
import numpy as np

from projection_mapping.point_sfx import PointSFXRenderer
from projection_mapping.point_tracker import LKPointTracker, TrackedPoint


def _feature_frame(shift_x: int = 0) -> np.ndarray:
    frame = np.zeros((160, 220, 3), dtype=np.uint8)
    for y in range(30, 140, 28):
        for x in range(35, 190, 32):
            xx = x + shift_x
            cv2.rectangle(frame, (xx - 4, y - 4), (xx + 4, y + 4), (255, 255, 255), -1)
    return frame


def test_lk_tracker_preserves_points_and_velocity():
    tracker = LKPointTracker(max_points=48, quality_level=0.005, min_distance=8, reseed_interval=50)
    mask = np.full((160, 220), 255, dtype=np.uint8)
    first = tracker.update(_feature_frame(0), mask)
    second = tracker.update(_feature_frame(4), mask)
    assert len(first) >= 8
    assert len(second) >= 8
    moving = [p for p in second if p.age > 0]
    assert moving
    assert np.median([p.vx for p in moving]) > 2.0
    assert np.median([abs(p.vy) for p in moving]) < 1.5


def test_point_sfx_renderer_returns_rgb_frame():
    renderer = PointSFXRenderer(160, 100, mode="plasma_mesh", bloom=0.5)
    points = [
        TrackedPoint(1, 40, 50, 4, 0, 4, 10, 1.0),
        TrackedPoint(2, 85, 52, -3, 1, 3.2, 8, 1.0),
    ]
    out = renderer.render(points, mask=np.full((100, 160), 255, np.uint8))
    assert out.shape == (100, 160, 3)
    assert out.dtype == np.uint8
    assert int(out.max()) > 0

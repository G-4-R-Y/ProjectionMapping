import numpy as np

from projection_mapping.attractor_lab import ATTRACTOR_MODES, attractor_flow_phase, generate_attractor


def test_every_attractor_generates_finite_normalized_points():
    for mode in ATTRACTOR_MODES:
        pts = generate_attractor(mode, count=2048)
        assert pts.shape == (2048, 4)
        assert np.isfinite(pts).all()
        assert np.max(np.abs(pts[:, :3])) <= 1.45 + 1e-6
        assert np.all((pts[:, 3] >= 0.0) & (pts[:, 3] < 1.0))
        # A chaotic visual accidentally converging to one fixed point is technically finite but
        # artistically blank. Keep enough spatial spread to make every registered mode meaningful.
        spatial_std = np.std(pts[:, :3], axis=0)
        assert float(np.max(spatial_std)) > 0.05, f"{mode} collapsed to a fixed point"


def test_attractor_families_are_not_identical():
    lorenz = generate_attractor("lorenz", count=2048)
    clifford = generate_attractor("clifford", count=2048)
    assert not np.allclose(lorenz[:, :2], clifford[:, :2])


def test_attractor_flow_is_frame_rate_independent_and_wraps():
    assert attractor_flow_phase(0.0) == 0.0
    assert attractor_flow_phase(6.0) == 0.25
    assert attractor_flow_phase(12.0, speed=0.5) == 0.25
    assert attractor_flow_phase(24.0) == 0.0
    assert attractor_flow_phase(6.0, speed=0.0) == 0.0
    assert attractor_flow_phase(6.0) != attractor_flow_phase(6.1)


def test_flow_phase_rejects_invalid_time_or_speed():
    import pytest

    with pytest.raises(ValueError):
        attractor_flow_phase(float("nan"))
    with pytest.raises(ValueError):
        attractor_flow_phase(1.0, float("inf"))


def test_attractor_shader_exposes_live_trajectory_window():
    from projection_mapping.attractor_lab import _POINT_FRAGMENT, _VERTEX

    assert "u_flow_enabled" in _VERTEX
    assert "u_flow_phase" in _VERTEX
    assert "v_flow" in _POINT_FRAGMENT

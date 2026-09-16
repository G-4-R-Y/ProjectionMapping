import numpy as np

from projection_mapping.attractor_lab import ATTRACTOR_MODES, generate_attractor


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

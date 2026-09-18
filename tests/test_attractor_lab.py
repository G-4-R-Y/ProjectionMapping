import numpy as np

from projection_mapping.attractor_lab import (
    ATTRACTOR_MODES,
    ATTRACTOR_PALETTES,
    ATTRACTOR_TRACE_MODES,
    generate_attractor,
)
from projection_mapping.color_palettes import CURATED_PALETTES, palette_css, sample_palette


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


def test_attractor_has_curated_palettes_and_motion_modes():
    assert tuple(ATTRACTOR_PALETTES[: len(CURATED_PALETTES)]) == CURATED_PALETTES
    assert ATTRACTOR_TRACE_MODES == ("comet", "pulse_train", "full")
    for name in CURATED_PALETTES:
        assert palette_css(name).startswith("linear-gradient")
        dark = np.asarray(sample_palette(name, 0.0))
        hot = np.asarray(sample_palette(name, 1.0))
        assert np.all((dark >= 0.0) & (dark <= 1.0))
        assert np.all((hot >= 0.0) & (hot <= 1.0))
        assert float(hot.mean()) > float(dark.mean()) + 0.35


def test_curated_palette_midpoints_are_visually_distinct():
    samples = [np.asarray(sample_palette(name, 0.62)) for name in CURATED_PALETTES]
    for index, left in enumerate(samples):
        assert all(np.linalg.norm(left - right) > 0.12 for right in samples[index + 1 :])

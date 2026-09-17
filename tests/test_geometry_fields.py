import numpy as np

from projection_mapping.geometry_fields import GEOMETRY_MODES, lloyd_relax


def test_geometry_modes_are_distinct():
    assert GEOMETRY_MODES == (
        "voronoi_flow",
        "power_diagram",
        "lloyd_relaxation",
        "delaunay_ridges",
        "apollonian_gasket",
        "penrose_interference",
    )


def test_lloyd_relaxation_moves_sites_toward_cell_centroids():
    points = np.array([[-0.8, -0.8], [0.9, -0.5], [-0.4, 0.9], [0.7, 0.8]], dtype=np.float32)
    out = lloyd_relax(points, strength=0.7, grid=28)
    assert out.shape == points.shape
    assert np.isfinite(out).all()
    assert not np.allclose(out, points)
    assert np.max(np.abs(out)) <= 0.98 + 1e-6

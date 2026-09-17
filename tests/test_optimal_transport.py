import numpy as np

from projection_mapping.optimal_transport import TRANSPORT_MODES, make_transport_shapes, sinkhorn_barycentric_map


def test_transport_modes_are_stable():
    assert TRANSPORT_MODES == (
        "circle_to_spiral",
        "grid_to_disc",
        "rose_to_lissajous",
        "phyllotaxis_to_rose",
        "constellation_swap",
    )


def test_sinkhorn_barycentric_map_is_finite_and_nontrivial():
    source, target = make_transport_shapes("rose_to_lissajous", 96)
    mapped = sinkhorn_barycentric_map(source, target, epsilon=0.06, iterations=60)
    assert mapped.shape == source.shape
    assert np.isfinite(mapped).all()
    assert not np.allclose(mapped, source)
    assert np.max(np.abs(mapped)) < 1.5


def test_all_transport_shape_generators_are_finite():
    for mode in TRANSPORT_MODES:
        source, target = make_transport_shapes(mode, 80)
        assert source.shape == target.shape == (80, 2)
        assert np.isfinite(source).all() and np.isfinite(target).all()

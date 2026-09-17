from projection_mapping.hyperbolic_geometry import HYPERBOLIC_MODES, HYPERBOLIC_PALETTES


def test_hyperbolic_modes_are_stable_and_distinct():
    assert HYPERBOLIC_MODES == (
        "poincare_orbifold",
        "hyperbolic_geodesics",
        "mobius_lattice",
        "schottky_inversions",
        "klein_chords",
        "modular_domain",
    )
    assert len(set(HYPERBOLIC_MODES)) == len(HYPERBOLIC_MODES)


def test_hyperbolic_geometry_has_projector_palettes():
    assert {"spectral", "electric", "solar", "bio", "ultraviolet", "icefire"}.issubset(
        set(HYPERBOLIC_PALETTES)
    )

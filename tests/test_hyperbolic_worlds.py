from projection_mapping.hyperbolic_worlds import HYPERBOLIC_MODES, HYPERBOLIC_PALETTES


def test_hyperbolic_modes_are_stable_and_distinct():
    assert HYPERBOLIC_MODES == (
        "poincare_geodesics",
        "circle_inversion",
        "mobius_flow",
        "schottky_orbits",
        "hyperbolic_kaleidoscope",
    )
    assert len(set(HYPERBOLIC_MODES)) == len(HYPERBOLIC_MODES)


def test_hyperbolic_worlds_have_projector_palettes():
    assert {"spectral", "electric", "solar", "bio", "ultraviolet", "icefire"}.issubset(
        set(HYPERBOLIC_PALETTES)
    )

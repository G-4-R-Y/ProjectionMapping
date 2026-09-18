from projection_mapping.famous_math import MATH_MODES, MATH_PALETTES


def test_famous_math_modes_are_distinct_and_stable():
    assert MATH_MODES == (
        "mandelbrot_julia",
        "newton_basins",
        "riemann_zeta",
        "chladni_plate",
        "quasicrystal_5fold",
        "logistic_bifurcation",
        "superformula",
        "complex_domain",
    )
    assert len(set(MATH_MODES)) == len(MATH_MODES)


def test_famous_math_has_multiple_art_palettes():
    assert {"spectral", "electric", "solar", "bio", "ultraviolet", "icefire"}.issubset(
        set(MATH_PALETTES)
    )

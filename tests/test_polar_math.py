from projection_mapping.polar_math import POLAR_MODES, POLAR_PALETTES


def test_polar_math_has_five_distinct_equation_families():
    assert POLAR_MODES == (
        "rose_lattice",
        "hypotrochoid_engine",
        "log_spiral_interference",
        "phyllotaxis_reactor",
        "bessel_wave_chamber",
    )
    assert len(set(POLAR_MODES)) == 5


def test_polar_math_has_vivid_palette_choices():
    assert {"spectral", "cyber", "solar", "bio", "ultraviolet"}.issubset(POLAR_PALETTES)

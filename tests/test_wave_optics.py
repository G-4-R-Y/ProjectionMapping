from projection_mapping.wave_optics import OPTICS_MODES, OPTICS_PALETTES


def test_wave_optics_modes_are_stable_and_distinct():
    assert OPTICS_MODES == (
        "young_double_slit",
        "fresnel_zone_plate",
        "airy_diffraction",
        "multi_source_interference",
        "moire_gratings",
        "cusp_catastrophe",
    )
    assert len(set(OPTICS_MODES)) == len(OPTICS_MODES)


def test_wave_optics_has_projector_palettes():
    assert {"spectral", "electric", "solar", "bio", "ultraviolet", "icefire"}.issubset(
        set(OPTICS_PALETTES)
    )

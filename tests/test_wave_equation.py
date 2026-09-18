from projection_mapping.wave_equation import WAVE_MODES, WAVE_PALETTES


def test_wave_equation_modes_are_stable():
    assert WAVE_MODES == (
        "membrane_drop",
        "chladni_drive",
        "multi_source_resonance",
        "spiral_wave",
        "chaotic_boundary",
        "audio_plate",
    )
    assert len(set(WAVE_MODES)) == len(WAVE_MODES)


def test_wave_equation_has_multiple_palettes():
    assert {"spectral", "electric", "solar", "bio", "ultraviolet", "icefire"}.issubset(set(WAVE_PALETTES))

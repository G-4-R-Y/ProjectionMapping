from projection_mapping.continuous_ca import CONTINUOUS_CA_MODES, CONTINUOUS_CA_PALETTES


def test_continuous_ca_modes_are_stable():
    assert CONTINUOUS_CA_MODES == (
        "lenia_ring",
        "smoothlife",
        "continuous_life",
        "cyclic_lenia",
        "excitable_garden",
        "orbium_study",
    )
    assert len(set(CONTINUOUS_CA_MODES)) == len(CONTINUOUS_CA_MODES)


def test_continuous_ca_palette_family_is_rich():
    assert len(CONTINUOUS_CA_PALETTES) >= 6

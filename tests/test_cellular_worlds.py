from projection_mapping.cellular_worlds import CELLULAR_MODES, CELLULAR_PALETTES


def test_cellular_worlds_cover_distinct_rule_families():
    assert CELLULAR_MODES == (
        "conway_life",
        "brians_brain",
        "cyclic_8",
        "seeds",
    )
    assert len(set(CELLULAR_MODES)) == len(CELLULAR_MODES)


def test_cellular_worlds_have_projector_palettes():
    assert {"electric", "bio", "solar", "ultraviolet", "icefire"}.issubset(
        set(CELLULAR_PALETTES)
    )

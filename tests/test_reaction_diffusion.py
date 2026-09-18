from projection_mapping.reaction_diffusion import REACTION_PALETTES, REACTION_PRESETS


def test_reaction_presets_are_in_stable_gray_scott_ranges():
    assert {"coral", "mitosis", "worms", "maze", "solitons", "waves"}.issubset(
        REACTION_PRESETS
    )
    for preset in REACTION_PRESETS.values():
        assert 0.0 < preset.feed < 0.1
        assert 0.0 < preset.kill < 0.1
        assert preset.du > preset.dv > 0.0


def test_reaction_palettes_include_dark_installation_options():
    assert "ultraviolet" in REACTION_PALETTES
    assert "mono" in REACTION_PALETTES

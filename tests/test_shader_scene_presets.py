from projection_mapping.shader_scenes import (
    PALETTE_IDS,
    SCENE_IDS,
    SHADER_SCENE_PRESETS,
)


def test_shader_scene_expansion_registry_is_complete():
    expected = {
        "liquid_chrome",
        "liquid_membrane",
        "ferrofluid_bloom",
        "holographic_oil",
        "data_tide",
    }
    assert expected <= set(SCENE_IDS)
    assert SCENE_IDS["liquid_chrome"] != SCENE_IDS["holographic_oil"]


def test_shader_palettes_include_project_defaults():
    assert PALETTE_IDS["cyan_magenta"] == 0
    assert {"cyan_magenta", "ultraviolet", "deep_ocean", "sunset_neon", "spectral"} <= set(PALETTE_IDS)


def test_shader_presets_reference_valid_assets():
    assert "liquid_neon" in SHADER_SCENE_PRESETS
    for preset in SHADER_SCENE_PRESETS.values():
        assert preset.scene in SCENE_IDS
        assert preset.scene_b in SCENE_IDS
        assert preset.palette in PALETTE_IDS
        assert 0.0 <= preset.scene_mix <= 1.0
        assert preset.speed > 0.0
        assert preset.intensity > 0.0
        assert 0.0 <= preset.chaos <= 2.5

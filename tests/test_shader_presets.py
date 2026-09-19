from pathlib import Path

import pytest

from projection_mapping.feature_registry import load_registry
from projection_mapping.shader_presets import PRESET_IDS, SHADER_PRESETS, resolve_shader_preset
from projection_mapping.shader_scenes import SCENE_IDS


def test_preset_vault_covers_every_shader_scene_once():
    scenes = [preset.scene for preset in SHADER_PRESETS.values()]

    assert len(SHADER_PRESETS) == 12
    assert set(scenes) == set(SCENE_IDS)
    assert len(scenes) == len(set(scenes))


@pytest.mark.parametrize("preset", SHADER_PRESETS.values())
def test_preset_controls_stay_inside_supported_ranges(preset):
    assert 0.1 <= preset.speed <= 2.5
    assert 0.2 <= preset.intensity <= 2.0
    assert 0.1 <= preset.chaos <= 3.0
    assert preset.preview_time >= 0.0


def test_resolver_applies_preset_and_preserves_custom_controls():
    selected = SHADER_PRESETS["solar_tapestry"]
    assert resolve_shader_preset(
        "solar_tapestry",
        scene="liquid_chrome",
        speed=2.0,
        intensity=0.5,
        chaos=2.0,
    ) == (selected.scene, selected.speed, selected.intensity, selected.chaos)
    assert resolve_shader_preset(
        "custom",
        scene="prism_mirage",
        speed=0.9,
        intensity=1.2,
        chaos=1.4,
    ) == ("prism_mirage", 0.9, 1.2, 1.4)


def test_scene_features_expose_the_same_preset_vault():
    registry = load_registry(Path("configs/features.toml"))

    for feature_id in ("shader_scene_lab", "gpu_mapped_scene"):
        feature = registry.by_id(feature_id)
        preset = next(param for param in feature.params if param.key == "preset")
        assert preset.choices == PRESET_IDS
        assert set(preset.choice_labels) == set(PRESET_IDS)

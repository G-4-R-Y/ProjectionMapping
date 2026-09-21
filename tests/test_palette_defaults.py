from pathlib import Path

from projection_mapping.feature_registry import load_registry


def _default(registry, feature_id: str, key: str):
    feature = registry.by_id(feature_id)
    return next(param.default for param in feature.params if param.key == key)


def test_visual_palette_defaults_use_cyan_magenta():
    registry = load_registry(Path("configs/features.toml"))
    expected = {
        ("cyber_mage", "palette"),
        ("attractor_lab", "palette"),
        ("famous_math_lab", "palette"),
        ("geometry_fields_lab", "palette"),
        ("hyperbolic_geometry_lab", "palette"),
        ("reaction_diffusion_lab", "palette"),
        ("cellular_worlds_lab", "palette"),
        ("continuous_ca_lab", "palette"),
        ("wave_equation_lab", "palette"),
        ("audio_visual_instrument", "palette"),
        ("audio_reactive_studio_cpu", "palette"),
        ("human_reactor", "palette"),
        ("performer_fx_gpu", "style"),
        ("shader_scene_lab", "palette"),
    }
    for feature_id, key in expected:
        assert _default(registry, feature_id, key) == "cyan_magenta"

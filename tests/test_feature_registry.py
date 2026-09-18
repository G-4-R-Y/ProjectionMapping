from pathlib import Path
import sys

import pytest

from projection_mapping.feature_registry import (
    Feature,
    FeatureParam,
    current_platform,
    infer_param_group,
    load_registry,
)


def test_registry_loads_project_features():
    registry = load_registry(Path("configs/features.toml"))
    ids = {feature.id for feature in registry.features}
    assert "room_skin" in ids
    assert "streamdiffusion_live" in ids
    assert "graycode_capture" in ids
    assert "surface_mapper" in ids
    assert "benchmark_streamdiffusion" in ids
    assert registry.by_id("spout_diagnostics").platforms == ("windows",)


def test_build_argv_coerces_python_and_bool_flags():
    feature = Feature(
        id="demo",
        name="Demo",
        category="Test",
        description="",
        command=("python", "demo.py"),
        params=(
            FeatureParam("display", "--display", "Display", "int", 1, min=0, max=8),
            FeatureParam("spout", "--spout", "Spout", "bool", False),
        ),
    )
    argv = feature.build_argv({"display": "2", "spout": True})
    assert argv == [sys.executable, "demo.py", "--display", "2", "--spout"]


def test_build_argv_rejects_out_of_range_values():
    feature = Feature(
        id="demo",
        name="Demo",
        category="Test",
        description="",
        command=("demo",),
        params=(FeatureParam("madness", "--madness", "Madness", "float", 0.5, min=0.0, max=1.0),),
    )
    with pytest.raises(ValueError, match="must be <= 1.0"):
        feature.build_argv({"madness": 2.0})


def test_portable_feature_supports_all_named_platforms():
    feature = Feature("demo", "Demo", "Test", "", ("python", "demo.py"))
    assert feature.supported_on("windows")
    assert feature.supported_on("linux")
    assert feature.supported_on("macos")


def test_platform_restricted_feature():
    feature = Feature(
        "spout",
        "Spout",
        "Test",
        "",
        ("python", "demo.py"),
        platforms=("windows",),
    )
    assert feature.supported_on("windows")
    assert not feature.supported_on("linux")
    assert not feature.supported_on("macos")


def test_build_argv_rejects_unsupported_current_platform():
    platform = current_platform()
    unsupported = {
        "windows": "linux",
        "linux": "macos",
        "macos": "windows",
        "other": "windows",
    }[platform]
    feature = Feature(
        "restricted",
        "Restricted",
        "Test",
        "",
        ("python", "demo.py"),
        platforms=(unsupported,),
    )
    with pytest.raises(RuntimeError, match="not supported"):
        feature.build_argv()


def test_external_command_requirement(monkeypatch):
    feature = Feature(
        "external",
        "External",
        "Test",
        "",
        ("imaginary-tool",),
        requires_commands=("imaginary-tool",),
    )
    monkeypatch.setattr("projection_mapping.feature_registry.shutil.which", lambda _name: None)
    assert feature.missing_commands() == ("imaginary-tool",)
    assert not feature.available()
    assert "missing external command" in feature.availability_hint()
    with pytest.raises(RuntimeError, match="not found on PATH"):
        feature.build_argv()


def test_external_command_requirement_satisfied(monkeypatch):
    feature = Feature(
        "external",
        "External",
        "Test",
        "",
        ("imaginary-tool",),
        requires_commands=("imaginary-tool",),
    )
    monkeypatch.setattr(
        "projection_mapping.feature_registry.shutil.which",
        lambda name: f"/usr/bin/{name}",
    )
    assert feature.missing_commands() == ()
    assert feature.available()
    assert feature.build_argv() == ["imaginary-tool"]


def test_param_group_inference_matches_console_personalization_contract():
    assert infer_param_group("source", "--source") == "System & Input"
    assert infer_param_group("device", "--device") == "System & Input"
    assert infer_param_group("render_width", "--render-width") == "Output & Resolution"
    assert infer_param_group("projector_height", "--projector-height") == "Output & Resolution"
    assert infer_param_group("mode", "--mode") == "Design Customization"
    assert infer_param_group("palette", "--palette") == "Design Customization"
    assert infer_param_group("madness", "--madness") == "Behavior & Reactivity"
    assert infer_param_group("capacity", "--capacity") == "Performance & Advanced"


def test_explicit_param_group_overrides_inference():
    param = FeatureParam(
        "mode",
        "--mode",
        "Equation",
        type="choice",
        default="lorenz",
        choices=("lorenz",),
        group="My Custom Box",
    )
    assert param.ui_group == "My Custom Box"


def test_feature_grouped_params_have_stable_intent_order():
    feature = Feature(
        "demo",
        "Demo",
        "Test",
        "",
        ("python", "demo.py"),
        params=(
            FeatureParam("mode", "--mode", "Mode"),
            FeatureParam("display", "--display", "Display"),
            FeatureParam("source", "--source", "Source"),
            FeatureParam("capacity", "--capacity", "Capacity"),
            FeatureParam("feedback", "--feedback", "Feedback"),
        ),
    )
    assert [name for name, _ in feature.grouped_params()] == [
        "System & Input",
        "Output & Resolution",
        "Design Customization",
        "Behavior & Reactivity",
        "Performance & Advanced",
    ]

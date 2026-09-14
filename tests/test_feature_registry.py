from pathlib import Path
import sys

from projection_mapping.feature_registry import Feature, FeatureParam, load_registry


def test_registry_loads_project_features():
    registry = load_registry(Path("configs/features.toml"))
    ids = {feature.id for feature in registry.features}
    assert "room_skin" in ids
    assert "streamdiffusion_live" in ids
    assert "graycode_capture" in ids
    assert "benchmark_streamdiffusion" in ids


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
    try:
        feature.build_argv({"madness": 2.0})
    except ValueError as exc:
        assert "must be <= 1.0" in str(exc)
    else:
        raise AssertionError("expected ValueError")

"""Contract tests for optional Varda launch; no Varda install/GPU required."""

from pathlib import Path

import pytest

from projection_mapping.feature_registry import load_registry


def test_varda_external_registry_contract(monkeypatch):
    feature = load_registry(Path("configs/features.toml")).by_id("varda_external")
    assert feature.command == ("varda",)
    assert feature.requires_commands == ("varda",)
    assert not feature.fullscreen
    assert all(feature.supported_on(os_name) for os_name in ("windows", "linux", "macos"))
    monkeypatch.setattr(
        "projection_mapping.feature_registry.shutil.which",
        lambda name: "/mock/varda" if name == "varda" else None,
    )
    assert feature.build_argv() == ["varda"]
    assert feature.build_argv(
        {
            "scene": "show.scene",
            "stage": "stage.json",
            "shader_dir": "./shaders",
            "no_osc": True,
            "no_ndi": True,
        }
    ) == [
        "varda",
        "--scene",
        "show.scene",
        "--stage",
        "stage.json",
        "--shader-dir",
        "./shaders",
        "--no-osc",
        "--no-ndi",
    ]


def test_varda_external_missing_binary_is_reported(monkeypatch):
    feature = load_registry(Path("configs/features.toml")).by_id("varda_external")
    monkeypatch.setattr(
        "projection_mapping.feature_registry.shutil.which", lambda _name: None
    )
    assert feature.missing_commands() == ("varda",)
    assert "missing external command" in feature.availability_hint()
    with pytest.raises(RuntimeError, match="not found on PATH"):
        feature.build_argv()

from __future__ import annotations

import sys
from pathlib import Path

from projection_mapping.feature_registry import Feature, FeatureParam, FeatureRegistry
from projection_mapping.launcher import LaunchState
from projection_mapping.web_ui import ControlDeck, _feature_payload


class FakeLauncher:
    def __init__(self, tmp_path: Path):
        self.state = LaunchState()
        self.log_path = tmp_path / "run.log"
        self.log_path.write_text("ready\n", encoding="utf-8")
        self.closed = False

    def poll(self):
        return self.state

    def launch(self, feature, values):
        self.state = LaunchState(
            feature_id=feature.id,
            feature_name=feature.name,
            argv=tuple(feature.build_argv(values)),
            pid=42,
            started_at="now",
            returncode=None,
            log_path=self.log_path,
        )
        return self.state

    def stop(self):
        self.state.returncode = 0
        return self.state

    def read_log_since(self, offset=0):
        data = self.log_path.read_bytes()
        return data[offset:].decode(), len(data)

    def close(self):
        self.closed = True


def _registry() -> FeatureRegistry:
    return FeatureRegistry(
        (
            Feature(
                id="demo",
                name="Demo",
                category="Visual",
                description="Fast controls",
                command=(sys.executable, "demo.py"),
                params=(
                    FeatureParam("mode", "--mode", "Mode", "choice", "one", ("one", "two")),
                    FeatureParam("gain", "--gain", "Gain", "float", 0.5, min=0.0, max=1.0),
                ),
            ),
        )
    )


def test_feature_payload_preserves_registry_driven_groups():
    payload = _feature_payload(_registry().by_id("demo"))
    assert payload["available"]
    assert payload["groups"][0]["name"] == "Design Customization"
    assert [param["key"] for param in payload["groups"][0]["params"]] == ["mode", "gain"]


def test_feature_payload_preserves_choice_labels():
    feature = Feature(
        id="labeled_demo",
        name="Labeled demo",
        category="Visual",
        description="Readable choices",
        command=(sys.executable, "demo.py"),
        params=(
            FeatureParam(
                "look",
                "--look",
                "Look",
                "choice",
                "black_sun",
                ("black_sun",),
                choice_labels={"black_sun": "Black Sun"},
            ),
        ),
    )

    payload = _feature_payload(feature)
    look = payload["groups"][0]["params"][0]
    assert look["choice_labels"] == {"black_sun": "Black Sun"}


def test_feature_payload_adds_known_palette_swatches():
    feature = Feature(
        id="palette_demo",
        name="Palette demo",
        category="Visual",
        description="Color preview",
        command=(sys.executable, "demo.py"),
        params=(
            FeatureParam(
                "palette",
                "--palette",
                "Palette",
                "choice",
                "aurora_ice",
                ("aurora_ice", "ember_gold"),
            ),
        ),
    )
    payload = _feature_payload(feature)
    palette = payload["groups"][0]["params"][0]
    assert set(palette["swatches"]) == {"aurora_ice", "ember_gold"}
    assert all(value.startswith("linear-gradient") for value in palette["swatches"].values())


def test_control_deck_launch_preserves_values_and_streams_incremental_log(tmp_path):
    launcher = FakeLauncher(tmp_path)
    deck = ControlDeck(_registry(), launcher)  # type: ignore[arg-type]

    state = deck.launch("demo", {"mode": "two", "gain": "0.8"})
    status = deck.status(0)

    assert state["running"]
    assert "--mode" in launcher.state.argv
    assert deck.values["demo"]["mode"] == "two"
    assert status["log"] == "ready\n"
    assert status["log_offset"] == 6


def test_control_deck_stop_and_close_delegate_to_launcher(tmp_path):
    launcher = FakeLauncher(tmp_path)
    deck = ControlDeck(_registry(), launcher)  # type: ignore[arg-type]
    deck.launch("demo", {})

    assert deck.stop()["returncode"] == 0
    deck.close()
    assert launcher.closed

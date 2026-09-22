from __future__ import annotations

import pytest

from projection_mapping.external_tools import build_brush_viewer_command


def test_brush_command_is_shell_free_and_preserves_source() -> None:
    source = "captures/room scan/scene.ply"
    command = build_brush_viewer_command(source, extra_args=("--some-upstream-flag", "7"))
    assert command.executable == "brush"
    assert command.argv == (
        "brush",
        source,
        "--with-viewer",
        "true",
        "--some-upstream-flag",
        "7",
    )


def test_brush_command_rejects_empty_source() -> None:
    with pytest.raises(ValueError):
        build_brush_viewer_command("   ")

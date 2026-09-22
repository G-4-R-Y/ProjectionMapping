from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
from typing import Sequence


@dataclass(frozen=True)
class ExternalToolCommand:
    argv: tuple[str, ...]
    executable: str


def build_brush_viewer_command(
    source: str | Path,
    *,
    executable: str = "brush",
    extra_args: Sequence[str] = (),
) -> ExternalToolCommand:
    """Build a shell-free Brush viewer command.

    Brush is intentionally kept out-of-process: it is a Rust/WebGPU application
    with its own dependency/runtime stack. The adapter only launches a user-
    installed Brush binary and never downloads, installs, or executes a shell.
    """
    source_text = str(source).strip()
    if not source_text:
        raise ValueError("Brush source path/URL must not be empty")
    if not executable.strip():
        raise ValueError("Brush executable must not be empty")
    argv = (executable, source_text, "--with-viewer", "true", *tuple(extra_args))
    return ExternalToolCommand(argv=argv, executable=executable)


def find_executable(name: str) -> str | None:
    return shutil.which(name)


def launch_external(command: ExternalToolCommand) -> subprocess.Popen[bytes]:
    """Launch an external tool without a shell so paths/URLs stay literal."""
    return subprocess.Popen(command.argv, shell=False)

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BUILD = ROOT / "build"
ENTRY = ROOT / "packaging" / "desktop_main.py"


def add_data_arg(source: str, dest: str) -> str:
    # PyInstaller accepts SOURCE:DEST on current releases across platforms.
    return f"{ROOT / source}{os.pathsep}{dest}"


def main() -> None:
    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        str(ENTRY),
        "--name",
        "ProjectionMapping",
        "--onedir",
        "--console",
        "--noconfirm",
        "--clean",
        "--paths",
        str(ROOT / "src"),
        "--distpath",
        str(DIST),
        "--workpath",
        str(BUILD / "pyinstaller"),
        "--specpath",
        str(BUILD / "spec"),
        "--collect-submodules",
        "projection_mapping",
        "--collect-all",
        "textual",
        "--collect-all",
        "soundcard",
        "--hidden-import",
        "cv2",
        "--add-data",
        add_data_arg("configs", "configs"),
        "--add-data",
        add_data_arg("experiments", "experiments"),
        "--add-data",
        add_data_arg("shaders", "shaders"),
        "--add-data",
        add_data_arg("docs/assets", "docs/assets"),
    ]
    print("Building desktop bundle:\n  " + " ".join(args))
    subprocess.run(args, cwd=ROOT, check=True)

    bundle = DIST / "ProjectionMapping"
    if sys.platform.startswith("win"):
        executable = bundle / "ProjectionMapping.exe"
    else:
        executable = bundle / "ProjectionMapping"
    if not executable.exists():
        raise SystemExit(f"build finished but executable was not found: {executable}")

    print(f"\nDesktop bundle ready: {bundle}")
    print(f"Double-click / launch: {executable}")


if __name__ == "__main__":
    main()

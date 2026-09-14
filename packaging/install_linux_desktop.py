from __future__ import annotations

import shutil
from pathlib import Path


def main() -> None:
    source = Path(__file__).resolve().parents[1] / "dist" / "ProjectionMapping"
    if not source.exists():
        raise SystemExit("Build first with: python packaging/build_desktop.py")

    install_root = Path.home() / ".local" / "opt" / "ProjectionMapping"
    applications = Path.home() / ".local" / "share" / "applications"
    desktop = applications / "ProjectionMapping.desktop"

    if install_root.exists():
        shutil.rmtree(install_root)
    install_root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, install_root)

    executable = install_root / "ProjectionMapping"
    executable.chmod(executable.stat().st_mode | 0o111)

    icon = install_root / "docs" / "assets" / "icon.svg"
    applications.mkdir(parents=True, exist_ok=True)
    desktop.write_text(
        "\n".join(
            [
                "[Desktop Entry]",
                "Type=Application",
                "Name=ProjectionMapping",
                "Comment=Visual Madness Control Deck",
                f"Exec={executable}",
                f"Icon={icon}",
                "Terminal=true",
                "Categories=AudioVideo;Graphics;",
                "StartupNotify=true",
                "",
            ]
        ),
        encoding="utf-8",
    )
    desktop.chmod(0o755)

    print(f"Installed application bundle to: {install_root}")
    print(f"Registered desktop launcher: {desktop}")
    print("ProjectionMapping should now appear in your application menu.")


if __name__ == "__main__":
    main()

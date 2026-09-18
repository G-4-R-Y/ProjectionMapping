from __future__ import annotations

import os
import sys

from projection_mapping.app_runtime import bundle_root, is_frozen, run_frozen_child


def main() -> int:
    if len(sys.argv) >= 2 and sys.argv[1] == "--pm-child":
        return run_frozen_child(sys.argv[2:])

    # Registry commands and bundled experiment paths are relative to the bundle.
    if is_frozen():
        os.chdir(bundle_root())

    if "--tui" in sys.argv:
        sys.argv.remove("--tui")
        from projection_mapping.tui import main as ui_main
    else:
        from projection_mapping.web_ui import main as ui_main

    ui_main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

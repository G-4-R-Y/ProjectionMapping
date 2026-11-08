from __future__ import annotations

import argparse
import sys

from projection_mapping.external_tools import (
    build_brush_viewer_command,
    find_executable,
    launch_external,
)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Launch a user-installed Brush WebGPU Gaussian-splat viewer out-of-process."
    )
    ap.add_argument("source", help="PLY/compressed PLY, dataset path, or URL accepted by Brush")
    ap.add_argument("--brush", default="brush", help="Brush executable name/path")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print the command without launching Brush",
    )
    args, extra = ap.parse_known_args()

    command = build_brush_viewer_command(args.source, executable=args.brush, extra_args=extra)
    if args.dry_run:
        print("[brush-adapter]", " ".join(command.argv))
        return 0

    resolved = find_executable(command.executable)
    if resolved is None:
        print(
            "[brush-adapter] Brush is not installed or is not on PATH. "
            "Install/build Brush separately, then rerun this experiment. "
            "The ProjectionMapping environment is intentionally not modified.",
            file=sys.stderr,
        )
        return 2

    print(
        "[brush-adapter] launching external Brush viewer; WebGPU/GPU behavior is upstream- and hardware-dependent",
        flush=True,
    )
    process = launch_external(command)
    try:
        return int(process.wait())
    except KeyboardInterrupt:
        process.terminate()
        try:
            return int(process.wait(timeout=5.0))
        except Exception:
            process.kill()
            return int(process.wait())


if __name__ == "__main__":
    raise SystemExit(main())

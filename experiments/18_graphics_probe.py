from __future__ import annotations

import argparse

from projection_mapping.graphics_runtime import probe_context


def main() -> None:
    ap = argparse.ArgumentParser(description="Probe the OpenGL/ModernGL runtime used by ProjectionMapping.")
    ap.add_argument("--require", type=int, default=330, help="Required OpenGL version code, e.g. 330")
    args = ap.parse_args()
    info = probe_context(require=args.require)
    print("ProjectionMapping graphics runtime OK")
    print(f"backend:      {info.backend}")
    print(f"version_code: {info.version_code}")
    print(f"GL_VERSION:   {info.gl_version}")
    print(f"GL_VENDOR:    {info.vendor}")
    print(f"GL_RENDERER:  {info.renderer}")


if __name__ == "__main__":
    main()

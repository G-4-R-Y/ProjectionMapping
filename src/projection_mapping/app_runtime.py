from __future__ import annotations

import gc
import importlib
import importlib.util
import runpy
import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def bundle_root() -> Path:
    """Return the source/data root for a normal checkout or a PyInstaller bundle."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS")).resolve()
    return Path(__file__).resolve().parents[2]


def runtime_root() -> Path:
    """Writable runtime directory independent of the launch working directory."""
    root = Path.home() / ".projection_mapping"
    root.mkdir(parents=True, exist_ok=True)
    return root


def release_runtime_resources() -> None:
    """Best-effort cleanup before a child process exits.

    Process termination is the real hard boundary that releases CUDA contexts, but
    explicitly dropping Python garbage and cached PyTorch allocations makes graceful
    shutdown cleaner and is useful when child-runner code returns normally.
    """
    gc.collect()
    torch = sys.modules.get("torch")
    if torch is None:
        return
    try:
        cuda = getattr(torch, "cuda", None)
        if cuda is not None and cuda.is_available():
            cuda.empty_cache()
            ipc_collect = getattr(cuda, "ipc_collect", None)
            if callable(ipc_collect):
                ipc_collect()
    except Exception:
        # Cleanup must never mask the original renderer error/exit code.
        pass


def desktop_self_test() -> int:
    """Exercise the installed/frozen desktop runtime without opening a window."""
    checks = ("numpy", "cv2", "textual", "moderngl", "glcontext", "soundcard")
    missing = [name for name in checks if importlib.util.find_spec(name) is None]
    if missing:
        print("[self-test] missing modules: " + ", ".join(missing), file=sys.stderr)
        return 2

    try:
        numpy = importlib.import_module("numpy")
        cv2 = importlib.import_module("cv2")
        importlib.import_module("textual")
        importlib.import_module("moderngl")
        importlib.import_module("glcontext")

        from .feature_registry import load_registry

        registry = load_registry()
        cyber = registry.by_id("cyber_mage")
        if cyber.defaults().get("palette") != "cyan_magenta":
            raise RuntimeError("Cyber Mage registry default is not cyan_magenta")

        print(
            "[self-test] ok "
            f"frozen={is_frozen()} python={sys.version.split()[0]} "
            f"numpy={numpy.__version__} opencv={cv2.__version__} "
            f"features={len(registry.features)} root={bundle_root()}"
        )
        return 0
    except Exception as exc:
        print(f"[self-test] failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 3


def run_frozen_child(argv: list[str]) -> int:
    """Execute a bundled Python-style registry command inside a fresh app process.

    Supported forms mirror registry commands after the leading ``python`` token:

    - ``-m package.module ...``
    - ``experiments/foo.py ...``

    The TUI relaunches the frozen executable with ``--pm-child`` so renderers stay
    isolated even though there is no standalone Python interpreter in the bundle.
    """
    if not argv:
        raise SystemExit("missing frozen child command")

    old_argv = sys.argv[:]
    try:
        if argv[0] == "-m":
            if len(argv) < 2:
                raise SystemExit("-m requires a module name")
            module = argv[1]
            sys.argv = [module, *argv[2:]]
            runpy.run_module(module, run_name="__main__", alter_sys=True)
            return 0

        script = Path(argv[0])
        if not script.is_absolute():
            script = bundle_root() / script
        if not script.exists():
            raise SystemExit(f"bundled script not found: {script}")
        sys.argv = [str(script), *argv[1:]]
        runpy.run_path(str(script), run_name="__main__")
        return 0
    finally:
        release_runtime_resources()
        sys.argv = old_argv

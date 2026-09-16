from __future__ import annotations

from dataclasses import dataclass
import os
import sys
from typing import Any


@dataclass(frozen=True)
class GraphicsContextInfo:
    backend: str
    version_code: int
    vendor: str
    renderer: str
    gl_version: str


def _candidate_backends() -> tuple[str | None, ...]:
    """Backends in preferred order for standalone/offscreen rendering.

    Linux tries EGL first because it does not depend on an X11/GLX window and works well
    with NVIDIA proprietary drivers. The platform default remains a fallback. Windows/macOS
    should use glcontext's default WGL/CGL path.
    """
    if sys.platform.startswith("linux"):
        forced = os.environ.get("PM_GL_BACKEND", "").strip().lower()
        if forced:
            return (forced, None)
        return ("egl", None)
    return (None,)


def create_context(*, require: int = 330) -> tuple[Any, GraphicsContextInfo]:
    """Create a ModernGL standalone context with actionable diagnostics.

    Raises RuntimeError with install/context details instead of a vague "unsupported" message.
    """
    try:
        import moderngl
    except ImportError as exc:
        raise RuntimeError(
            "ModernGL is not installed in this environment. Install the graphics extra with "
            "`python -m pip install -e '.[graphics]'`."
        ) from exc

    errors: list[str] = []
    for backend in _candidate_backends():
        label = backend or "platform-default"
        try:
            if backend is None:
                ctx = moderngl.create_standalone_context(require=require)
            else:
                ctx = moderngl.create_standalone_context(require=require, backend=backend)
            info = getattr(ctx, "info", {}) or {}
            return ctx, GraphicsContextInfo(
                backend=label,
                version_code=int(getattr(ctx, "version_code", 0)),
                vendor=str(info.get("GL_VENDOR", "unknown")),
                renderer=str(info.get("GL_RENDERER", "unknown")),
                gl_version=str(info.get("GL_VERSION", "unknown")),
            )
        except Exception as exc:  # pragma: no cover - hardware/platform dependent
            errors.append(f"{label}: {type(exc).__name__}: {exc}")

    details = " | ".join(errors) if errors else "no context backend was attempted"
    raise RuntimeError(
        "ModernGL is installed but an OpenGL 3.3+ context could not be created. "
        f"Backends tried: {details}. On Linux verify NVIDIA/Mesa OpenGL/EGL drivers and "
        "try `PM_GL_BACKEND=egl`; on packaged builds use a bundle built with the graphics extra."
    )


def probe_context(*, require: int = 330) -> GraphicsContextInfo:
    ctx, info = create_context(require=require)
    try:
        return info
    finally:
        try:
            ctx.release()
        except Exception:
            pass


__all__ = ["GraphicsContextInfo", "create_context", "probe_context"]

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .graphics_runtime import GraphicsContextInfo


@dataclass(frozen=True)
class MonitorInfo:
    index: int
    name: str
    width: int
    height: int
    refresh_rate: int


class NativeGLWindow:
    """GLFW window whose framebuffer is owned directly by one ModernGL context."""

    _F11 = 300

    def __init__(
        self,
        *,
        title: str,
        display: int = 0,
        width: int = 1280,
        height: int = 720,
        fullscreen: bool = True,
        vsync: bool = True,
    ) -> None:
        try:
            import glfw
            import moderngl
        except ImportError as exc:
            raise RuntimeError(
                "The native GPU window requires the graphics extra: "
                "`python -m pip install -e '.[graphics]'`."
            ) from exc

        self.glfw = glfw
        if not glfw.init():
            raise RuntimeError("GLFW could not initialize a display connection")

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.DOUBLEBUFFER, glfw.TRUE)
        self.monitors = self._monitor_infos()
        if not self.monitors:
            glfw.terminate()
            raise RuntimeError("GLFW found no displays")
        if not 0 <= display < len(self.monitors):
            glfw.terminate()
            raise ValueError(f"display {display} does not exist; found 0..{len(self.monitors) - 1}")

        self.display = display
        self.fullscreen = bool(fullscreen)
        self.windowed_rect = (80, 80, int(width), int(height))
        monitor = glfw.get_monitors()[display] if fullscreen else None
        if monitor is not None:
            mode = glfw.get_video_mode(monitor)
            width, height = mode.size.width, mode.size.height
        self.window = glfw.create_window(int(width), int(height), title, monitor, None)
        if not self.window:
            glfw.terminate()
            raise RuntimeError("GLFW could not create an OpenGL 3.3 window")

        try:
            glfw.make_context_current(self.window)
            glfw.swap_interval(1 if vsync else 0)
            self.ctx = moderngl.create_context(require=330)
        except Exception as exc:
            glfw.destroy_window(self.window)
            glfw.terminate()
            raise RuntimeError(f"could not attach ModernGL to the GLFW window: {exc}") from exc
        raw = getattr(self.ctx, "info", {}) or {}
        self.context_info = GraphicsContextInfo(
            backend="glfw-window",
            version_code=int(getattr(self.ctx, "version_code", 0)),
            vendor=str(raw.get("GL_VENDOR", "unknown")),
            renderer=str(raw.get("GL_RENDERER", "unknown")),
            gl_version=str(raw.get("GL_VERSION", "unknown")),
        )
        glfw.set_key_callback(self.window, self._on_key)

    def _monitor_infos(self) -> tuple[MonitorInfo, ...]:
        result = []
        for index, monitor in enumerate(self.glfw.get_monitors() or []):
            mode = self.glfw.get_video_mode(monitor)
            result.append(
                MonitorInfo(
                    index=index,
                    name=self.glfw.get_monitor_name(monitor) or f"Display {index}",
                    width=mode.size.width,
                    height=mode.size.height,
                    refresh_rate=mode.refresh_rate,
                )
            )
        return tuple(result)

    @property
    def framebuffer_size(self) -> tuple[int, int]:
        width, height = self.glfw.get_framebuffer_size(self.window)
        return int(width), int(height)

    @property
    def should_close(self) -> bool:
        return bool(self.glfw.window_should_close(self.window))

    def _on_key(self, _window: Any, key: int, _scancode: int, action: int, _mods: int) -> None:
        if action != self.glfw.PRESS:
            return
        if key == self.glfw.KEY_ESCAPE:
            self.glfw.set_window_should_close(self.window, True)
        elif key == self.glfw.KEY_F11 or key == self._F11:
            self.toggle_fullscreen()

    def toggle_fullscreen(self) -> None:
        glfw = self.glfw
        if self.fullscreen:
            x, y, width, height = self.windowed_rect
            glfw.set_window_monitor(self.window, None, x, y, width, height, 0)
            self.fullscreen = False
            return

        self.windowed_rect = (*glfw.get_window_pos(self.window), *glfw.get_window_size(self.window))
        monitor = glfw.get_monitors()[self.display]
        mode = glfw.get_video_mode(monitor)
        glfw.set_window_monitor(
            self.window,
            monitor,
            0,
            0,
            mode.size.width,
            mode.size.height,
            mode.refresh_rate,
        )
        self.fullscreen = True

    def present(self) -> None:
        self.glfw.swap_buffers(self.window)
        self.glfw.poll_events()

    def close(self) -> None:
        if getattr(self, "window", None) is not None:
            try:
                self.ctx.release()
            except Exception:
                pass
            self.glfw.destroy_window(self.window)
            self.window = None
        self.glfw.terminate()


__all__ = ["MonitorInfo", "NativeGLWindow"]

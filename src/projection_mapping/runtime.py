from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Protocol
import numpy as np


class Source(Protocol):
    def __call__(self) -> np.ndarray: ...


class Sink(Protocol):
    def __call__(self, frame: np.ndarray) -> bool | None: ...


@dataclass
class RuntimeStats:
    frames: int = 0
    fps: float = 0.0
    last_frame_ms: float = 0.0


def run_loop(
    source: Source,
    sink: Sink,
    processors: list[Callable[[np.ndarray], np.ndarray]] | None = None,
    max_frames: int | None = None,
) -> RuntimeStats:
    processors = processors or []
    stats = RuntimeStats()
    start = time.perf_counter()
    while max_frames is None or stats.frames < max_frames:
        t0 = time.perf_counter()
        frame = source()
        for proc in processors:
            frame = proc(frame)
        keep_going = sink(frame)
        stats.frames += 1
        stats.last_frame_ms = (time.perf_counter() - t0) * 1000
        stats.fps = stats.frames / max(time.perf_counter() - start, 1e-9)
        if keep_going is False:
            break
    return stats


class FullscreenSink:
    """OpenCV display sink with ESC-to-exit and F11 fullscreen toggle."""

    # OpenCV waitKeyEx values vary by backend. 122 is VK_F11 on Windows;
    # 65480 is XK_F11 on X11. Some builds encode the virtual key in upper bits.
    _F11_CODES = {122, 65480, 0x7A0000, 0x7A0001}

    def __init__(self, window="ProjectionMapping", display=0, quit_key=27, fullscreen=True):
        import cv2

        self.cv2 = cv2
        self.window = window
        self.quit_key = quit_key
        self.display = int(display)
        self.fullscreen = bool(fullscreen)
        cv2.namedWindow(window, cv2.WINDOW_NORMAL)
        self._apply_window_mode()
        if self.display > 0:
            # Temporary placement heuristic; monitor enumeration is tracked separately.
            cv2.moveWindow(window, self.display * 1920, 0)

    def _apply_window_mode(self) -> None:
        mode = self.cv2.WINDOW_FULLSCREEN if self.fullscreen else self.cv2.WINDOW_NORMAL
        self.cv2.setWindowProperty(self.window, self.cv2.WND_PROP_FULLSCREEN, mode)

    def toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen
        self._apply_window_mode()

    def __call__(self, frame):
        self.cv2.imshow(self.window, frame)
        key = self.cv2.waitKeyEx(1)
        if key < 0:
            return True
        if (key & 0xFF) == self.quit_key:
            return False
        if key in self._F11_CODES or (key & 0xFFFF) in self._F11_CODES:
            self.toggle_fullscreen()
        return True

    def close(self):
        try:
            self.cv2.destroyWindow(self.window)
        except Exception:
            self.cv2.destroyAllWindows()

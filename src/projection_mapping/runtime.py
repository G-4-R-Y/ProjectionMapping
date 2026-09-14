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


def run_loop(source: Source, sink: Sink, processors: list[Callable[[np.ndarray], np.ndarray]] | None = None, max_frames: int | None = None) -> RuntimeStats:
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
    def __init__(self, window="ProjectionMapping", display=0, quit_key=27):
        import cv2
        self.cv2 = cv2
        self.window = window
        self.quit_key = quit_key
        cv2.namedWindow(window, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(window, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        if display > 0:
            cv2.moveWindow(window, display * 1920, 0)

    def __call__(self, frame):
        self.cv2.imshow(self.window, frame)
        return (self.cv2.waitKey(1) & 0xFF) != self.quit_key

    def close(self):
        self.cv2.destroyWindow(self.window)

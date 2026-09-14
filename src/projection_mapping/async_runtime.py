from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import threading
import time
from typing import Callable, Generic, TypeVar

T = TypeVar("T")
U = TypeVar("U")


@dataclass
class AsyncStats:
    submitted: int = 0
    processed: int = 0
    dropped: int = 0
    errors: int = 0
    last_inference_ms: float = 0.0
    ema_inference_ms: float = 0.0
    last_completed_at: float = 0.0

    @property
    def inference_fps(self) -> float:
        return 1000.0 / self.ema_inference_ms if self.ema_inference_ms > 0 else 0.0


class LatestFrameWorker(Generic[T, U]):
    """Single-worker async processor with latest-frame-wins semantics.

    At most one pending item is kept while inference is busy. Submitting a newer item
    replaces the pending one, bounding latency instead of allowing an ever-growing queue.

    The worker never raises inference exceptions on the producer thread; call
    ``last_error()`` or inspect ``stats.errors`` from the display/control loop.
    """

    def __init__(
        self,
        fn: Callable[[T], U],
        *,
        name: str = "projection-inference",
        ema_alpha: float = 0.1,
    ) -> None:
        self.fn = fn
        self.name = name
        self.ema_alpha = float(ema_alpha)
        self.stats = AsyncStats()

        self._condition = threading.Condition()
        self._pending: deque[tuple[int, T, float]] = deque(maxlen=1)
        self._latest: tuple[int, U, float] | None = None
        self._error: BaseException | None = None
        self._closed = False
        self._seq = 0
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)
        self._thread.start()

    def submit(self, item: T) -> int:
        with self._condition:
            if self._closed:
                raise RuntimeError("worker is closed")
            self._seq += 1
            seq = self._seq
            if self._pending:
                self.stats.dropped += 1
                self._pending.clear()
            self._pending.append((seq, item, time.perf_counter()))
            self.stats.submitted += 1
            self._condition.notify()
            return seq

    def latest(self) -> tuple[int, U, float] | None:
        """Return ``(sequence, result, completed_monotonic_time)`` without blocking."""
        with self._condition:
            return self._latest

    def last_error(self) -> BaseException | None:
        with self._condition:
            return self._error

    def close(self, timeout: float | None = 5.0) -> None:
        with self._condition:
            self._closed = True
            self._condition.notify_all()
        self._thread.join(timeout=timeout)

    def __enter__(self) -> "LatestFrameWorker[T, U]":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _run(self) -> None:
        while True:
            with self._condition:
                while not self._pending and not self._closed:
                    self._condition.wait()
                if self._closed and not self._pending:
                    return
                seq, item, _submitted_at = self._pending.pop()
                self._pending.clear()

            started = time.perf_counter()
            try:
                output = self.fn(item)
            except BaseException as exc:  # keep display loop alive; surface through last_error
                elapsed_ms = (time.perf_counter() - started) * 1000.0
                with self._condition:
                    self.stats.errors += 1
                    self.stats.last_inference_ms = elapsed_ms
                    self._error = exc
                continue

            completed = time.perf_counter()
            elapsed_ms = (completed - started) * 1000.0
            with self._condition:
                self.stats.processed += 1
                self.stats.last_inference_ms = elapsed_ms
                if self.stats.ema_inference_ms == 0:
                    self.stats.ema_inference_ms = elapsed_ms
                else:
                    a = self.ema_alpha
                    self.stats.ema_inference_ms = a * elapsed_ms + (1.0 - a) * self.stats.ema_inference_ms
                self.stats.last_completed_at = completed
                self._latest = (seq, output, completed)
                self._error = None

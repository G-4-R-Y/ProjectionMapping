from __future__ import annotations

from dataclasses import dataclass, asdict
from collections import deque
import json
import statistics
import time
from pathlib import Path
from typing import Callable, Iterable


@dataclass
class TimingSummary:
    name: str
    samples: int
    mean_ms: float
    p50_ms: float
    p95_ms: float
    min_ms: float
    max_ms: float
    fps: float

    def to_dict(self) -> dict:
        return asdict(self)


class RollingTimer:
    """Collect latency samples and summarize them without external deps."""

    def __init__(self, name: str, maxlen: int = 4096):
        self.name = name
        self.samples_ms: deque[float] = deque(maxlen=maxlen)

    def add(self, ms: float) -> None:
        self.samples_ms.append(float(ms))

    def measure(self, fn: Callable, *args, **kwargs):
        t0 = time.perf_counter()
        out = fn(*args, **kwargs)
        self.add((time.perf_counter() - t0) * 1000.0)
        return out

    def summary(self) -> TimingSummary:
        xs = list(self.samples_ms)
        if not xs:
            return TimingSummary(self.name, 0, 0, 0, 0, 0, 0, 0)
        xs_sorted = sorted(xs)
        def q(p: float) -> float:
            idx = min(len(xs_sorted) - 1, max(0, round((len(xs_sorted) - 1) * p)))
            return xs_sorted[idx]
        mean = statistics.fmean(xs)
        return TimingSummary(
            name=self.name,
            samples=len(xs),
            mean_ms=mean,
            p50_ms=q(0.50),
            p95_ms=q(0.95),
            min_ms=min(xs),
            max_ms=max(xs),
            fps=1000.0 / mean if mean > 0 else 0.0,
        )


class BenchmarkReport:
    def __init__(self):
        self.timers: dict[str, RollingTimer] = {}
        self.metadata: dict[str, object] = {}

    def timer(self, name: str) -> RollingTimer:
        return self.timers.setdefault(name, RollingTimer(name))

    def summaries(self) -> list[TimingSummary]:
        return [t.summary() for t in self.timers.values()]

    def to_dict(self) -> dict:
        return {
            "metadata": self.metadata,
            "timings": {s.name: s.to_dict() for s in self.summaries()},
        }

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")


def warmup(callable_: Callable, inputs: Iterable, n: int = 10) -> None:
    it = iter(inputs)
    for _ in range(n):
        callable_(next(it))

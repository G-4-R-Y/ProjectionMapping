from __future__ import annotations

import asyncio
from dataclasses import dataclass
import threading
import time


@dataclass(frozen=True)
class AbletonLinkState:
    enabled: bool = False
    beat: float = 0.0
    phase: float = 0.0
    bpm: float = 120.0
    pulses: int = 0


class AbletonLinkClock:
    """Optional Ableton Link beat clock using aalink in a dedicated asyncio thread.

    The project does not require or bundle aalink by default. When enabled, beat boundaries are
    learned from Link.sync(1); wall-clock interpolation provides phase between boundaries.
    """

    def __init__(self, initial_tempo: float = 120.0) -> None:
        self.initial_tempo = float(initial_tempo)
        self._lock = threading.Lock()
        self._state = AbletonLinkState(bpm=self.initial_tempo)
        self._last_pulse_time: float | None = None
        self._period = 60.0 / max(self.initial_tempo, 1.0)
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._stop = threading.Event()
        self._link = None

    def start(self) -> "AbletonLinkClock":
        try:
            from aalink import Link  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "Ableton Link requires the optional link extra: "
                "python -m pip install -e '.[link]'"
            ) from exc

        if self._thread is not None:
            return self
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="pm-ableton-link", daemon=True)
        self._thread.start()
        return self

    def _run(self) -> None:
        asyncio.run(self._async_main())

    async def _async_main(self) -> None:
        from aalink import Link

        self._loop = asyncio.get_running_loop()
        link = Link(self.initial_tempo)
        link.enabled = True
        self._link = link
        try:
            while not self._stop.is_set():
                beat_value = float(await link.sync(1))
                now = time.perf_counter()
                with self._lock:
                    if self._last_pulse_time is not None:
                        interval = now - self._last_pulse_time
                        if 0.15 <= interval <= 2.0:
                            # Smooth tempo to reject scheduler jitter.
                            measured_period = interval
                            self._period = 0.78 * self._period + 0.22 * measured_period
                    self._last_pulse_time = now
                    bpm = 60.0 / max(self._period, 1e-6)
                    self._state = AbletonLinkState(
                        enabled=True,
                        beat=beat_value,
                        phase=0.0,
                        bpm=bpm,
                        pulses=self._state.pulses + 1,
                    )
        finally:
            link.enabled = False
            self._link = None

    def state(self, *, now: float | None = None) -> AbletonLinkState:
        now = time.perf_counter() if now is None else float(now)
        with self._lock:
            base = self._state
            last = self._last_pulse_time
            period = self._period
        if not base.enabled or last is None:
            return base
        elapsed = max(0.0, now - last)
        phase = (elapsed / max(period, 1e-6)) % 1.0
        beat = base.beat + elapsed / max(period, 1e-6)
        return AbletonLinkState(
            enabled=True,
            beat=beat,
            phase=phase,
            bpm=60.0 / max(period, 1e-6),
            pulses=base.pulses,
        )

    def close(self) -> None:
        self._stop.set()
        loop = self._loop
        if loop is not None:
            loop.call_soon_threadsafe(lambda: None)
        thread = self._thread
        if thread is not None:
            thread.join(timeout=1.5)
        self._thread = None
        self._loop = None

    def __enter__(self) -> "AbletonLinkClock":
        return self.start()

    def __exit__(self, *_exc) -> None:
        self.close()


__all__ = ["AbletonLinkClock", "AbletonLinkState"]

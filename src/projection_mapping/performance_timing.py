from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

import numpy as np

from .music_reactivity import MusicalSignals
from .music_structure import MusicStructure
from .performance_control import ControlEvent


_QUANTIZED_ACTIONS = {"cue", "next", "journey", "snapshot_load"}


@dataclass(frozen=True)
class PendingControlEvent:
    due: float
    event: ControlEvent


class PerformanceQuantizer:
    """Schedule scene-changing actions to musical beat/bar boundaries."""

    def __init__(self, mode: str = "off") -> None:
        self.mode = "off"
        self._pending: list[PendingControlEvent] = []
        self.set_mode(mode)

    def set_mode(self, mode: str) -> None:
        if mode not in {"off", "beat", "bar"}:
            raise ValueError(f"unknown performance quantize mode: {mode}")
        self.mode = mode

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    def _delay(self, signals: MusicalSignals) -> float:
        if self.mode == "off" or signals.beat_confidence < 0.18 or signals.tempo_bpm <= 0.0:
            return 0.0
        beat_seconds = 60.0 / float(np.clip(signals.tempo_bpm, 30.0, 300.0))
        if self.mode == "beat":
            phase = float(np.clip(signals.beat_phase, 0.0, 1.0))
            if phase <= 0.04 or phase >= 0.985:
                return 0.0
            return (1.0 - phase) * beat_seconds
        phase = float(np.clip(signals.bar_phase, 0.0, 1.0))
        if phase <= 0.025 or phase >= 0.992:
            return 0.0
        return (1.0 - phase) * beat_seconds * 4.0

    def submit(self, event: ControlEvent, now: float, signals: MusicalSignals) -> bool:
        """Return True when the event should execute immediately; otherwise queue it."""
        if event.action not in _QUANTIZED_ACTIONS:
            return True
        delay = self._delay(signals)
        if delay <= 0.0:
            return True

        # A newly requested action of the same semantic type replaces stale pending intent.
        if event.action in {"cue", "next", "journey"}:
            self._pending = [
                item
                for item in self._pending
                if item.event.action not in {"cue", "next", "journey"}
            ]
        self._pending.append(PendingControlEvent(float(now) + delay, event))
        self._pending.sort(key=lambda item: item.due)
        return False

    def pop_due(self, now: float) -> list[ControlEvent]:
        now = float(now)
        due: list[ControlEvent] = []
        future: list[PendingControlEvent] = []
        for item in self._pending:
            (due if item.due <= now else future).append(item.event if item.due <= now else item)
        self._pending = [item for item in future if isinstance(item, PendingControlEvent)]
        return due

    def clear(self) -> None:
        self._pending.clear()


@dataclass(frozen=True)
class LoopEvent:
    offset_beats: float
    event: ControlEvent


class PerformanceCueLooper:
    """Record sparse performance actions in musical beats and loop them by bar length."""

    RECORDABLE_ACTIONS = {"cue", "next", "journey", "snapshot_load"}

    def __init__(self) -> None:
        self.recording = False
        self.playing = False
        self.events: list[LoopEvent] = []
        self.length_beats = 0.0
        self._record_start = 0.0
        self._play_origin = 0.0
        self._last_relative: float | None = None

    @staticmethod
    def beat_position(structure: MusicStructure, signals: MusicalSignals) -> float:
        return float(structure.bars_seen) * 4.0 + float(np.clip(signals.bar_phase, 0.0, 1.0)) * 4.0

    def start_record(self, beat_position: float) -> None:
        self.recording = True
        self.playing = False
        self.events.clear()
        self.length_beats = 0.0
        self._record_start = float(beat_position)
        self._last_relative = None

    def record(self, event: ControlEvent, beat_position: float) -> None:
        if not self.recording or event.action not in self.RECORDABLE_ACTIONS:
            return
        offset = max(0.0, float(beat_position) - self._record_start)
        self.events.append(LoopEvent(offset, event))

    def stop_record(self, beat_position: float, *, auto_play: bool = True) -> None:
        if not self.recording:
            return
        elapsed = max(0.25, float(beat_position) - self._record_start)
        self.length_beats = max(4.0, math.ceil(elapsed / 4.0) * 4.0)
        self.recording = False
        self.events = [
            LoopEvent(float(np.clip(item.offset_beats, 0.0, self.length_beats - 1e-6)), item.event)
            for item in self.events
        ]
        self.events.sort(key=lambda item: item.offset_beats)
        self.playing = bool(auto_play and self.events)
        self._play_origin = float(beat_position)
        self._last_relative = None

    def start_play(self, beat_position: float) -> None:
        if not self.events or self.length_beats <= 0.0:
            return
        self.playing = True
        self._play_origin = float(beat_position)
        self._last_relative = None

    def stop(self) -> None:
        self.recording = False
        self.playing = False
        self._last_relative = None

    def clear(self) -> None:
        self.stop()
        self.events.clear()
        self.length_beats = 0.0

    def tick(self, beat_position: float) -> list[ControlEvent]:
        if not self.playing or not self.events or self.length_beats <= 0.0:
            return []

        relative = max(0.0, float(beat_position) - self._play_origin)
        if self._last_relative is None:
            self._last_relative = relative - 1e-6
        previous = self._last_relative
        self._last_relative = relative
        if relative < previous:
            return []

        emitted: list[ControlEvent] = []
        # Bound catch-up if a machine stalls or the musical clock jumps.
        lower = max(previous, relative - self.length_beats * 2.0)
        for item in self.events:
            first_cycle = math.floor((lower - item.offset_beats) / self.length_beats) + 1
            cycle = max(0, first_cycle)
            occurrence = item.offset_beats + cycle * self.length_beats
            while occurrence <= relative + 1e-9 and len(emitted) < 128:
                if occurrence > lower + 1e-9:
                    emitted.append(item.event)
                cycle += 1
                occurrence = item.offset_beats + cycle * self.length_beats
        return emitted


__all__ = [
    "LoopEvent",
    "PendingControlEvent",
    "PerformanceCueLooper",
    "PerformanceQuantizer",
]

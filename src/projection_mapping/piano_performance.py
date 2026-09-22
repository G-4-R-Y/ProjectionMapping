from __future__ import annotations

from dataclasses import dataclass
import math
import threading
import time
from typing import Any

import numpy as np

@dataclass(frozen=True)
class PianoExpression:
    pitch: float = 0.5
    velocity: float = 0.0
    strike: float = 0.0
    density: float = 0.0
    spread: float = 0.0
    sustain: float = 0.0
    soft: float = 0.0
    pressure: float = 0.0
    bend: float = 0.0
    tension: float = 0.0
    chord: str = "silence"
    active_notes: tuple[int, ...] = ()


def _recognize_chord(notes: tuple[int, ...]) -> tuple[str, float]:
    """Return a coarse chord family + visual tension in [0, 1].

    The goal is expressive visual classification, not exhaustive harmonic analysis.
    Inversions are recognized by trying every active pitch class as a possible root.
    """
    pcs = sorted({int(note) % 12 for note in notes})
    if not pcs:
        return "silence", 0.0
    if len(pcs) == 1:
        return "single", 0.08
    if len(pcs) == 2:
        interval = (pcs[1] - pcs[0]) % 12
        if interval in {5, 7}:
            return "open", 0.14
        if interval in {1, 2, 10, 11}:
            return "cluster", 0.68
        return "dyad", 0.30

    patterns: tuple[tuple[str, frozenset[int], float], ...] = (
        ("major7", frozenset({0, 4, 7, 11}), 0.34),
        ("dominant7", frozenset({0, 4, 7, 10}), 0.52),
        ("minor7", frozenset({0, 3, 7, 10}), 0.38),
        ("major", frozenset({0, 4, 7}), 0.22),
        ("minor", frozenset({0, 3, 7}), 0.28),
        ("sus2", frozenset({0, 2, 7}), 0.34),
        ("sus4", frozenset({0, 5, 7}), 0.36),
        ("diminished", frozenset({0, 3, 6}), 0.86),
        ("augmented", frozenset({0, 4, 8}), 0.76),
    )
    pc_set = set(pcs)
    for root in pcs:
        intervals = frozenset((pc - root) % 12 for pc in pc_set)
        for name, pattern, tension in patterns:
            if pattern <= intervals:
                extra = max(0, len(intervals) - len(pattern))
                return name, float(np.clip(tension + extra * 0.08, 0.0, 1.0))

    distances = sorted((pcs[(i + 1) % len(pcs)] - pcs[i]) % 12 for i in range(len(pcs)))
    small_steps = sum(1 for distance in distances if distance <= 2)
    tension = 0.45 + 0.12 * small_steps + 0.05 * max(0, len(pcs) - 3)
    return ("cluster" if small_steps >= 2 else "complex"), float(np.clip(tension, 0.0, 1.0))


class PianoMIDIInterpreter:
    """Translate ordinary piano playing into continuous visual expression.

    All playable notes shape pitch/color, velocity/strike, polyphonic density, register spread,
    harmonic tension and sustain. Optional low-key hot cues are deliberately off by default so an
    88-key performance is not interrupted by accidental scene changes.
    """

    def __init__(
        self,
        bus: Any | None = None,
        *,
        hot_cues: bool = False,
        cue_note_base: int = 21,
        cue_names: tuple[str, ...] = (
            "liquid_intro",
            "membrane_drift",
            "data_build",
            "mercury_rise",
            "cathedral_release",
            "reactor_release",
            "singularity_drop",
            "afterglow",
        ),
    ) -> None:
        self.bus = bus
        self.hot_cues = bool(hot_cues)
        self.cue_note_base = int(np.clip(cue_note_base, 0, 120))
        self.cue_names = tuple(cue_names)
        self._lock = threading.Lock()
        self._held: dict[int, int] = {}
        self._latched: dict[int, int] = {}
        self._sustain = 0.0
        self._soft = 0.0
        self._pressure = 0.0
        self._bend = 0.0
        self._expression = 1.0
        self._last_strike = 0.0
        self._last_strike_time = -999.0

    def _note_off(self, note: int) -> None:
        velocity = self._held.pop(note, None)
        if velocity is None:
            return
        if self._sustain >= 0.5:
            self._latched[note] = velocity
        else:
            self._latched.pop(note, None)

    def feed(self, message: Any, *, now: float | None = None) -> bool:
        now = time.perf_counter() if now is None else float(now)
        msg_type = str(getattr(message, "type", ""))
        with self._lock:
            if msg_type == "note_on":
                note = int(getattr(message, "note", 0))
                velocity = int(getattr(message, "velocity", 0))
                if velocity <= 0:
                    self._note_off(note)
                    return True
                self._held[note] = velocity
                self._latched.pop(note, None)
                self._last_strike = velocity / 127.0
                self._last_strike_time = now
                if (
                    self.hot_cues
                    and self.bus is not None
                    and self.cue_note_base <= note < self.cue_note_base + len(self.cue_names)
                ):
                    self.bus.emit("cue", self.cue_names[note - self.cue_note_base])
                return True

            if msg_type == "note_off":
                self._note_off(int(getattr(message, "note", 0)))
                return True

            if msg_type == "control_change":
                control = int(getattr(message, "control", -1))
                value = float(np.clip(int(getattr(message, "value", 0)) / 127.0, 0.0, 1.0))
                if control == 64:  # sustain
                    previous = self._sustain
                    self._sustain = value
                    if previous >= 0.5 and value < 0.5:
                        self._latched.clear()
                    return True
                if control == 67:  # soft pedal
                    self._soft = value
                    return True
                if control == 11:  # expression pedal
                    self._expression = value
                    return True
                return False

            if msg_type in {"aftertouch", "polytouch"}:
                self._pressure = float(
                    np.clip(int(getattr(message, "value", 0)) / 127.0, 0.0, 1.0)
                )
                return True

            if msg_type == "pitchwheel":
                self._bend = float(
                    np.clip(int(getattr(message, "pitch", 0)) / 8192.0, -1.0, 1.0)
                )
                return True
        return False

    def expression(self, *, now: float | None = None) -> PianoExpression:
        now = time.perf_counter() if now is None else float(now)
        with self._lock:
            sounding = dict(self._latched)
            sounding.update(self._held)
            notes = tuple(sorted(sounding))
            velocities = tuple(sounding[note] / 127.0 for note in notes)
            sustain = self._sustain
            soft = self._soft
            pressure = self._pressure
            bend = self._bend
            expression = self._expression
            strike = self._last_strike * math.exp(-max(0.0, now - self._last_strike_time) / 0.42)

        if not notes:
            return PianoExpression(
                velocity=0.0,
                strike=float(strike),
                sustain=sustain,
                soft=soft,
                pressure=pressure,
                bend=bend,
            )

        weights = np.asarray(velocities, dtype=np.float32)
        pitch_values = np.asarray(notes, dtype=np.float32)
        weighted_pitch = float(np.average(pitch_values, weights=np.maximum(weights, 0.05)))
        pitch = float(np.clip((weighted_pitch - 21.0) / 87.0, 0.0, 1.0))
        velocity = float(np.clip(np.mean(weights) * expression, 0.0, 1.0))
        density = float(np.clip(len(notes) / 10.0, 0.0, 1.0))
        spread = float(np.clip((max(notes) - min(notes)) / 48.0, 0.0, 1.0))
        chord, tension = _recognize_chord(notes)
        tension = float(np.clip(tension + density * 0.10 + abs(bend) * 0.08, 0.0, 1.0))

        return PianoExpression(
            pitch=pitch,
            velocity=velocity,
            strike=float(np.clip(strike, 0.0, 1.0)),
            density=density,
            spread=spread,
            sustain=sustain,
            soft=soft,
            pressure=pressure,
            bend=bend,
            tension=tension,
            chord=chord,
            active_notes=notes,
        )


__all__ = ["PianoExpression", "PianoMIDIInterpreter"]

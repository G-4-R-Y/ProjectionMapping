"""Optional Fosfora Signal v1 OSC musical telemetry adapter."""
from __future__ import annotations
import math
import threading
import time
from .music_reactivity import MusicalSignals

SILENT_SIGNALS = MusicalSignals(0, 0, 0, 0, .5, 0, 0, 0)
_PREFIX = "/fosfora/v1/"
_VALUES = frozenset(("energy", "build", "bpm", "bpm/confidence", "bpm/locked",
"bar_phase", "stem/drums/energy", "stem/bass/energy", "stem/melody/energy",
"feat/centroid", "feat/beat_phase"))
_COUNTS = frozenset(("beat", "downbeat", "drop"))
_IMPULSES = frozenset(("onset", "stem/drums/onset"))

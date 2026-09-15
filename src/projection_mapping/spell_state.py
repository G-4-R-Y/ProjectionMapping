from __future__ import annotations

from dataclasses import dataclass
import math

from .performer_rig import GestureState


@dataclass(frozen=True)
class SpellState:
    phase: str = "idle"
    charge: float = 0.0
    release_energy: float = 0.0
    shield_energy: float = 0.0
    ascension_energy: float = 0.0
    cast_energy: float = 0.0


class SpellStateMachine:
    """Turns noisy frame-level gestures into intentional temporal spell events."""

    def __init__(
        self,
        charge_seconds: float = 0.65,
        minimum_release_charge: float = 0.25,
        cast_cooldown: float = 0.35,
    ) -> None:
        self.charge_seconds = max(float(charge_seconds), 0.05)
        self.minimum_release_charge = float(minimum_release_charge)
        self.cast_cooldown = max(float(cast_cooldown), 0.05)
        self._charge = 0.0
        self._release = 0.0
        self._shield = 0.0
        self._ascension = 0.0
        self._cast = 0.0
        self._hands_together = False
        self._arms_spread = False
        self._hands_raised = False
        self._cast_timer = 999.0

    def update(self, gestures: GestureState, dt: float) -> SpellState:
        dt = min(max(float(dt), 1e-4), 0.2)
        self._cast_timer += dt

        phase = "idle"
        if gestures.hands_together:
            self._charge = min(1.0, self._charge + dt / self.charge_seconds)
            phase = "charged" if self._charge >= 0.98 else "charging"
        else:
            if self._hands_together and self._charge >= self.minimum_release_charge:
                self._release = max(self._release, self._charge)
                phase = "release"
            self._charge *= math.exp(-dt * 2.2)

        if gestures.arms_spread:
            self._shield = min(1.0, self._shield + dt * 3.2)
            phase = "shield" if phase == "idle" else phase
        else:
            self._shield *= math.exp(-dt * 4.0)

        if gestures.hands_raised:
            self._ascension = min(1.0, self._ascension + dt * 2.6)
            phase = "ascension" if phase == "idle" else phase
        else:
            self._ascension *= math.exp(-dt * 3.2)

        if gestures.motion_burst and self._cast_timer >= self.cast_cooldown and not gestures.hands_together:
            self._cast = max(self._cast, min(1.0, 0.35 + gestures.motion_energy * 1.8))
            self._cast_timer = 0.0
            if phase == "idle":
                phase = "cast"

        self._release *= math.exp(-dt * 5.0)
        self._cast *= math.exp(-dt * 6.5)
        self._hands_together = gestures.hands_together
        self._arms_spread = gestures.arms_spread
        self._hands_raised = gestures.hands_raised

        return SpellState(
            phase=phase,
            charge=float(self._charge),
            release_energy=float(self._release),
            shield_energy=float(self._shield),
            ascension_energy=float(self._ascension),
            cast_energy=float(self._cast),
        )

from projection_mapping.performer_rig import GestureState
from projection_mapping.spell_state import SpellStateMachine


def test_charge_then_release_emits_release_energy():
    sm = SpellStateMachine(charge_seconds=0.2, minimum_release_charge=0.1)
    state = None
    for _ in range(4):
        state = sm.update(GestureState(hands_together=True), 0.06)
    assert state is not None and state.charge > 0.8
    released = sm.update(GestureState(hands_together=False), 0.02)
    assert released.release_energy > 0.5


def test_arms_spread_builds_shield():
    sm = SpellStateMachine()
    state = sm.update(GestureState(arms_spread=True), 0.1)
    assert state.shield_energy > 0

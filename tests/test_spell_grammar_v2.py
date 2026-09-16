from projection_mapping.performance_bus import AnchorState, TrackingState, Vec3
from projection_mapping.spell_grammar import SpellGrammar


def anchor(name: str, x: float, y: float, vx: float = 0.0, vy: float = 0.0):
    return AnchorState(name, Vec3(x, y), Vec3(vx, vy), confidence=0.95, source="test")


def state(t: float, *anchors: AnchorState):
    return TrackingState(t, (640, 360), anchors=anchors, source="test")


def test_charge_then_separation_releases():
    grammar = SpellGrammar()
    for i in range(8):
        s = grammar.update(
            state(
                1.0 + i * 0.08,
                anchor("left_palm", 0.44, 0.50),
                anchor("right_palm", 0.56, 0.50),
            )
        )
    assert any(e.name == "charge_orb" and e.strength > 0.8 for e in s.gestures)

    released = grammar.update(
        state(
            1.75,
            anchor("left_palm", 0.25, 0.50),
            anchor("right_palm", 0.75, 0.50),
        )
    )
    assert any(e.name == "charge_release" for e in released.gestures)


def test_fast_palm_emits_slash():
    grammar = SpellGrammar()
    result = grammar.update(state(1.0, anchor("left_palm", 0.3, 0.5, vx=1.8, vy=0.2)))
    event = next(e for e in result.gestures if e.name == "slash_trail")
    assert event.source_anchor == "left_palm"
    assert event.strength > 0.35


def test_raised_wrists_emit_ascension():
    grammar = SpellGrammar()
    result = grammar.update(
        state(
            1.0,
            anchor("head", 0.5, 0.35),
            anchor("left_wrist", 0.35, 0.28),
            anchor("right_wrist", 0.65, 0.27),
        )
    )
    assert any(e.name == "ascension_aura" and e.phase == "begin" for e in result.gestures)


def test_missing_hands_never_invents_hand_spell():
    grammar = SpellGrammar()
    result = grammar.update(state(1.0, anchor("head", 0.5, 0.3)))
    names = {e.name for e in result.gestures}
    assert "charge_orb" not in names
    assert "charge_release" not in names
    assert "shield_dome" not in names

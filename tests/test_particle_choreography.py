from projection_mapping.gpu_particles import GPUParticleField
from projection_mapping.music_reactivity import MusicalSignals
from projection_mapping.particle_choreography import BANKS, blend_choreographies, choreography


def signals(**kwargs):
    values = {
        "loudness": 0.4,
        "bass": 0.5,
        "mids": 0.3,
        "highs": 0.2,
        "color": 0.4,
        "strike": 0.0,
        "beat": 0.0,
        "ascension": 0.0,
        "tempo_bpm": 120.0,
        "beat_phase": 0.25,
        "bar_phase": 0.31,
        "beat_confidence": 0.9,
        "section_energy": 0.4,
        "drop": 0.0,
    }
    values.update(kwargs)
    return MusicalSignals(**values)


def test_every_bank_produces_emitters_and_valid_parameters():
    s = signals()
    for bank in BANKS:
        c = choreography(bank, s, t=1.0, madness=0.5)
        assert c.emitters
        assert c.emission_rate >= 0.0
        assert 0.0 <= c.feedback <= 1.0
        assert c.palette in GPUParticleField.PALETTES
        assert c.material in GPUParticleField.MATERIALS
        for emitter in c.emitters:
            assert 0.0 <= emitter.x <= 1.0
            assert 0.0 <= emitter.y <= 1.0
            assert emitter.energy >= 0.0


def test_drop_expands_vortex_emission_rate():
    quiet = choreography("vortex_gate", signals(drop=0.0), t=2.0)
    drop = choreography("vortex_gate", signals(drop=1.0), t=2.0)
    assert drop.emission_rate > quiet.emission_rate


def test_constellation_is_sparse_until_accents():
    quiet = choreography("constellation_bloom", signals(loudness=0.1, strike=0.0, drop=0.0), t=3.0)
    accent = choreography("constellation_bloom", signals(loudness=0.1, strike=1.0, drop=1.0), t=3.0)
    assert accent.emission_rate > quiet.emission_rate * 5.0


def test_drop_can_switch_reactor_to_shock_ring_material():
    quiet = choreography("reactor_bloom", signals(drop=0.0), t=2.0)
    drop = choreography("reactor_bloom", signals(drop=1.0), t=2.0)
    assert quiet.material == "plasma"
    assert drop.material == "shock_ring"


def test_choreography_blend_preserves_eight_emitter_budget_and_interpolates():
    source = choreography("helix_fountain", signals(), t=2.0)
    target = choreography("techno_lattice", signals(), t=2.0)
    blended = blend_choreographies(source, target, 0.25)

    assert 0 < len(blended.emitters) <= 8
    assert blended.emission_rate == source.emission_rate + 0.25 * (
        target.emission_rate - source.emission_rate
    )
    assert blended.palette == source.palette
    assert blended.emitters[0].x == source.emitters[0].x + 0.25 * (
        target.emitters[0].x - source.emitters[0].x
    )


def test_choreography_blend_reaches_target_exactly():
    source = choreography("nebula_bloom", signals(), t=1.0)
    target = choreography("polar_gate", signals(), t=1.0)

    assert blend_choreographies(source, target, 1.0) == target

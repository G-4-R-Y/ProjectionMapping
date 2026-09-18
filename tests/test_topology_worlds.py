from projection_mapping.topology_worlds import TOPOLOGY_MODES, TOPOLOGY_PALETTES


def test_topology_world_modes_are_stable():
    assert TOPOLOGY_MODES == (
        "torus_knot",
        "hopf_link_field",
        "gyroid",
        "schwarz_p",
        "helicoid",
        "mobius_ribbon",
    )
    assert len(set(TOPOLOGY_MODES)) == len(TOPOLOGY_MODES)


def test_topology_worlds_have_projector_palettes():
    assert len(TOPOLOGY_PALETTES) >= 6

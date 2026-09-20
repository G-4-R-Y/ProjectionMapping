from projection_mapping.point_sfx import PALETTES, PointSFXRenderer


def test_performance_palettes_are_rgb_quads():
    expected = {"cyan_magenta", "ultraviolet", "deep_ocean", "sunset_neon"}
    assert expected <= set(PALETTES)
    for name in expected:
        palette = PALETTES[name]
        assert len(palette) == 4
        assert all(len(rgb) == 3 for rgb in palette)
        assert all(0 <= channel <= 255 for rgb in palette for channel in rgb)


def test_cyan_magenta_palette_is_selectable():
    renderer = PointSFXRenderer(64, 36, palette="cyan_magenta")
    assert renderer.palette_name == "cyan_magenta"
    assert renderer.palette[0] == (0, 245, 255)
    assert renderer.palette[1] == (255, 0, 210)

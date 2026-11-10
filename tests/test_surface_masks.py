import json

import numpy as np
import pytest

from projection_mapping.surface_masks import apply_surface_mask, load_surface_mask


def write(tmp_path, outlines, space="normalized"):
    path = tmp_path / "surface.json"
    path.write_text(json.dumps({"space": space, "outlines": outlines}), encoding="utf-8")
    return path


def test_polygon_even_odd_hole_and_black_floor(tmp_path):
    outer = [[0.1, 0.1], [0.9, 0.1], [0.9, 0.9], [0.1, 0.9]]
    inner = [[0.4, 0.4], [0.6, 0.4], [0.6, 0.6], [0.4, 0.6]]
    mask = load_surface_mask(write(tmp_path, [outer, inner]), 101, 101)
    assert mask.dtype == np.float32 and mask.shape == (101, 101)
    assert mask[20, 20] == 1 and mask[50, 50] == 0 and mask[2, 2] == 0
    frame = np.full((101, 101, 3), 245, np.uint8)
    result = apply_surface_mask(frame, mask)
    assert result[20, 20].tolist() == [245, 245, 245]
    assert result[50, 50].tolist() == [0, 0, 0]
    assert result[2, 2].tolist() == [0, 0, 0]


def test_feather_only_inside_and_no_leakage(tmp_path):
    outline = [[0.2, 0.2], [0.8, 0.2], [0.8, 0.8], [0.2, 0.8]]
    path = write(tmp_path, [outline])
    hard = load_surface_mask(path, 101, 101)
    soft = load_surface_mask(path, 101, 101, feather_px=8)
    assert hard[21, 50] == 1
    assert 0 < soft[21, 50] < 1
    assert soft[50, 50] == 1
    assert soft[19, 50] == 0 and soft[0, 0] == 0
    assert soft.min() == 0 and soft.max() == 1


@pytest.mark.parametrize("outlines", [
    [], [[[0, 0], [1, 0]]],
    [[[0, 0], [0.5, 0.5], [1, 1]]],
    [[[0, 0], [1, 0], [float('nan'), 1]]],
    [[[0, 0], [1, 0], [True, 1]]],
    [[[0, 0], [1.2, 0], [0, 1]]],
])
def test_reject_malformed_polygons(tmp_path, outlines):
    with pytest.raises(ValueError):
        load_surface_mask(write(tmp_path, outlines), 101, 101)


def test_reject_invalid_specs(tmp_path):
    path = write(tmp_path, [[[0, 0], [1, 0], [0, 1]]], space="pixels")
    with pytest.raises(ValueError, match="space"):
        load_surface_mask(path, 100, 100)
    path = write(tmp_path, [[[0, 0], [1, 0], [0, 1]]])
    with pytest.raises(ValueError, match="feather"):
        load_surface_mask(path, 100, 100, feather_px=-1)
    with pytest.raises(ValueError, match="dimensions"):
        load_surface_mask(path, 0, 100)
    with pytest.raises(ValueError, match="Mask"):
        apply_surface_mask(np.zeros((100, 100, 3), np.uint8), np.ones((20, 20)))


def test_grayscale_frame(tmp_path):
    m = load_surface_mask(write(tmp_path, [[[0, 0], [1, 0], [0, 1]]]), 17, 17)
    out = apply_surface_mask(np.full((17, 17), 255, np.uint8), m)
    assert out.shape == (17, 17) and out.dtype == np.uint8
    assert out[16, 16] == 0

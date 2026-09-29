from __future__ import annotations

import numpy as np
import pytest

from projection_mapping.surface_mask import (
    SurfaceMaskProcessor,
    SurfaceMaskSpec,
    apply_surface_alpha,
    build_surface_alpha,
)


def test_empty_spec_keeps_full_frame() -> None:
    alpha = build_surface_alpha(9, 7, SurfaceMaskSpec())
    np.testing.assert_array_equal(alpha, np.ones((7, 9), dtype=np.float32))


def test_edge_feather_reaches_black_at_border_and_full_alpha_inside() -> None:
    alpha = build_surface_alpha(11, 11, SurfaceMaskSpec(edge_feather_px=2.0))
    assert alpha[0, 5] == pytest.approx(0.0)
    assert alpha[1, 5] == pytest.approx(0.5)
    assert alpha[5, 5] == pytest.approx(1.0)


def test_polygon_is_defined_in_normalized_output_space() -> None:
    spec = SurfaceMaskSpec(
        polygon=((0.25, 0.25), (0.75, 0.25), (0.75, 0.75), (0.25, 0.75)),
        polygon_feather_px=2.0,
    )
    alpha = build_surface_alpha(21, 21, spec)
    assert alpha[10, 10] == pytest.approx(1.0)
    assert alpha[0, 0] == pytest.approx(0.0)
    assert 0.0 < alpha[6, 10] < 1.0


def test_output_mask_does_not_depend_on_source_content_or_source_warp() -> None:
    spec = SurfaceMaskSpec(
        polygon=((0.1, 0.2), (0.9, 0.2), (0.8, 0.85), (0.2, 0.9)),
        edge_feather_px=3.0,
    )
    alpha = build_surface_alpha(32, 18, spec)
    source_a = np.ones((18, 32, 3), dtype=np.float32)
    source_b = np.roll(source_a * 2.0, shift=7, axis=1)
    expected = np.repeat(alpha[..., None], 3, axis=2)

    masked_a = apply_surface_alpha(source_a, alpha)
    masked_b = apply_surface_alpha(source_b, alpha)

    np.testing.assert_allclose(masked_a, expected)
    np.testing.assert_allclose(masked_b / 2.0, expected)


def test_background_composite_preserves_dtype() -> None:
    frame = np.full((4, 5, 3), 200, dtype=np.uint8)
    background = np.full_like(frame, 20)
    alpha = np.full((4, 5), 0.25, dtype=np.float32)
    out = apply_surface_alpha(frame, alpha, background=background)
    assert out.dtype == np.uint8
    np.testing.assert_array_equal(out, np.full_like(frame, 65))


def test_processor_caches_alpha() -> None:
    processor = SurfaceMaskProcessor(8, 6, SurfaceMaskSpec(edge_feather_px=1.0))
    frame = np.full((6, 8, 3), 255, dtype=np.uint8)
    out = processor(frame)
    assert out.shape == frame.shape
    assert out[0, 4].max() == 0
    assert out[3, 4].min() == 255


@pytest.mark.parametrize(
    "spec",
    (
        SurfaceMaskSpec(edge_feather_px=-1.0),
        SurfaceMaskSpec(polygon_feather_px=-1.0),
    ),
)
def test_negative_feather_is_rejected(spec: SurfaceMaskSpec) -> None:
    with pytest.raises(ValueError):
        build_surface_alpha(10, 10, spec)


def test_degenerate_polygon_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_surface_alpha(
            10,
            10,
            SurfaceMaskSpec(polygon=((0.1, 0.1), (0.2, 0.2), (0.3, 0.3))),
        )

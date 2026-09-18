from __future__ import annotations

import numpy as np
import pytest

from projection_mapping.surface_mapping import (
    MappedSurface,
    SurfaceMapProcessor,
    SurfaceMapProfile,
    SurfaceMapRenderer,
    render_surface_map,
    surface_alpha,
)


def test_profile_roundtrip_preserves_normalized_surface_geometry(tmp_path):
    profile = SurfaceMapProfile(
        name="studio_wall",
        projector_width=1920,
        projector_height=1080,
        surfaces=[
            MappedSurface(
                name="left_panel",
                projector_corners=((0.05, 0.1), (0.48, 0.04), (0.52, 0.92), (0.08, 0.86)),
                feather=0.02,
            )
        ],
    )
    path = profile.save(tmp_path / "maps" / "wall.json")
    loaded = SurfaceMapProfile.load(path)

    assert loaded == profile
    assert path.read_text(encoding="utf-8").endswith("\n")


def test_identity_surface_map_preserves_content_without_feathering():
    rng = np.random.default_rng(7)
    frame = rng.integers(0, 256, (48, 64, 3), dtype=np.uint8)
    profile = SurfaceMapProfile(
        projector_width=64,
        projector_height=48,
        surfaces=[MappedSurface(feather=0.0)],
    )

    mapped = render_surface_map(frame, profile)

    assert mapped.shape == frame.shape
    assert np.array_equal(mapped, frame)


def test_inset_surface_masks_pixels_outside_projector_quad():
    frame = np.full((40, 60, 3), 200, dtype=np.uint8)
    surface = MappedSurface(
        projector_corners=((0.25, 0.25), (0.75, 0.25), (0.75, 0.75), (0.25, 0.75)),
        feather=0.0,
    )
    profile = SurfaceMapProfile(projector_width=120, projector_height=80, surfaces=[surface])

    mapped = render_surface_map(frame, profile)

    assert np.all(mapped[0, 0] == 0)
    assert np.all(mapped[40, 60] >= 195)


def test_feather_produces_soft_edge_and_opaque_interior():
    surface = MappedSurface(feather=0.10)
    alpha = surface_alpha(surface, width=100, height=100)

    assert 0.0 < alpha[1, 50] < 0.5
    assert alpha[50, 50] == pytest.approx(1.0)
    assert alpha.min() >= 0.0
    assert alpha.max() <= 1.0


def test_normalized_profile_scales_to_a_different_projector_resolution():
    frame = np.full((12, 16, 3), 255, dtype=np.uint8)
    surface = MappedSurface(
        projector_corners=((0.0, 0.0), (0.5, 0.0), (0.5, 1.0), (0.0, 1.0)),
        feather=0.0,
    )
    profile = SurfaceMapProfile(projector_width=80, projector_height=40, surfaces=[surface])
    mapped = SurfaceMapProcessor(profile)(frame)

    assert mapped.shape == (40, 80, 3)
    assert mapped[:, 10].mean() > 240
    assert mapped[:, 70].max() == 0


def test_cached_renderer_rebuilds_after_live_corner_edit():
    frame = np.full((24, 32, 3), 255, dtype=np.uint8)
    surface = MappedSurface(feather=0.0)
    profile = SurfaceMapProfile(projector_width=64, projector_height=48, surfaces=[surface])
    renderer = SurfaceMapRenderer(profile)
    full = renderer.render(frame)

    surface.projector_corners = ((0.0, 0.0), (0.5, 0.0), (0.5, 1.0), (0.0, 1.0))
    half = renderer.render(frame)

    assert full[:, 55].mean() > 240
    assert half[:, 55].max() == 0


def test_degenerate_surface_is_rejected():
    with pytest.raises(ValueError, match="degenerate"):
        MappedSurface(projector_corners=((0.0, 0.0),) * 4)

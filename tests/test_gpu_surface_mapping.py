from __future__ import annotations

import numpy as np
import pytest

from projection_mapping.gpu_surface_mapping import (
    GPUSurfaceCompositor,
    ShaderScenePass,
    homography_matrix,
)
from projection_mapping.surface_mapping import MappedSurface, SurfaceMapProfile


def _apply(matrix: np.ndarray, points: np.ndarray) -> np.ndarray:
    homogeneous = np.column_stack((points, np.ones(len(points))))
    mapped = (matrix @ homogeneous.T).T
    return mapped[:, :2] / mapped[:, 2:]


def test_homography_maps_unit_square_to_projector_quad():
    source = np.asarray(((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)))
    destination = np.asarray(((0.08, 0.12), (0.91, 0.04), (0.82, 0.94), (0.15, 0.83)))
    matrix = homography_matrix(source, destination)

    assert np.allclose(_apply(matrix, source), destination, atol=1e-9)
    assert np.allclose(_apply(np.linalg.inv(matrix), destination), source, atol=1e-9)


def test_homography_rejects_degenerate_quad():
    source = np.zeros((4, 2))
    destination = np.asarray(((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)))

    try:
        homography_matrix(source, destination)
    except ValueError as exc:
        assert "stable homography" in str(exc)
    else:
        raise AssertionError("degenerate homography was accepted")


def test_gpu_compositor_and_promoted_scene_compile_and_render():
    pytest.importorskip("moderngl")
    from projection_mapping.graphics_runtime import create_context

    try:
        context, _info = create_context(require=330)
    except RuntimeError as exc:
        pytest.skip(str(exc))

    profile = SurfaceMapProfile(
        projector_width=96,
        projector_height=54,
        surfaces=[
            MappedSurface(
                projector_corners=((0.1, 0.1), (0.9, 0.06), (0.84, 0.92), (0.14, 0.86)),
                feather=0.02,
            )
        ],
    )
    scene = ShaderScenePass(context, 96, 54)
    mapper = GPUSurfaceCompositor(context, profile)
    target = context.texture((96, 54), 4, dtype="f1")
    framebuffer = context.framebuffer(color_attachments=[target])
    try:
        source = scene.render("liquid_chrome", t=0.8, intensity=1.0, chaos=1.15)
        mapper.render(source, 96, 54, target=framebuffer)
        pixels = np.frombuffer(framebuffer.read(components=4, alignment=1), dtype=np.uint8)
        pixels = pixels.reshape(54, 96, 4)
        assert pixels[..., :3].max() > 100
        assert pixels[..., :3].mean() > 2.0
        assert pixels[0, 0, :3].max() == 0
    finally:
        mapper.close()
        scene.close()
        framebuffer.release()
        target.release()
        context.release()

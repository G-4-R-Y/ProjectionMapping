import numpy as np
import pytest

from projection_mapping.mesh_assets import BUILTIN_MESHES, load_mesh_asset, make_builtin_mesh_asset


@pytest.mark.parametrize("name", BUILTIN_MESHES)
def test_builtin_meshes_are_nonempty_and_bounded(name):
    asset = load_mesh_asset(name)
    assert asset.primitives
    assert asset.path.as_posix() == name
    lo = np.asarray(asset.bounds_min, dtype=np.float32)
    hi = np.asarray(asset.bounds_max, dtype=np.float32)
    assert np.all(np.isfinite(lo))
    assert np.all(np.isfinite(hi))
    assert np.all(hi > lo)

    for primitive in asset.primitives:
        assert primitive.vertices.ndim == 2
        assert primitive.vertices.shape[1] == 3
        assert primitive.faces.ndim == 2
        assert primitive.faces.shape[1] == 3
        assert len(primitive.vertices) > 0
        assert len(primitive.faces) > 0
        assert primitive.normals is not None
        assert primitive.normals.shape == primitive.vertices.shape
        assert np.all(np.isfinite(primitive.normals))


def test_builtin_mesh_alias_without_prefix():
    asset = make_builtin_mesh_asset("crystal")
    assert asset.path.as_posix() == "builtin:crystal"


def test_unknown_builtin_mesh_has_actionable_error():
    with pytest.raises(ValueError, match="unknown built-in mesh"):
        make_builtin_mesh_asset("builtin:nope")

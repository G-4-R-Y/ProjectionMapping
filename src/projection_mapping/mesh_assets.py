from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class MeshPrimitive:
    name: str
    vertices: np.ndarray
    faces: np.ndarray
    normals: np.ndarray | None = None
    uv: np.ndarray | None = None


@dataclass(frozen=True)
class MeshAsset:
    path: Path
    primitives: tuple[MeshPrimitive, ...]
    bounds_min: tuple[float, float, float]
    bounds_max: tuple[float, float, float]


def load_mesh_asset(path: str | Path) -> MeshAsset:
    """Load GLB/glTF/OBJ/etc through the optional MIT-licensed trimesh backend.

    This keeps generated 3D assets out of renderer-specific code. A future renderer can upload
    these arrays to OpenGL/Vulkan while gameplay/mixed-reality code continues to reference the
    stable asset-pack ID.
    """
    try:
        import trimesh
    except ImportError as exc:
        raise RuntimeError(
            "3D asset ingestion requires the assets3d extra: "
            "`python -m pip install -e '.[assets3d]'`."
        ) from exc

    p = Path(path)
    loaded = trimesh.load(p, force="scene")
    geometries = getattr(loaded, "geometry", {})
    primitives: list[MeshPrimitive] = []
    mins: list[np.ndarray] = []
    maxs: list[np.ndarray] = []
    for name, mesh in geometries.items():
        vertices = np.asarray(mesh.vertices, dtype=np.float32)
        faces = np.asarray(mesh.faces, dtype=np.int32)
        normals = None
        if getattr(mesh, "vertex_normals", None) is not None and len(mesh.vertex_normals) == len(vertices):
            normals = np.asarray(mesh.vertex_normals, dtype=np.float32)
        uv = None
        visual = getattr(mesh, "visual", None)
        candidate_uv = getattr(visual, "uv", None) if visual is not None else None
        if candidate_uv is not None and len(candidate_uv) == len(vertices):
            uv = np.asarray(candidate_uv, dtype=np.float32)
        primitives.append(MeshPrimitive(str(name), vertices, faces, normals, uv))
        if len(vertices):
            mins.append(vertices.min(axis=0))
            maxs.append(vertices.max(axis=0))

    if not primitives:
        raise ValueError(f"no mesh primitives found in {p}")
    if mins:
        lo = np.min(np.stack(mins), axis=0)
        hi = np.max(np.stack(maxs), axis=0)
    else:
        lo = hi = np.zeros(3, dtype=np.float32)
    return MeshAsset(
        path=p,
        primitives=tuple(primitives),
        bounds_min=tuple(float(x) for x in lo),
        bounds_max=tuple(float(x) for x in hi),
    )


__all__ = ["MeshPrimitive", "MeshAsset", "load_mesh_asset"]

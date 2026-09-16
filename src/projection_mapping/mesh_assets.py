from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math

import numpy as np


BUILTIN_MESHES = ("builtin:cyber_orb", "builtin:energy_ring", "builtin:crystal")


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


def _vertex_normals(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    vertices = np.asarray(vertices, dtype=np.float32)
    faces = np.asarray(faces, dtype=np.int32)
    normals = np.zeros_like(vertices, dtype=np.float32)
    if len(faces):
        tri = vertices[faces]
        face_normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        lengths = np.linalg.norm(face_normals, axis=1, keepdims=True)
        face_normals /= np.maximum(lengths, 1e-8)
        for corner in range(3):
            np.add.at(normals, faces[:, corner], face_normals)
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    normals /= np.maximum(lengths, 1e-8)
    return normals.astype(np.float32)


def _asset_from_primitives(name: str, primitives: list[MeshPrimitive]) -> MeshAsset:
    mins: list[np.ndarray] = []
    maxs: list[np.ndarray] = []
    for primitive in primitives:
        if len(primitive.vertices):
            mins.append(np.asarray(primitive.vertices, dtype=np.float32).min(axis=0))
            maxs.append(np.asarray(primitive.vertices, dtype=np.float32).max(axis=0))
    if not primitives:
        raise ValueError(f"no primitives produced for {name}")
    if mins:
        lo = np.min(np.stack(mins), axis=0)
        hi = np.max(np.stack(maxs), axis=0)
    else:
        lo = hi = np.zeros(3, dtype=np.float32)
    return MeshAsset(
        path=Path(name),
        primitives=tuple(primitives),
        bounds_min=tuple(float(x) for x in lo),
        bounds_max=tuple(float(x) for x in hi),
    )


def _uv_sphere(rows: int = 22, cols: int = 44) -> MeshPrimitive:
    vertices: list[tuple[float, float, float]] = []
    uv: list[tuple[float, float]] = []
    for iy in range(rows + 1):
        v = iy / rows
        phi = math.pi * v
        sp, cp = math.sin(phi), math.cos(phi)
        for ix in range(cols + 1):
            u = ix / cols
            theta = math.tau * u
            # Slightly faceted/elongated silhouette reads better as a holographic summon.
            r = 1.0 + 0.055 * math.sin(theta * 6.0) * (sp**2)
            vertices.append((r * sp * math.cos(theta), cp * 1.08, r * sp * math.sin(theta)))
            uv.append((u, v))
    faces: list[tuple[int, int, int]] = []
    stride = cols + 1
    for iy in range(rows):
        for ix in range(cols):
            a = iy * stride + ix
            b = a + 1
            c = a + stride
            d = c + 1
            faces.append((a, c, b))
            faces.append((b, c, d))
    verts = np.asarray(vertices, dtype=np.float32)
    fs = np.asarray(faces, dtype=np.int32)
    return MeshPrimitive("cyber_orb", verts, fs, _vertex_normals(verts, fs), np.asarray(uv, dtype=np.float32))


def _torus(major: float = 0.82, minor: float = 0.19, rings: int = 56, sides: int = 18) -> MeshPrimitive:
    vertices: list[tuple[float, float, float]] = []
    uv: list[tuple[float, float]] = []
    for i in range(rings):
        u = i / rings
        a = math.tau * u
        ca, sa = math.cos(a), math.sin(a)
        for j in range(sides):
            v = j / sides
            b = math.tau * v
            cb, sb = math.cos(b), math.sin(b)
            radial = major + minor * cb
            vertices.append((radial * ca, minor * sb, radial * sa))
            uv.append((u, v))
    faces: list[tuple[int, int, int]] = []
    for i in range(rings):
        ni = (i + 1) % rings
        for j in range(sides):
            nj = (j + 1) % sides
            a = i * sides + j
            b = ni * sides + j
            c = i * sides + nj
            d = ni * sides + nj
            faces.append((a, b, c))
            faces.append((c, b, d))
    verts = np.asarray(vertices, dtype=np.float32)
    fs = np.asarray(faces, dtype=np.int32)
    return MeshPrimitive("energy_ring", verts, fs, _vertex_normals(verts, fs), np.asarray(uv, dtype=np.float32))


def _crystal() -> MeshPrimitive:
    # Two staggered rings plus poles: deliberately low-poly so normals create sharp, expensive-looking facets.
    vertices = np.asarray(
        [
            (0.0, 1.35, 0.0),
            (0.0, -1.35, 0.0),
            (0.72, 0.34, 0.0),
            (0.0, 0.34, 0.72),
            (-0.72, 0.34, 0.0),
            (0.0, 0.34, -0.72),
            (0.52, -0.36, 0.52),
            (-0.52, -0.36, 0.52),
            (-0.52, -0.36, -0.52),
            (0.52, -0.36, -0.52),
        ],
        dtype=np.float32,
    )
    faces = np.asarray(
        [
            (0, 2, 3), (0, 3, 4), (0, 4, 5), (0, 5, 2),
            (2, 6, 3), (3, 6, 7), (3, 7, 4), (4, 7, 8),
            (4, 8, 5), (5, 8, 9), (5, 9, 2), (2, 9, 6),
            (1, 7, 6), (1, 8, 7), (1, 9, 8), (1, 6, 9),
        ],
        dtype=np.int32,
    )
    return MeshPrimitive("crystal", vertices, faces, _vertex_normals(vertices, faces), None)


def make_builtin_mesh_asset(name: str) -> MeshAsset:
    key = str(name).strip().lower()
    if not key.startswith("builtin:"):
        key = f"builtin:{key}"
    if key == "builtin:cyber_orb":
        primitive = _uv_sphere()
    elif key == "builtin:energy_ring":
        primitive = _torus()
    elif key == "builtin:crystal":
        primitive = _crystal()
    else:
        raise ValueError(f"unknown built-in mesh {name!r}; choices: {', '.join(BUILTIN_MESHES)}")
    return _asset_from_primitives(key, [primitive])


def load_mesh_asset(path: str | Path) -> MeshAsset:
    """Load a built-in primitive or GLB/glTF/OBJ/etc through trimesh.

    `builtin:*` assets deliberately require no external file and are useful for graphics/pose
    validation before a generated asset pipeline is connected. Real files stay renderer-agnostic
    arrays so future OpenGL/Vulkan/WebGPU renderers can reuse the ingestion layer.
    """
    raw = str(path).strip()
    if raw.startswith("builtin:"):
        return make_builtin_mesh_asset(raw)

    try:
        import trimesh
    except ImportError as exc:
        raise RuntimeError(
            "3D asset ingestion requires the assets3d extra: "
            "`python -m pip install -e '.[assets3d]'`."
        ) from exc

    p = Path(raw).expanduser()
    if not p.exists():
        raise FileNotFoundError(
            f"3D asset does not exist: {p}. Supply a generated GLB/glTF/OBJ path or use one of: "
            + ", ".join(BUILTIN_MESHES)
        )
    if not p.is_file():
        raise ValueError(f"3D asset path is not a file: {p}")

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


__all__ = [
    "BUILTIN_MESHES",
    "MeshPrimitive",
    "MeshAsset",
    "make_builtin_mesh_asset",
    "load_mesh_asset",
]

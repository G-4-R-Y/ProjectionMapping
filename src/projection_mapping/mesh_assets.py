from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math

import numpy as np


BUILTIN_MESHES = (
    "builtin:cyber_orb",
    "builtin:energy_ring",
    "builtin:crystal",
    "builtin:relic",
    "builtin:drone",
    "builtin:sigil_totem",
    "builtin:summon_proxy",
)


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


def _transform_primitive(
    primitive: MeshPrimitive,
    *,
    name: str | None = None,
    scale=(1.0,1.0,1.0),
    translate=(0.0,0.0,0.0),
    rotate=(0.0,0.0,0.0),
) -> MeshPrimitive:
    v=np.asarray(primitive.vertices,dtype=np.float32).copy()
    sx,sy,sz=(float(x) for x in scale)
    rx,ry,rz=(float(x) for x in rotate)
    cx,sx_=math.cos(rx),math.sin(rx)
    cy,sy_=math.cos(ry),math.sin(ry)
    cz,sz_=math.cos(rz),math.sin(rz)
    Rx=np.array([[1,0,0],[0,cx,-sx_],[0,sx_,cx]],dtype=np.float32)
    Ry=np.array([[cy,0,sy_],[0,1,0],[-sy_,0,cy]],dtype=np.float32)
    Rz=np.array([[cz,-sz_,0],[sz_,cz,0],[0,0,1]],dtype=np.float32)
    v=(v*np.asarray([sx,sy,sz],dtype=np.float32))@(Rz@Ry@Rx).T
    v+=np.asarray(translate,dtype=np.float32)
    f=np.asarray(primitive.faces,dtype=np.int32).copy()
    n=_vertex_normals(v,f)
    uv=None if primitive.uv is None else np.asarray(primitive.uv,dtype=np.float32).copy()
    return MeshPrimitive(name or primitive.name,v,f,n,uv)


def _uv_sphere(rows: int = 22, cols: int = 44) -> MeshPrimitive:
    vertices: list[tuple[float, float, float]] = []
    uv: list[tuple[float, float]] = []
    for iy in range(rows + 1):
        vv = iy / rows
        phi = math.pi * vv
        sp, cp = math.sin(phi), math.cos(phi)
        for ix in range(cols + 1):
            u = ix / cols
            theta = math.tau * u
            r = 1.0 + 0.055 * math.sin(theta * 6.0) * (sp**2)
            vertices.append((r * sp * math.cos(theta), cp * 1.08, r * sp * math.sin(theta)))
            uv.append((u, vv))
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
            vv = j / sides
            b = math.tau * vv
            cb, sb = math.cos(b), math.sin(b)
            radial = major + minor * cb
            vertices.append((radial * ca, minor * sb, radial * sa))
            uv.append((u, vv))
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


def _relic() -> list[MeshPrimitive]:
    core=_transform_primitive(_crystal(),name="relic_core",scale=(.58,.72,.58))
    ring0=_transform_primitive(_torus(.82,.07,48,12),name="relic_ring_a",rotate=(math.pi*.5,0,0))
    ring1=_transform_primitive(_torus(.66,.055,44,10),name="relic_ring_b",rotate=(0,math.pi*.5,math.pi*.18))
    return [core,ring0,ring1]


def _drone() -> list[MeshPrimitive]:
    core=_transform_primitive(_uv_sphere(14,28),name="drone_core",scale=(.42,.28,.42))
    halo=_transform_primitive(_torus(.73,.075,44,12),name="drone_halo",rotate=(math.pi*.5,0,0))
    halo2=_transform_primitive(_torus(.54,.045,40,10),name="drone_halo2",rotate=(0,math.pi*.36,math.pi*.23))
    pods=[]
    for i in range(4):
        a=i*math.tau/4.0
        pods.append(_transform_primitive(_uv_sphere(8,14),name=f"drone_pod_{i}",scale=(.13,.13,.13),translate=(math.cos(a)*.82,math.sin(a)*.24,math.sin(a)*.82)))
    return [core,halo,halo2,*pods]


def _sigil_totem() -> list[MeshPrimitive]:
    core=_transform_primitive(_crystal(),name="totem_core",scale=(.34,.82,.34))
    rings=[]
    for i,(y,major) in enumerate(((-.62,.50),(0.0,.68),(.62,.50))):
        rings.append(_transform_primitive(_torus(major,.045,42,10),name=f"totem_ring_{i}",scale=(1,.75,1),translate=(0,y,0),rotate=(math.pi*.5,0,i*.31)))
    crown=_transform_primitive(_torus(.34,.055,36,10),name="totem_crown",translate=(0,.96,0),rotate=(0,math.pi*.5,0))
    return [core,*rings,crown]


def _summon_proxy() -> list[MeshPrimitive]:
    # Abstract creature proxy: faceted torso, head, horns/wings and orbit ring. Intentionally
    # stylized so generated character replacements can inherit the same transform/attachment path.
    torso=_transform_primitive(_crystal(),name="summon_torso",scale=(.42,.68,.32),translate=(0,-.18,0))
    head=_transform_primitive(_uv_sphere(10,20),name="summon_head",scale=(.28,.30,.28),translate=(0,.88,0))
    ring=_transform_primitive(_torus(.82,.04,44,10),name="summon_orbit",translate=(0,.10,0),rotate=(math.pi*.5,0,0))
    wing_l=_transform_primitive(_crystal(),name="summon_wing_l",scale=(.16,.52,.12),translate=(-.58,.12,0),rotate=(0,0,-.82))
    wing_r=_transform_primitive(_crystal(),name="summon_wing_r",scale=(.16,.52,.12),translate=(.58,.12,0),rotate=(0,0,.82))
    horn_l=_transform_primitive(_crystal(),name="summon_horn_l",scale=(.08,.24,.08),translate=(-.18,1.18,0),rotate=(0,0,-.28))
    horn_r=_transform_primitive(_crystal(),name="summon_horn_r",scale=(.08,.24,.08),translate=(.18,1.18,0),rotate=(0,0,.28))
    return [torso,head,ring,wing_l,wing_r,horn_l,horn_r]


def make_builtin_mesh_asset(name: str) -> MeshAsset:
    key = str(name).strip().lower()
    if not key.startswith("builtin:"):
        key = f"builtin:{key}"
    if key == "builtin:cyber_orb":
        primitives=[_uv_sphere()]
    elif key == "builtin:energy_ring":
        primitives=[_torus()]
    elif key == "builtin:crystal":
        primitives=[_crystal()]
    elif key == "builtin:relic":
        primitives=_relic()
    elif key == "builtin:drone":
        primitives=_drone()
    elif key == "builtin:sigil_totem":
        primitives=_sigil_totem()
    elif key == "builtin:summon_proxy":
        primitives=_summon_proxy()
    else:
        raise ValueError(f"unknown built-in mesh {name!r}; choices: {', '.join(BUILTIN_MESHES)}")
    return _asset_from_primitives(key, primitives)


def load_mesh_asset(path: str | Path) -> MeshAsset:
    """Load a built-in primitive or GLB/glTF/OBJ/etc through trimesh."""
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

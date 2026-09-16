from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import hashlib
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    import tomli as tomllib


_ALLOWED_KINDS = {"sprite", "atlas", "gltf", "glb", "material", "shader", "audio", "metadata"}
_ALLOWED_BINDINGS = {
    "none", "left_palm", "right_palm", "chest", "head", "pelvis", "left_foot", "right_foot",
    "room_hit", "screen", "world",
}


@dataclass(frozen=True)
class AssetEntry:
    id: str
    kind: str
    path: str | None = None
    binding: str = "none"
    tags: tuple[str, ...] = ()
    scale: float = 1.0
    fps: float = 0.0
    frames: int = 1
    emissive: float = 1.0
    blend: str = "add"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VFXPack:
    root: Path
    id: str
    name: str
    version: str
    license: str
    author: str = ""
    source: str = ""
    generated_with: str = ""
    assets: tuple[AssetEntry, ...] = ()

    def by_id(self, asset_id: str) -> AssetEntry:
        for asset in self.assets:
            if asset.id == asset_id:
                return asset
        raise KeyError(asset_id)

    def resolve(self, asset: AssetEntry | str) -> Path | None:
        entry = self.by_id(asset) if isinstance(asset, str) else asset
        if not entry.path:
            return None
        p = (self.root / entry.path).resolve()
        root = self.root.resolve()
        if root not in p.parents and p != root:
            raise ValueError(f"asset path escapes pack root: {entry.path}")
        return p


def load_vfx_pack(path: str | Path) -> VFXPack:
    manifest = Path(path)
    if manifest.is_dir():
        manifest = manifest / "manifest.toml"
    data = tomllib.loads(manifest.read_text(encoding="utf-8"))
    pack = data.get("pack", {})
    raw_assets = data.get("asset", [])
    seen: set[str] = set()
    assets: list[AssetEntry] = []
    for raw in raw_assets:
        asset_id = str(raw["id"])
        if asset_id in seen:
            raise ValueError(f"duplicate asset id: {asset_id}")
        seen.add(asset_id)
        kind = str(raw["kind"]).lower()
        if kind not in _ALLOWED_KINDS:
            raise ValueError(f"unsupported asset kind {kind!r} for {asset_id}")
        binding = str(raw.get("binding", "none"))
        if binding not in _ALLOWED_BINDINGS:
            raise ValueError(f"unsupported binding {binding!r} for {asset_id}")
        known = {"id", "kind", "path", "binding", "tags", "scale", "fps", "frames", "emissive", "blend"}
        metadata = {k: v for k, v in raw.items() if k not in known}
        assets.append(
            AssetEntry(
                id=asset_id,
                kind=kind,
                path=raw.get("path"),
                binding=binding,
                tags=tuple(str(x) for x in raw.get("tags", [])),
                scale=float(raw.get("scale", 1.0)),
                fps=float(raw.get("fps", 0.0)),
                frames=int(raw.get("frames", 1)),
                emissive=float(raw.get("emissive", 1.0)),
                blend=str(raw.get("blend", "add")),
                metadata=metadata,
            )
        )
    result = VFXPack(
        root=manifest.parent,
        id=str(pack["id"]),
        name=str(pack.get("name", pack["id"])),
        version=str(pack.get("version", "0.1.0")),
        license=str(pack.get("license", "UNSPECIFIED")),
        author=str(pack.get("author", "")),
        source=str(pack.get("source", "")),
        generated_with=str(pack.get("generated_with", "")),
        assets=tuple(assets),
    )
    validate_vfx_pack(result)
    return result


def validate_vfx_pack(pack: VFXPack, *, require_files: bool = False) -> None:
    if not pack.id or any(c.isspace() for c in pack.id):
        raise ValueError("pack.id must be a non-empty whitespace-free identifier")
    if pack.license == "UNSPECIFIED":
        raise ValueError("asset packs must declare a license")
    for asset in pack.assets:
        resolved = pack.resolve(asset)
        if require_files and resolved is not None and not resolved.exists():
            raise FileNotFoundError(f"missing asset file {asset.id}: {resolved}")
        if asset.frames < 1:
            raise ValueError(f"asset {asset.id} frames must be >= 1")
        if asset.blend not in {"add", "alpha", "screen", "multiply", "opaque"}:
            raise ValueError(f"unsupported blend mode {asset.blend!r}")


def sha256_file(path: str | Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


__all__ = ["AssetEntry", "VFXPack", "load_vfx_pack", "validate_vfx_pack", "sha256_file"]

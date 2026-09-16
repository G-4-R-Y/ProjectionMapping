from pathlib import Path

import pytest

from projection_mapping.asset_pack import load_vfx_pack


def test_loads_vfx_pack_and_preserves_generated_metadata(tmp_path: Path):
    (tmp_path / "fx.png").write_bytes(b"not-an-image-but-present")
    manifest = tmp_path / "manifest.toml"
    manifest.write_text(
        """
[pack]
id = "test_pack"
name = "Test Pack"
version = "1.0.0"
license = "MIT"
generated_with = "genforge"

[[asset]]
id = "spark"
kind = "sprite"
path = "fx.png"
binding = "left_palm"
tags = ["spark", "generated"]
frames = 8
fps = 24
blend = "add"
prompt = "electric cyan spark"
""".strip(),
        encoding="utf-8",
    )
    pack = load_vfx_pack(manifest)
    spark = pack.by_id("spark")
    assert pack.generated_with == "genforge"
    assert spark.frames == 8
    assert spark.metadata["prompt"] == "electric cyan spark"
    assert pack.resolve(spark) == (tmp_path / "fx.png").resolve()


def test_pack_requires_declared_license(tmp_path: Path):
    manifest = tmp_path / "manifest.toml"
    manifest.write_text(
        """
[pack]
id = "bad_pack"

[[asset]]
id = "spark"
kind = "metadata"
""".strip(),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="license"):
        load_vfx_pack(manifest)


def test_pack_rejects_parent_escape(tmp_path: Path):
    manifest = tmp_path / "manifest.toml"
    manifest.write_text(
        """
[pack]
id = "bad_path"
license = "MIT"

[[asset]]
id = "bad"
kind = "sprite"
path = "../escape.png"
""".strip(),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="escapes"):
        load_vfx_pack(manifest)

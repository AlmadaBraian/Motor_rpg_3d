from __future__ import annotations

import json

import pytest

from motor_rpg.runtime.assets import AssetLoadError, load_asset_manifest, validate_asset_reference


def test_asset_manifest_loads_existing_relative_assets(tmp_path):
    texture = tmp_path / "wall.png"
    texture.write_bytes(b"png")
    manifest = tmp_path / "assets.json"
    manifest.write_text(json.dumps({"assets": [{"path": "wall.png", "kind": "texture"}]}), encoding="utf-8")

    loaded = load_asset_manifest(manifest)

    assert len(loaded.assets) == 1
    assert loaded.assets[0].path == texture.resolve()
    assert loaded.assets[0].kind == "texture"


def test_asset_reference_cannot_escape_root(tmp_path):
    outside = tmp_path.parent / "outside.png"
    outside.write_bytes(b"png")

    with pytest.raises(AssetLoadError):
        validate_asset_reference(outside, root=tmp_path)


def test_asset_reference_rejects_unsupported_extension(tmp_path):
    script = tmp_path / "bad.exe"
    script.write_bytes(b"nope")

    with pytest.raises(AssetLoadError):
        validate_asset_reference(script, root=tmp_path)

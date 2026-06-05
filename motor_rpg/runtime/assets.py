from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from motor_rpg.domain.config import AssetPolicy


class AssetLoadError(ValueError):
    """Raised when an asset reference or manifest violates the asset policy."""


@dataclass(frozen=True, slots=True)
class AssetReference:
    path: Path
    kind: str = "generic"


@dataclass(frozen=True, slots=True)
class AssetManifest:
    root: Path
    assets: tuple[AssetReference, ...] = field(default_factory=tuple)

    @classmethod
    def from_json(cls, path: Path | str, policy: AssetPolicy | None = None) -> AssetManifest:
        manifest_path = Path(path)
        with manifest_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return cls.from_dict(data, root=manifest_path.parent, policy=policy)

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        *,
        root: Path | str,
        policy: AssetPolicy | None = None,
    ) -> AssetManifest:
        if not isinstance(data, dict):
            raise AssetLoadError("Asset manifest must be a JSON object")

        entries = data.get("assets", data.get("textures", []))
        if not isinstance(entries, list):
            raise AssetLoadError("Asset manifest requires an 'assets' list")

        root_path = Path(root).resolve()
        refs: list[AssetReference] = []
        for index, entry in enumerate(entries):
            refs.append(_asset_reference_from_entry(entry, index=index, root=root_path, policy=policy))
        return cls(root=root_path, assets=tuple(refs))


def _asset_reference_from_entry(
    entry: Any,
    *,
    index: int,
    root: Path,
    policy: AssetPolicy | None,
) -> AssetReference:
    asset_path: object
    if isinstance(entry, str):
        asset_path = entry
        kind = "generic"
    elif isinstance(entry, dict):
        asset_path = entry.get("path") or entry.get("file") or entry.get("src")
        kind = str(entry.get("kind", entry.get("type", "generic")))
    else:
        raise AssetLoadError(f"Asset entry #{index} must be a path string or object")

    if not isinstance(asset_path, str) or not asset_path.strip():
        raise AssetLoadError(f"Asset entry #{index} has an empty path")

    resolved = validate_asset_reference(root / asset_path, root=root, policy=policy)
    return AssetReference(path=resolved, kind=kind)


def validate_asset_reference(
    path: Path | str,
    *,
    root: Path | str,
    policy: AssetPolicy | None = None,
) -> Path:
    policy = policy or AssetPolicy()
    root_path = Path(root).resolve()
    asset_path = Path(path)
    resolved = asset_path.resolve()

    try:
        resolved.relative_to(root_path)
    except ValueError as exc:
        raise AssetLoadError(f"Asset path escapes project root: {asset_path}") from exc

    if resolved.suffix.lower() not in policy.allowed_extensions:
        raise AssetLoadError(f"Unsupported asset extension: {resolved.suffix}")

    if not resolved.exists():
        raise AssetLoadError(f"Asset file does not exist: {resolved}")

    if resolved.stat().st_size > policy.max_bytes:
        raise AssetLoadError(f"Asset exceeds max size policy: {resolved}")

    return resolved


def load_asset_manifest(path: Path | str, policy: AssetPolicy | None = None) -> AssetManifest:
    return AssetManifest.from_json(path, policy=policy)

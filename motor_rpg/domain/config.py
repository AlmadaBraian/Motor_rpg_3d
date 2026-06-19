from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class GridConfig:
    width: int = 24
    height: int = 24
    cell_pixels: int = 28
    asset_grid: int = 16
    asset_cell: int = 20


@dataclass(frozen=True, slots=True)
class RenderConfig:
    screen_width: int = 640
    screen_height: int = 480
    camera_presets: Mapping[str, Mapping[str, float]] = field(
        default_factory=lambda: MappingProxyType(
            {
                "editor": MappingProxyType(
                    {"x": 12.0, "y": 0.0, "z": 12.0, "yaw": 45.0, "pitch": 55.0, "distance": 35.0}
                ),
                "world": MappingProxyType({"y": 0.8, "yaw": 0.0, "pitch": 35.0, "distance": 7.0}),
                "battle_tactical": MappingProxyType({"y": 0.0, "yaw": 0.0, "pitch": 55.0, "distance": 14.0}),
                "battle_close": MappingProxyType({"y": 1.0, "pitch": 20.0, "distance": 6.0}),
            }
        )
    )


@dataclass(frozen=True, slots=True)
class PathsConfig:
    root: Path
    textures: Path
    decals: Path
    export: Path
    media: Path
    scenes: Path

    @classmethod
    def from_root(cls, root: Path | str) -> PathsConfig:
        root_path = Path(root).resolve()
        return cls(
            root=root_path,
            textures=root_path / "textures",
            decals=root_path / "decals",
            export=root_path / "export_dc",
            media=root_path / "media",
            scenes=root_path / "scenes",
        )


@dataclass(frozen=True, slots=True)
class CombatConfig:
    d20_sides: int = 20
    natural_critical_hit: int = 20
    natural_critical_miss: int = 1
    guard_armor_bonus: int = 4
    guard_damage_multiplier: float = 0.6
    speed_bonus_threshold: int = 4
    speed_attack_multiplier: float = 1.25
    body_type_armor_scale: Mapping[str, float] = field(
        default_factory=lambda: MappingProxyType({"delgado": 0.8, "normal": 1.0, "robusto": 1.2})
    )


@dataclass(frozen=True, slots=True)
class AssetPolicy:
    allowed_extensions: frozenset[str] = frozenset(
        {".bmp", ".c", ".jpg", ".jpeg", ".json", ".kra", ".mp3", ".mtl", ".obj", ".otf", ".png", ".ttf", ".txt", ".wav"}
    )
    asset_roots: tuple[str, ...] = (
        "cd",
        "export_dc",
        "fonts",
        "music",
        "obj",
        "png",
        "scenes",
        "sprites",
        "textures",
    )
    max_bytes: int = 25 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class GameConfig:
    grid: GridConfig = field(default_factory=GridConfig)
    render: RenderConfig = field(default_factory=RenderConfig)
    combat: CombatConfig = field(default_factory=CombatConfig)
    paths: PathsConfig = field(default_factory=lambda: PathsConfig.from_root(Path.cwd()))
    assets: AssetPolicy = field(default_factory=AssetPolicy)

    @classmethod
    def from_root(cls, root: Path | str) -> GameConfig:
        return cls(paths=PathsConfig.from_root(root))


Settings = GameConfig

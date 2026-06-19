from __future__ import annotations

from pathlib import Path

from motor_rpg.domain.config import GameConfig


SETTINGS = GameConfig.from_root(Path(__file__).resolve().parent)

GRID_W = SETTINGS.grid.width
GRID_H = SETTINGS.grid.height
SCREEN_W = SETTINGS.render.screen_width
SCREEN_H = SETTINGS.render.screen_height
CELL_PIXELS = SETTINGS.grid.cell_pixels
ASSET_GRID = SETTINGS.grid.asset_grid
ASSET_CELL = SETTINGS.grid.asset_cell

base_path = str(SETTINGS.paths.root)
tex_path = str(SETTINGS.paths.textures)
decals_tex_path = str(SETTINGS.paths.textures)
TEXTURE_FOLDER = tex_path
DECAL_TEXTURE_FOLDER = decals_tex_path
EXPORT_FOLDER = str(SETTINGS.paths.export)
media_folder = str(SETTINGS.paths.media)
scene_folder = str(SETTINGS.paths.scenes)

CAMERA_PRESETS = {name: dict(values) for name, values in SETTINGS.render.camera_presets.items()}
BODY_TYPE_ARMOR_SCALE = dict(SETTINGS.combat.body_type_armor_scale)

import os


GRID_W = 24
GRID_H = 24
SCREEN_W = 640
SCREEN_H = 480
CELL_PIXELS = 28
ASSET_GRID = 16
ASSET_CELL = 20


base_path = os.path.dirname(__file__)
tex_path = os.path.join(base_path, "textures")
TEXTURE_FOLDER = tex_path
EXPORT_FOLDER = base_path + "/export_dc"

media_folder = base_path + "/media"

scene_folder = base_path + "/scenes"

CAMERA_PRESETS = {
    "editor": {
        "x": 12,
        "y": 0,
        "z": 12,
        "yaw": 45,
        "pitch": 55,
        "distance": 35
    },

    "world": {
        "y": 0.8,
        "yaw": 0,
        "pitch": 35,
        "distance": 7
    },

    "battle_tactical": {
        "y": 0,
        "yaw":0,
        "pitch": 55,
        "distance": 14
    },

    "battle_close": {
        "y": 1,
        "pitch": 20,
        "distance": 6
    }
}

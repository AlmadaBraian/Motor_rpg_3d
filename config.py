import os


GRID_W = 24
GRID_H = 24
CELL_PIXELS = 28
ASSET_GRID = 16
ASSET_CELL = 20


base_path = os.path.dirname(__file__)
tex_path = os.path.join(base_path, "textures")
TEXTURE_FOLDER = tex_path
EXPORT_FOLDER = base_path + "/export_dc"

media_folder = base_path + "/media"

scene_folder = base_path + "/scenes"
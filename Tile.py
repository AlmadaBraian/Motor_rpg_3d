class Tile:
    def __init__(self):
        self.gx = 0
        self.gy = 0

        self.floor_tex = None
        self.wall_tex = None

        self.floor_uv_mode = "tile"
        self.wall_uv_mode = "tile"

        self.floor_height = 0.0

        self.is_block = False

        self.block_bottom = 0.0
        self.block_top = 1.0

        self.block_side_tex = None
        self.block_top_tex = None

        self.block_uv_mode = "tile"

        self.wall_n = False
        self.wall_s = False
        self.wall_e = False
        self.wall_w = False
        self.wall_ne = False
        self.wall_nw = False
        self.wall_se = False
        self.wall_sw = False

        self.wall_n_height = 1.0
        self.wall_s_height = 1.0
        self.wall_e_height = 1.0
        self.wall_w_height = 1.0
        self.wall_ne_height = 1.0
        self.wall_se_height = 1.0
        self.wall_nw_height = 1.0
        self.wall_sw_height = 1.0

        self.wall_n_floor_height = 1.0
        self.wall_s_floor_height = 1.0
        self.wall_e_floor_height = 1.0
        self.wall_w_floor_height = 1.0
        self.wall_ne_floor_height = 1.0
        self.wall_se_floor_height = 1.0
        self.wall_nw_floor_height = 1.0
        self.wall_sw_floor_height = 1.0

        self.wall_segments = {
            "n": [],
            "s": [],
            "e": [],
            "w": [],
            "ne": [],
            "nw": [],
            "se": [],
            "sw": []
        }

        self.event_data = {
            "enabled": False,          # existe evento?
            "trigger": "step",         # step / action / proximity / autorun
            "scene": "",              # scenes/intro.json
            "dialog": "",             # texto rapido opcional
            "script": "",             # script custom
            "teleport": None,         # {"map":"casa.json","x":4,"y":8}
            "combat": False,          # inicia combate?
            "once": False,            # una sola vez
            "done": False,            # ya ejecutado
            "switch_required": "",    # necesita switch ON
            "switch_set": "",         # activa switch al terminar
            "enemy_id": "",           # enemigo a spawnear si combate
            "item_required": "",      # item necesario
            "facing_lock": False      # requiere mirar hacia el tile
        }


        self.objects = []
        self.sprites = []
        self.actors = []
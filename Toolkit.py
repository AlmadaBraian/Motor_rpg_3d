import copy
import tkinter as tk
from tkinter import ttk, simpledialog, filedialog
from tkinter import messagebox
from pyopengltk import OpenGLFrame
from OpenGL.GL import *
from OpenGL.GLU import *
from PIL import Image, ImageTk
import math
import os
import json
import shutil
import glob
from ActorAsset import ActorAsset
from ActorCreatorWindows import open_actor_creator_window
from EventTileEditor import EventTileEditor
from ItemAsset import ItemAsset
from ItemCreatorWindows import open_item_editor
from SkillAsset import SkillAsset
from SkillCreatorWindows import open_skill_editor
from ActorInstance import ActorInstance
from CameraKeyframe import CameraKeyframe
from EventManager import *
from OpglManager import *
from OpglManager import TEXTURE_FOLDER
from RuntimeActor import RuntimeActor
from RuntimeCombat import RuntimeCombat
from RuntimeWorld import RuntimeWorld
from RuntimeSystem import RuntimeSystem
from Tile import Tile
from SpriteAsset import SpriteAsset
from SpriteManager import *
from LowPolyAsset import LowPolyAsset
from SpriteAnimatorEditor import SpriteAnimatorEditor
from WallSegmentEditor import WallSegmentEditor
from config import *


def rotate_3d(px, py, pz, rx, ry, rz):
    rx = math.radians(rx)
    ry = math.radians(ry)
    rz = math.radians(rz)

    # X
    cy = math.cos(rx)
    sy = math.sin(rx)
    py, pz = py*cy - pz*sy, py*sy + pz*cy

    # Y
    cx = math.cos(ry)
    sx = math.sin(ry)
    px, pz = px*cx + pz*sx, -px*sx + pz*cx

    # Z
    cz = math.cos(rz)
    sz = math.sin(rz)
    px, py = px*cz - py*sz, px*sz + py*cz

    return px, py, pz

class Toolkit:
    def __init__(self,root):
        self.root=root
        self.root.title('Dreamcast Toolkit V8.1')
        self.grid=[[Tile() for _ in range(GRID_W)] for _ in range(GRID_H)]
        self.maps = {"Map001": self.grid}
        self.current_map_id = "Map001"
        self.current_map_var = tk.StringVar(value=self.current_map_id)
        self.play_mode = False
        self.assets={}
        self.sprites = {}
        self.sprite_cycle_index = {}
        self.selected_sprite = None
        self.selected_sprite_gx = None
        self.selected_sprite_gy = None
        self.selected_tool='floorpaint'
        self.show_walls=False
        self.show_object_transform=False
        self.selected_asset=None
        self.selected_instance = None
        self.obj_offx = tk.DoubleVar(value=0.0)
        self.obj_offy = tk.DoubleVar(value=0.0)
        self.obj_offz = tk.DoubleVar(value=0.0)
        self.obj_rot_x = tk.IntVar(value=0)
        self.obj_rot_y = tk.IntVar(value=0)
        self.obj_rot_z = tk.IntVar(value=0)
        self.texture_manager=TextureManager()
        self.event_tile_editor=EventTileEditor(toolkit=self)
        self.selected_texture=None
        self.texture_assign_mode=tk.StringVar(value='floor')
        self.texture_thumb_refs=[]
        self.texture_preview_ref=None
        self.current_floor_height = tk.DoubleVar(value=0.0)
        self.current_wall_height = tk.DoubleVar(value=1.0)
        self.prefab_buffer = None
        self.prefab_start = None
        self.prefab_end = None
        self.actors = {}
        self.selected_actor_asset = None
        self.selected_skill_asset = None
        self.selected_actor = None
        self.actor_cycle_index = {}
        self.runtime_world = None
        self.runtime_message = ""
        self.runtime_message_timer = 0.0
        self.runtime_climb_action = None
        self.runtime_camera_locked = False
        self.runtime_camera_catchup = False
        self.current_wall_direction = ""
        self.skills = {}
        self.items = {}
        self.runtime_combat = RuntimeCombat(self)
        self.runtime = RuntimeSystem(self)
        self.screen_fade_alpha = 0.0

        self.screen_fade_active = False

        self.screen_fade_speed = 1.5

        self.screen_fade_direction = 0

        self.screen_fade_callback = None

        self.event_wait_fade = False

        self.game_over = False

        # =====================================
        # DRAG PAINT
        # =====================================

        self.drag_painting = False
        self.drag_start = None
        self.drag_end = None

        # ================================
        # WORLD EVENT ENGINE
        # ================================
        self.world_event_running = False
        self.world_event_locked = False

        self.current_event_data = None
        self.current_event_script = []
        self.current_event_index = 0

        self.event_wait_timer = 0.0
        self.event_wait_input = False
        self.event_wait_move = None

        self.dialog_visible = False
        self.dialog_pages = []
        self.dialog_index = 0
        self.dialog_speaker = ""
        self.space_pressed = False
        self.dialog_visible_chars = 0
        self.dialog_char_timer = 0
        self.dialog_char_speed = 0.02

        self.space_icon_blink = 0.0

        self.world_move_queue = []
        self.world_actor_moving = False
        self.world_moving_unit = None
        self.event_wait_move = False

        self.event_wait_camera = False


        self.button_A_command = "Interactuar"
        self.text_A_button_color = (1, 0.2, 0.2, 1)
        self.button_Y_command = "Items"
        self.text_Y_button_color = (0.2, 1, 0.2, 1)
        self.button_B_command = "Especial"
        self.text_B_button_color = (0.2, 0.2, 1, 1)
        self.button_X_command = ""
        self.text_X_button_color = (0.85, 0.75, 0.25, 1)

        # triggers
        self.tile_events = {}      # (gx,gy) -> json file
        self.actor_events = {}     # actor_name -> json file

        self.runtime_event_cooldown = 0.0
        self.world_event_running = False

        # battle variables
        self.battle_selected_tile = None

        self.show_ui = False

        self.runtime_cam_target_pitch = 35
        self.runtime_cam_target_distance = 7
        self.runtime_cam_target_height = 0.8

        # =========================================
        # TACTICAL RPG
        # =========================================
        self.battle_mode = False
        self.pending_combat_enemy = False
        self.combat_actor_moving = False
        self.battle_input_cooldown = 0
        self.waiting_enemy_turn_start = False

        self.battle_cursor_x = 0
        self.battle_cursor_y = 0

        self.battle_units = []

        self.battle_deploy_tiles = []
        self.battle_deploy_index = 0
        self.battle_deploy_party = []
        self.battle_deploy_finished = False
        self.party = ["A","b","c"]

        self.battle_selected_unit = None
        self.battle_attacker_unit = None
        self.battle_target_unit = None
        self.combat_moving_unit = None

        self.battle_turn_index = 0
        self.battle_current_unit = None
        self.battle_item_index = 0
        self.battle_special_index = 0
        self.current_action_type = ""

        self.battle_state = "idle"

        self.battle_move_tiles = []
        self.battle_target_tiles = []

        self.max_actions = 2

        self.battle_team_turn = "player"

        self.battle_cam_target_x = 0
        self.battle_cam_target_z = 0
        self.battle_cam_active = True
        self.selected_combat_action = ""

        self.enemy_target_tile = None
        self.enemy_ai_state = None

        self.body_type_list = {
        "delgado": 0.75,
        "normal": 1,
        "robusto": 1.25
        }


        self.build_ui()

    def build_ui(self):
        left=tk.Frame(self.root)
        left.pack(side='left',fill='y')
        center=tk.Frame(self.root)
        center.pack(side='left')
        top_map_panel = tk.Frame(center)
        top_map_panel.pack(fill='x', pady=4)

        asset_top_frame = tk.Frame(top_map_panel)
        asset_top_frame.pack(side='left', padx=5, anchor='n')

        prop_frame = tk.Frame(top_map_panel)
        prop_frame.pack(side='left', padx=20, anchor='n')

        prop_frame_2 = tk.Frame(top_map_panel)
        prop_frame_2.pack(side='left', padx=40, anchor='n')

        prop_frame_3 = tk.Frame(top_map_panel)
        prop_frame_3.pack(side='left', padx=60, anchor='n')

        map_frame = tk.LabelFrame(top_map_panel, text="Mapas del Proyecto")
        map_frame.pack(side='left', padx=20, anchor='n')

        tk.Label(map_frame, text="Mapa activo").pack(anchor='w')
        self.map_combo = ttk.Combobox(map_frame, textvariable=self.current_map_var, state='readonly', width=18)
        self.map_combo.pack(fill='x')
        self.map_combo.bind("<<ComboboxSelected>>", self.on_map_combo_selected)

        nav_frame = tk.Frame(map_frame)
        nav_frame.pack(fill='x', pady=(4, 0))
        tk.Button(nav_frame, text="◀", width=3, command=self.previous_map).pack(side='left')
        tk.Button(nav_frame, text="Nuevo", command=self.create_map).pack(side='left', fill='x', expand=True)
        tk.Button(nav_frame, text="▶", width=3, command=self.next_map).pack(side='left')

        tk.Button(map_frame, text="Renombrar mapa", command=self.rename_current_map).pack(fill='x', pady=(4, 0))
        tk.Button(map_frame, text="Duplicar mapa", command=self.duplicate_current_map).pack(fill='x')
        tk.Button(map_frame, text="Eliminar mapa", command=self.delete_current_map).pack(fill='x')
        self.map_status_label = tk.Label(map_frame, text="", anchor='w')
        self.map_status_label.pack(fill='x', pady=(4, 0))
        self.refresh_map_selector()

        tk.Label(left,text='modo mapeo').pack(pady=4)
        self.uv_mode_combo = ttk.Combobox(left, values=["tile","stretch"], state="readonly")
        self.uv_mode_combo.set("tile")
        self.uv_mode_combo.pack(fill='x')

        self.tool_buttons = {}

        self.listaHerramientas(left)

        self.pintarParedes(left)

        self.wall_frame = tk.Frame(left) 
        

        self.tool_status = tk.Label(left, text="TOOL: smartselect", bg="#222", fg="white")
        self.tool_status.pack(fill="x", pady=5)

        tk.Button(left, text="Create/Edit Skill", command=self.open_skill_editor).pack(fill='x')

        tk.Button(left, text="Create/Edit Item", command=self.open_item_editor).pack(fill='x')

        tk.Label(prop_frame, text="Importar").pack(pady=4)
        tk.Button(prop_frame,text='Import OBJ Asset',command=self.import_obj_asset).pack(fill='x')
        tk.Button(prop_frame,text='Import OBJ Mesh',command=self.import_obj_mesh_asset).pack(fill='x')
        tk.Button(prop_frame,text='Import sprite Asset',command=self.import_sprite_sheet_window).pack(fill='x')
        #tk.Button(prop_frame,text='Select Obj',command=lambda:self.set_tool('selectobj')).pack(fill='x')
        #tk.Button(prop_frame,text='Select Sprite',command=lambda:self.set_tool('selectsprite')).pack(fill='x')

        tk.Button(left, text="Sprite Animator", command=self.open_sprite_animator).pack(fill='x')

        #ttk.Button(left,text='Abrir Asset Builder',command=self.open_asset_builder).pack(fill='x')
        ttk.Button(left,text='Guardar Proyecto',command=self.save_project).pack(fill='x')
        ttk.Button(left,text='Cargar Proyecto',command=self.load_project).pack(fill='x')
        ttk.Button(left,text='EXPORT DREAMCAST',command=self.export_dreamcast).pack(fill='x')

        tk.Label(left,text='Preview textura').pack(pady=4)

        self.texture_canvas=tk.Canvas(left,width=128,height=128,bg='black')
        self.texture_canvas.pack()

        self.texture_name_label=tk.Label(left,text='(sin textura)',wraplength=130)
        self.texture_name_label.pack()

        tk.Label(prop_frame, text="Configurar Tiles").pack(pady=4)

        tk.Label(prop_frame,text='Floor Height').pack()
        tk.Spinbox(
            prop_frame,
            from_=-2.0,
            to=5.0,
            increment=0.1,
            textvariable=self.current_floor_height,
            width=8
        ).pack()

        tk.Label(prop_frame,text='Wall Height').pack()
        tk.Spinbox(
            prop_frame,
            from_=0.2,
            to=6.0,
            increment=0.1,
            textvariable=self.current_wall_height,
            width=8
        ).pack()

        tk.Label(prop_frame, text="Configurar Camara").pack(pady=4)

        tk.Button(prop_frame, text="Reset Camera", command=self.reset_camera).pack(fill="x")

        tk.Label(prop_frame, text="Sens Rotacion").pack(pady=2)

        self.cam_rot_speed = tk.DoubleVar(value=0.20)

        tk.Scale(
            prop_frame,
            from_=0.05,
            to=1.0,
            resolution=0.05,
            orient="horizontal",
            variable=self.cam_rot_speed
        ).pack(fill="x")

        self.obj_title_label = tk.Frame(prop_frame_2)

        self.obj_config_frame_1 = tk.Frame(prop_frame_2) 

        self.obj_config_frame_2 = tk.Frame(prop_frame_3) 

        #self.mostrarConfigObj()


        tk.Button(
            prop_frame_3,
            text="RUN GAME",
            command=self.runtime.open_game_runtime
        ).pack(fill='x')

        tk.Label(prop_frame_2, text='Sprite Animation').pack(pady=(0,0))

        self.sprite_anim_combo = ttk.Combobox(prop_frame_2, state='readonly')
        self.sprite_anim_combo.pack(fill='x')
        self.sprite_anim_combo.bind("<<ComboboxSelected>>", self.change_selected_sprite_animation)

        self.texture_browser_wrap=tk.Frame(left)
        self.texture_browser_wrap.pack(pady=5)

        self.texture_scroll_canvas=tk.Canvas(
            self.texture_browser_wrap,
            width=145,
            height=220,
            bg='black',
            highlightthickness=0
        )
        self.texture_scroll_canvas.pack(side='left')

        self.texture_scrollbar=tk.Scrollbar(
            self.texture_browser_wrap,
            orient='vertical',
            command=self.texture_scroll_canvas.yview
        )
        self.texture_scrollbar.pack(side='left', fill='y')

        self.texture_scroll_canvas.configure(yscrollcommand=self.texture_scrollbar.set)

        self.texture_frame=tk.Frame(self.texture_scroll_canvas,bg='black')
        self.texture_scroll_canvas.create_window((0,0),window=self.texture_frame,anchor='nw')

        self.texture_frame.bind(
            '<Configure>',
            lambda e:self.texture_scroll_canvas.configure(
                scrollregion=self.texture_scroll_canvas.bbox('all')
            )
        )

        tk.Label(asset_top_frame,text='Assets').pack()
        self.asset_listbox = tk.Listbox(asset_top_frame,height=10,width=22)
        self.asset_listbox.pack()
        self.asset_listbox.bind('<<ListboxSelect>>',self.select_asset)

        tk.Label(asset_top_frame, text="Actor Library").pack(pady=(10,0))

        self.actor_listbox = tk.Listbox(asset_top_frame, height=6)
        self.actor_listbox.pack(fill='x')
        self.actor_listbox.bind("<<ListboxSelect>>", self.select_actor_asset_from_list)

        tk.Button(asset_top_frame, text="Create/Edit Actor", command=self.open_actor_creator_window).pack(fill='x')
        

        self.grid_canvas=tk.Canvas(center,width=GRID_W*CELL_PIXELS,height=GRID_H*CELL_PIXELS,bg='#202020')
        self.grid_canvas.pack()
        self.grid_canvas.bind("<ButtonPress-1>", self.start_grid_drag)
        self.grid_canvas.bind("<B1-Motion>", self.update_grid_drag)
        self.grid_canvas.bind("<ButtonRelease-1>", self.end_grid_drag)

        self.viewport=GLViewport(self.root,width=900,height=700)
        self.viewport.pack(side='left',fill='both',expand=True)
        self.viewport.toolkit_ref=self
        self.camera = self.viewport.camera

        self.viewport.bind("<ButtonPress-1>", self.start_rotate)
        self.viewport.bind("<B1-Motion>", self.viewport_mouse_drag)
        self.viewport.bind("<ButtonRelease-1>", self.viewport.on_mouse_release)

        self.viewport.bind("<Button-3>", self.start_pan)
        self.viewport.bind("<B3-Motion>", self.pan_camera)

        self.viewport.bind("<MouseWheel>", self.zoom_camera)
        self.viewport.bind("<Motion>", self.hover_3d)
        self.viewport.bind("<Double-Button-1>", self.paint_3d)

        self.root.bind("<KeyPress-Control_L>", self.space_down)
        self.root.bind("<KeyRelease-Control_L>", self.space_up)

        #self.root.bind_all("<KP_0>", self.toggle_camera_view)
        self.root.bind_all("<KeyPress-KP_Insert>", self.toggle_camera_view)
        self.root.bind_all("<KeyPress-0>", self.toggle_camera_view)

        self.root.bind("<Delete>", lambda e: self.delete_selected_instance())
        

        self.build_texture_browser()
        self.draw_grid()
        self.load_sprite_library()

    def open_actor_creator_window (self):
        
        open_actor_creator_window(self, self.selected_actor_asset)

    def open_skill_editor (self):
        
        open_skill_editor(self)

    def open_item_editor (self):
        
        open_item_editor(self)

    def on_event_fade_finished(self):

        print("EVENT FADE FINISHED")

        self.event_wait_fade = False

    def start_fade_out(
        self,
        callback=None,
        speed=1.5
    ):
        
        print("START FADE OUT")

        self.screen_fade_alpha = 0.0

        self.screen_fade_active = True

        self.screen_fade_speed = speed

        self.screen_fade_direction = 1

        self.screen_fade_callback = callback

    def start_fade_in(
        self,
        callback=None,
        speed=1.5
    ):
        
        print("START FADE IN")

        self.screen_fade_alpha = 1.0

        self.screen_fade_active = True

        self.screen_fade_speed = speed

        self.screen_fade_direction = -1

        self.screen_fade_callback = callback

    def update_screen_fade(self, dt):

        if not self.screen_fade_active:
            return

        self.screen_fade_alpha += (
            self.screen_fade_direction
            * self.screen_fade_speed
            * dt
        )

        self.screen_fade_alpha = max(
            0.0,
            min(
                1.0,
                self.screen_fade_alpha
            )
        )

        finished = False

        if (
            self.screen_fade_direction > 0
            and
            self.screen_fade_alpha >= 1.0
        ):
            finished = True

        if (
            self.screen_fade_direction < 0
            and
            self.screen_fade_alpha <= 0.0
        ):
            finished = True

        if finished:

            self.screen_fade_active = False

            callback = self.screen_fade_callback

            self.screen_fade_callback = None

            print("FADE COMPLETE")

            if callback:
                callback()

    def mouse_to_grid(self, event):

        gx = event.x // CELL_PIXELS
        gy = event.y // CELL_PIXELS

        if gx < 0 or gy < 0:
            return None, None

        if gx >= GRID_W or gy >= GRID_H:
            return None, None

        return gx, gy
    
    def start_grid_drag(self, event):

        gx, gy = self.mouse_to_grid(event)

        if gx is None:
            return

        self.drag_painting = True
        self.drag_start = (gx, gy)
        self.drag_end = (gx, gy)

        self.draw_grid()

    def update_grid_drag(self, event):

        if not self.drag_painting:
            return

        gx, gy = self.mouse_to_grid(event)

        if gx is None:
            return

        self.drag_end = (gx, gy)

        self.draw_grid()

    def end_grid_drag(self, event):

        if not self.drag_painting:
            return

        self.drag_painting = False

        gx, gy = self.mouse_to_grid(event)

        if gx is None:
            return

        self.drag_end = (gx, gy)

        x1 = min(self.drag_start[0], self.drag_end[0])
        y1 = min(self.drag_start[1], self.drag_end[1])

        x2 = max(self.drag_start[0], self.drag_end[0])
        y2 = max(self.drag_start[1], self.drag_end[1])

        # =====================================
        # PINTAR REGION
        # =====================================

        for yy in range(y1, y2 + 1):
            for xx in range(x1, x2 + 1):

                self.apply_tool(xx, yy)

        self.drag_start = None
        self.drag_end = None

        self.draw_grid()

    def listaHerramientas(self, place):
        tool_defs = [
            ('Pintar Piso','floorpaint'), ('Pintar tapa columna', 'floor_top_paint'),
            ('Columna', 'blockpaint'), ('Editar Segmento', 'edit_wall_segments'),
            ('Seleccionar mapa','smartselect'),
            ('Colocar Evento', 'place_event_tile')
        ]
        for txt, val in tool_defs:
            b = tk.Button(place, text=txt, command=lambda v=val: self.set_tool(v))
            b.pack(fill='x', pady=1)
            self.tool_buttons[val] = b

    def listaParedes(self, place):
        # Definimos (texto, toolname, fila, columna)
        wall_layout = [
            ('NW', 'wall_nw', 0, 0), ('N', 'wall_n', 0, 1), ('NE', 'wall_ne', 0, 2),
            ('W',  'wall_w',  1, 0),                       ('E',  'wall_e',  1, 2),
            ('SW', 'wall_sw', 2, 0), ('S', 'wall_s', 2, 1), ('SE', 'wall_se', 2, 2)
        ]
        
        for txt, val, r, c in wall_layout:
            # Creamos el botón. Nota: 'image' se puede agregar aquí más adelante.
            b = tk.Button(place, text=txt, width=4, height=2,
                        command=lambda v=val: self.set_tool(v))
            
            # Usamos grid para posicionar. El espacio (1,1) quedará vacío automáticamente.
            b.grid(row=r, column=c, padx=2, pady=2, sticky="nsew")
            
            # Guardamos en el diccionario para que set_tool pueda pintarlo de verde
            self.tool_buttons[val] = b

        # Opcional: Hacer que las columnas tengan el mismo ancho
        for i in range(3):
            place.grid_columnconfigure(i, weight=1)

    def get_uvs_from_idx(self, idx):
        cols = 4  # Tu atlas tiene 4 sub-tiles de ancho
        rows = 6  # Tu atlas tiene 6 sub-tiles de alto
        
        # Calculamos la columna (tx) y la fila (ty) del índice
        tx = idx % cols
        ty = idx // cols

        # Convertimos a coordenadas 0.0 - 1.0
        u0 = tx / float(cols)
        u1 = (tx + 1) / float(cols)

        # En OpenGL, el 0.0 de V suele estar abajo. 
        # Si tu atlas tiene el "Tile 0" arriba a la izquierda, invertimos V:
        v0 = 1.0 - ((ty + 1) / float(rows)) # Borde inferior del sub-tile
        v1 = 1.0 - (ty / float(rows))       # Borde superior del sub-tile

        return u0, u1, v0, v1

    def calculate_autotile_bits(self, L, R, U, D, LU, RU, LD, RD):
        # L=Left, R=Right, U=Up, D=Down (Relativos a la cara de la pared)
        out = [8, 11, 20, 23] # IDs base (centro del tile)

        # NW - Esquina Superior Izquierda
        if U == 1 and L == 1 and LU == 0: out[0] = 2   # Esquina interior
        elif U == 0 and L == 1: out[0] = 10           # Borde lateral
        elif U == 1 and L == 0: out[0] = 16           # Borde superior
        elif U == 1 and L == 1 and LU == 1: out[0] = 18 # Lleno

        # NE - Esquina Superior Derecha
        if U == 1 and R == 1 and RU == 0: out[1] = 3
        elif U == 0 and R == 1: out[1] = 9
        elif U == 1 and R == 0: out[1] = 19
        elif U == 1 and R == 1 and RU == 1: out[1] = 14

        # SW - Esquina Inferior Izquierda
        if D == 1 and L == 1 and LD == 0: out[2] = 6
        elif D == 0 and L == 1: out[2] = 22
        elif D == 1 and L == 0: out[2] = 12
        elif D == 1 and L == 1 and LD == 1: out[2] = 17

        # SE - Esquina Inferior Derecha
        if D == 1 and R == 1 and RD == 0: out[3] = 7  
        elif D == 0 and R == 1: out[3] = 21
        elif D == 1 and R == 0: out[3] = 15
        elif D == 1 and R == 1 and RD == 1: out[3] = 13

        return out



    def get_tile(self, x, y):

        if 0 <= x < GRID_W and 0 <= y < GRID_H:

            return self.grid[y][x]
        
        return None
    
    def check_neighbor_segment(self, nx, ny, side, current_h0, current_h1, tex_name):
        vecino = self.get_tile(nx, ny)
        if not vecino: return 0
        
        segments_vecinos = vecino.wall_segments.get(side, [])
        
        # 1. Si el vecino NO tiene segmentos (pared simple)
        if not segments_vecinos:
            if getattr(vecino, f"wall_{side}", False):
                v_h0 = vecino.floor_height
                v_h1 = v_h0 + getattr(vecino, f"wall_{side}_height", 1.0)
                v_tex = vecino.wall_tex
                
                if v_tex == tex_name:
                    # Verificamos si se solapan las alturas
                    if not (current_h1 <= v_h0 or current_h0 >= v_h1):
                        return 1
            return 0

        # 2. Si el vecino SÍ tiene segmentos, debemos acumular sus alturas
        v_base = vecino.floor_height
        for seg in segments_vecinos:
            v_h0 = v_base
            v_h1 = v_base + seg.get("h", 1.0)
            v_tex = seg.get("tex")
            
            if v_tex == tex_name:
                # Ahora v_h0 y v_h1 son floats reales, no habrá TypeError
                if not (current_h1 <= v_h0 or current_h0 >= v_h1):
                    return 1
            
            v_base = v_h1 # Acumulamos para el siguiente segmento del vecino
            
        return 0
    
    def objConfig_Offsets(self, place):

        tk.Label(place,text='Offset X').pack()
        tk.Scale(
            place,
            from_=-50,
            to=50,
            orient='horizontal',
            variable=self.obj_offx,
            command=lambda v: self.update_selected_instance_transform()
        ).pack(fill='x')
        #tk.Spinbox(prop_frame_2,from_=-1.0,to=1.0,increment=0.1,textvariable=self.obj_offx,width=8,
         #       command=self.update_selected_instance_transform).pack()

        tk.Label(place,text='Offset Y').pack()
        tk.Scale(
            place,
            from_=-50,
            to=50,
            orient='horizontal',
            variable=self.obj_offy,
            command=lambda v: self.update_selected_instance_transform()
        ).pack(fill='x')
        #tk.Spinbox(prop_frame_2,from_=-1.0,to=1.0,increment=0.1,textvariable=self.obj_offy,width=8,
         #       command=self.update_selected_instance_transform).pack()

        tk.Label(place,text='Offset Z').pack()
        tk.Scale(
            place,
            from_=-50,
            to=50,
            orient='horizontal',
            variable=self.obj_offz,
            command=lambda v: self.update_selected_instance_transform()
        ).pack(fill='x')
        #tk.Spinbox(prop_frame_2,from_=-1.0,to=2.0,increment=0.1,textvariable=self.obj_offz,width=8,
         #       command=self.update_selected_instance_transform).pack()

    def objConfig_Rotations(self, place):

        tk.Label(place,text='Rotation X').pack()
        tk.Scale(
            place,
            from_=-360,
            to=360,
            orient='horizontal',
            variable=self.obj_rot_x,
            command=lambda v: self.update_selected_instance_transform()
        ).pack(fill='x')

        tk.Label(place,text='Rotation Y').pack()
        tk.Scale(
            place,
            from_=-360,
            to=360,
            orient='horizontal',
            variable=self.obj_rot_y,
            command=lambda v: self.update_selected_instance_transform()
        ).pack(fill='x')

        tk.Label(place,text='Rotation Z').pack()
        tk.Scale(
            place,
            from_=-360,
            to=360,
            orient='horizontal',
            variable=self.obj_rot_z,
            command=lambda v: self.update_selected_instance_transform()
        ).pack(fill='x')

        tk.Button(place,text='Delete Selected Obj',command=self.delete_selected_instance).pack(fill='x',pady=4)


    def mostrarConfigObj(self):

        if self.show_object_transform:
            self.obj_title_label.pack_forget()
            self.obj_config_frame_1.pack_forget()
            self.obj_config_frame_2.pack_forget()
            self.show_object_transform = False

        else:
            self.show_object_transform = True
            # Limpiamos contenido interno de los frames
            for f in [self.obj_config_frame_1, self.obj_config_frame_2, self.obj_title_label]:
                for w in f.winfo_children():
                    w.destroy()

            titulo = tk.Label(self.obj_title_label, text='Object Transform', font=("Arial", 10, "bold"))
            titulo.pack(fill='x', pady=(10,0))

            self.objConfig_Offsets(self.obj_config_frame_1)
            self.objConfig_Rotations(self.obj_config_frame_2)

            #self.objConfig(self.obj_config_frame_1, self.obj_config_frame_2)
            self.obj_title_label.pack(fill='x')
            
            self.obj_config_frame_1.pack(fill='x', pady=(20,0))
            self.obj_config_frame_2.pack(fill='x', pady=(30,0))

        

    def pintarParedes(self, place):
        self.wall_btn = tk.Button(place, text='Pintar paredes', command=self.showParedes)
        self.wall_btn.pack(fill='x', pady=2)



    def smart_select_at_tile(self, gx, gy, t):

        self.show_object_transform = True

        # ==========================
        # ACTORS
        # ==========================
        if hasattr(t, "actors") and t.actors:
            self.cycle_select_actor_at_tile(gx, gy, t)
            self.selected_tool = "smartselect"

            self.mostrarConfigObj()
            return

        # ==========================
        # SPRITES
        # ==========================
        if hasattr(t, "sprites") and t.sprites:
            self.cycle_select_sprite_at_tile(gx, gy, t)
            self.selected_tool = "smartselect"
            self.mostrarConfigObj()
            return

        # ==========================
        # OBJECTS / MESHES
        # ==========================
        if hasattr(t, "objects") and t.objects:
            self.cycle_select_object_at_tile(gx, gy, t)
            self.selected_tool = "smartselect"
            self.show_object_transform = False
            self.mostrarConfigObj()
            return

        # ==========================
        # NADA -> selección tile
        # ==========================
        self.selected_instance = None
        self.selected_actor_instance = None
        self.selected_sprite_instance = None

        self.selected_gx = gx
        self.selected_gy = gy

        self.mostrarConfigObj()
        print("SMART SELECT: EMPTY TILE", gx, gy)

    def cycle_select_actor_at_tile(self, gx, gy, t):
        if not hasattr(t, "actors"):
            return

        if not t.actors:
            return
        
        self.smart_selected_kind = "actor"

        key = (gx, gy)

        idx = self.actor_cycle_index.get(key, 0)

        if idx >= len(t.actors):
            idx = 0

        pack = t.actors[idx]
        inst = pack["inst"]

        self.selected_instance = pack
        self.load_actor_into_panel(pack, gx, gy)

        idx += 1
        if idx >= len(t.actors):
            idx = 0

        self.actor_cycle_index[key] = idx

        print("SELECTED ACTOR:", inst.actor_name)

    

    def update_battle_unit_facings(self):

        if hasattr(self, "game_view"):
            cam = self.game_view.camera
        else:
            cam = self.viewport.camera

        cam_yaw = cam.yaw

        # =====================================
        # ACTORES DEL MAPA
        # =====================================

        for row in self.runtime_world.grid:

            for t in row:

                for pack in getattr(t, "actors", []):

                    inst = pack["inst"]

                    if not inst.animator:
                        continue

                    self.update_actor_idle_view_by_camera(inst)

        # =====================================
        # BATTLE UNITS
        # =====================================

        if self.battle_mode:

            for pack in self.battle_units:

                inst = pack["inst"]

                if not inst.animator:
                    continue

                self.update_actor_idle_view_by_camera(inst)

    def find_actor_pack_by_name(self, actor_name):

        for row in self.runtime_world.grid:

            for t in row:

                for pack in getattr(t, "actors", []):

                    inst = pack["inst"]

                    if inst.actor_name == actor_name:

                        return pack

        return None

    def find_actor_by_name(self, actor_name):

        for row in self.runtime_world.grid:
            for t in row:
                for pack in getattr(t, "actors", []):

                    actor = pack["inst"]

                    if actor.actor_name == actor_name:
                        return actor

        return None


    def update_runtime_actor(self, dt):

        if self.runtime_event_cooldown > 0:
            self.runtime_event_cooldown -= dt

        if self.runtime_climb_action:
            self.update_runtime_climb(dt)
            return

        if not hasattr(self, "play_mode"):
            return

        if not self.play_mode:
            return

        if not hasattr(self, "runtime_world"):
            return

        if self.runtime_world is None:
            return

        if not self.runtime_world.main_actor:
            return
        
        if self.world_event_running:
            update_world_event(self,dt)
            #print(self.sprites.keys())
            
        if self.battle_input_cooldown > 0:
            self.battle_input_cooldown -= dt

        if self.dialog_visible:

            if hasattr(self, "dialog_continue_actor"):

                self.dialog_continue_actor.animator.update(dt)

                page = self.dialog_pages[self.dialog_index]

                self.dialog_char_timer += dt

                while self.dialog_char_timer >= self.dialog_char_speed:

                    self.dialog_char_timer -= self.dialog_char_speed
                    self.dialog_visible_chars += 1

                    if self.dialog_visible_chars >= len(page):
                        self.dialog_visible_chars = len(page)
                        break

        pack = self.runtime_world.main_actor
        inst = pack["inst"]

        if pack["inst"].is_mantling:
            self.update_actor_mantle(pack, dt)

            if hasattr(self, "game_view"):
                self.game_view.follow_runtime_camera()

            self.viewport.follow_runtime_camera()
            return
        
        if getattr(inst, "is_falling", False):
            self.update_actor_fall(pack, dt)
            return

        move_speed = 1.5 * dt
        rot_speed = 40 * dt

        # =========================================
        # ROTACION DEL ACTOR + CAMARA ORBITAL
        # =========================================
        if inst.rot_l:
            self.runtime_cam_orbit -= rot_speed

        if inst.rot_r:
            self.runtime_cam_orbit += rot_speed

        if inst.rot_l or inst.rot_r:

            self.update_battle_unit_facings()

        # =========================================
        # CAMARA ACTIVA REAL
        # =========================================
        if self.play_mode and hasattr(self, "game_view"):
            active_cam = self.game_view.camera
        else:
            active_cam = self.viewport.camera

        cam_ang = math.radians(active_cam.yaw)

        dx = 0
        dy = 0

        forward_x = math.sin(cam_ang)
        forward_y = math.cos(cam_ang)

        right_x = math.sin(cam_ang + math.pi/2)
        right_y = math.cos(cam_ang + math.pi/2)

        if inst.move_f:
            dx += forward_x * move_speed
            dy += forward_y * move_speed

        if inst.move_b:
            dx -= forward_x * move_speed
            dy -= forward_y * move_speed

        if inst.move_l:
            dx -= right_x * move_speed
            dy -= right_y * move_speed

        if inst.move_r:
            dx += right_x * move_speed
            dy += right_y * move_speed

        # =========================================
        # CHEQUEAR EVENTOS DE TILE
        # =========================================
        moved = self.try_move_runtime_actor(pack, dx, dy)

        # =========================================
        # FOLLOW CAMERA DESPUES DE MOVER
        # =========================================
        if not self.battle_mode:

            if hasattr(self, "game_view"):
                self.game_view.follow_runtime_camera()

            self.viewport.follow_runtime_camera()

        # =========================================
        # ACTUALIZAR ANIM SEGUN CAMARA YA POSICIONADA
        # =========================================
        if getattr(inst, "is_battle_moving", False):
            return
        if inst.animator and not inst.is_mantling:
            if not inst.on_ground:
                pass
            else:
                moving = abs(dx) > 0.001 or abs(dy) > 0.001

                if moving:
                    self.update_actor_walk_by_input(inst, dx, dy)
                else:
                    # Al volver desde combate puede quedar un clip walk activo
                    # aunque ya no exista input de movimiento. Forzamos idle
                    # desde Toolkit, que es quien gobierna la exploracion.
                    self.update_actor_idle_hybrid(inst, dt)

        if self.runtime_message_timer > 0:
            self.runtime_message_timer -= dt
            if self.runtime_message_timer <= 0:
                self.runtime_message = ""

        self.update_runtime_actor_vertical(pack, dt)

        if self.world_event_locked:
            return

    def update_actor_fall(self, pack, dt):
        inst = pack["inst"]
        speed = 2.8
        inst.offz -= speed * dt

        if not inst.animator: return
        
        # 1. MIENTRAS CAE: Congelamos en el aire
        if not inst.fall_land_done:
            inst.animator.play("fall")
            inst.animator.frame = 0
            inst.animator.timer = 0
            inst.animator.paused = True # Evita que el update global sume tiempo

        # 2. MOMENTO DEL IMPACTO: Detectamos suelo
        if inst.offz <= inst.fall_target_z:
            inst.offz = inst.fall_target_z
            inst.ground_z = inst.fall_target_z
            
            if not inst.fall_land_done:
                inst.fall_land_done = True
                inst.animator.paused = False
                inst.animator.timer = 0  # <--- RESETEA AQUÍ TAMBIÉN
                inst.animator.frame = 1

        # 3. ESPERAR A QUE TERMINE LA ANIMACIÓN (Lógica automática)
        if inst.fall_land_done:
            # Dejamos que Animator.update(dt) haga avanzar los frames solo.
            # Solo chequeamos si ya terminó el clip.
            if inst.animator.finished:
                inst.is_falling = False
                inst.on_ground = True
                inst.animator.play("idle")
        
    def mantle_camera_yaw_from_dir(self, dx, dy):
        if abs(dx) > abs(dy):
            if dx > 0:
                return 270   # cubo a la derecha, cam a izquierda
            else:
                return 90
        else:
            if dy > 0:
                return 180   # cubo abajo pantalla / actor va sur
            else:
                return 0
    
    def show_runtime_dialog(self, txt):
        if not hasattr(self, "runtime_dialog_label"):
            return

        self.runtime_dialog_label.config(text=txt)

        if hasattr(self, "_runtime_dialog_after"):
            try:
                self.game_win.after_cancel(self._runtime_dialog_after)
            except:
                pass

        self._runtime_dialog_after = self.game_win.after(
            2500,
            lambda: self.runtime_dialog_label.config(text="")
        )
        

    def update_actor_idle_view_by_camera(self, inst, moving=False):
        if inst.scripted_animation:
            return
        if self.play_mode and hasattr(self, "game_view"):
            cam = self.game_view.camera
        else:
            cam = self.viewport.camera

        cam_ang = cam.yaw % 360
        #actor_ang = getattr(inst, "face_angle", 0) % 360
        actor_ang = inst.face_angle % 360

        rel = (actor_ang - cam_ang) % 360

        # =========================================
        # PREFIJO SEGUN ESTADO
        # =========================================
        prefix = "walk" if moving else "rot"

        # =========================================
        # SUFIJO DIRECCIONAL
        # =========================================
        if rel >= 337 or rel < 22:
            suffix = "_frente"

        elif rel >= 22 and rel < 67:
            suffix = "_frente_dere"

        elif rel >= 67 and rel < 112:
            suffix = "_perfil_dere"

        elif rel >= 112 and rel < 157:
            suffix = "_espalda_dere"

        elif rel >= 157 and rel < 202:
            suffix = "_espalda"

        elif rel >= 202 and rel < 247:
            suffix = "_espalda_izq"

        elif rel >= 247 and rel < 292:
            suffix = "_perfil_izq"

        else:
            suffix = "_frente_izq"

        chosen = prefix + suffix

        # quieto atrás puede usar idle clásico
        if not moving and suffix == "_espalda":
            if "idle" in inst.animator.clips:
                chosen = "idle"

        #print("CHOSEN =", chosen)

        map_vis = {
            "_espalda": "espalda",
            "_espalda_izq": "espalda_izq",
            "_perfil_izq": "perfil_izq",
            "_frente_izq": "frente_izq",
            "_frente": "frente",
            "_frente_dere": "frente_dere",
            "_perfil_dere": "perfil_dere",
            "_espalda_dere": "espalda_dere"
        }

        inst.visual_facing = map_vis.get(suffix, "espalda")

        if inst.animator:

            if chosen in inst.animator.clips:

                if inst.animator.current != chosen:
                    inst.animator.play(chosen)

                return

            # =====================================
            # FALLBACK MIRROR
            # =====================================
            if "_perfil_dere" in chosen and prefix + "_perfil_izq" in inst.animator.clips:
                inst.animator.play(prefix + "_perfil_izq")
                return

            if "_frente_dere" in chosen and prefix + "_frente_izq" in inst.animator.clips:
                inst.animator.play(prefix + "_frente_izq")
                return

            if "_espalda_dere" in chosen and prefix + "_espalda_izq" in inst.animator.clips:
                inst.animator.play(prefix + "_espalda_izq")
                return

            if moving:
                if "walk_espalda" in inst.animator.clips:
                    inst.animator.play("walk_espalda")
                    return
            else:
                if "idle" in inst.animator.clips:
                    inst.animator.play("idle")
                    return
                
                
    def update_actor_walk_by_input(self, inst, dx, dy):

        cam = self.game_view.get_active_camera()

        # =========================================
        # DIRECCION GLOBAL REAL DEL ACTOR
        # =========================================

        world_ang = math.degrees(math.atan2(dx, dy)) % 360

        inst.face_angle = world_ang

        # =========================================
        # RELACION CAMARA VS ACTOR
        # =========================================

        cam_ang = cam.yaw % 360

        rel = (inst.face_angle - cam_ang) % 360

        # =========================================
        # ELEGIR ANIMACION VISUAL
        # =========================================

        if rel >= 337 or rel < 22:
            chosen = "walk_frente"
            face = "frente"
        
        elif rel >= 22 and rel < 67:
            chosen = "walk_frente_dere"
            face = "frente_dere"

        elif rel >= 67 and rel < 112:
            chosen = "walk_perfil_dere"
            face = "perfil_dere"

        elif rel >= 112 and rel < 157:
            chosen = "walk_espalda_dere"
            face = "espalda_dere"

        elif rel >= 157 and rel < 202:
            chosen = "walk_espalda"
            face = "espalda"
            

        elif rel >= 202 and rel < 247:
            chosen = "walk_espalda_izq"
            face = "espalda_izq"

        elif rel >= 247 and rel < 292:
            chosen = "walk_perfil_izq"
            face = "perfil_izq"

        else:
            chosen = "walk_frente_izq"
            face = "frente_izq"

        # =========================================
        # GUARDAR VISUAL
        # =========================================

        inst.facing = face
        inst.visual_facing = face

        inst.inspect_timer = 0.0
        inst.last_cam_yaw = None

        # =========================================
        # PLAY
        # =========================================

        if chosen in inst.animator.clips:

            if inst.animator.current != chosen:
                inst.animator.play(chosen)

        elif "walk_espalda" in inst.animator.clips:

            if inst.animator.current != "walk_espalda":
                inst.animator.play("walk_espalda")
                

    def play_runtime_actor_idle(self, inst):

        if not inst.animator:
            return

        vf = getattr(inst, "visual_facing", "espalda")

        name_map = {
            "espalda": "idle",
            "frente": "idle_frente",
            "izq": "idle_izq",
            "dere": "idle_dere",
            "espalda_izq": "rot_espalda_izq",
            "perfil_izq": "rot_perfil_izq",
            "frente_izq": "rot_frente_izq",
            "frente_dere": "rot_frente_dere",
            "perfil_dere": "rot_perfil_dere",
            "espalda_dere": "rot_espalda_dere"
        }

        candidates = [
            name_map.get(vf, "idle"),
            "idle",
            "idle_espalda",
            "idle_frente"
        ]

        for chosen in candidates:
            if chosen in inst.animator.clips:
                if inst.animator.current != chosen:
                    inst.animator.play(chosen)
                return

    def update_actor_idle_hybrid(self, inst, dt):
        if inst.scripted_animation:
            return
        cam = self.game_view.camera if self.play_mode and hasattr(self, "game_view") else self.viewport.camera

        current_yaw = cam.yaw % 360

        if inst.last_cam_yaw is None:
            inst.last_cam_yaw = current_yaw

        diff = abs((current_yaw - inst.last_cam_yaw + 180) % 360 - 180)

        if diff > 0.05:
            inst.inspect_timer += dt
            inst.last_cam_yaw = current_yaw

            self.update_actor_idle_view_by_camera(inst)
            return

        inst.last_cam_yaw = current_yaw

        # ==========================================
        # QUIETO SIN GIRAR -> conservar ultima pose
        # ==========================================
        self.play_runtime_actor_idle(inst)

    def select_actor_asset_from_list(self, event=None):
        sel = self.actor_listbox.curselection()
        if not sel:
            return

        raw = self.actor_listbox.get(sel[0])
        name = raw.replace(" [MAIN]", "")

        self.selected_actor_asset = name
        self.set_tool("placeactor")
        print("SELECTED ACTOR ASSET =", name)


    def runtime_collides(self, px, py, actor_z, radius=0.18):
        g = self.runtime_world.grid

        gx = int(px)
        gy = int(py)

        if gy < 0 or gy >= len(g) or gx < 0 or gx >= len(g[0]):
            return True

        # Revisamos tiles vecinos porque el radio puede tocar paredes cercanas
        for ty in range(max(0, gy-1), min(len(g), gy+2)):
            for tx in range(max(0, gx-1), min(len(g[0]), gx+2)):

                t = g[ty][tx]

                lx = px - tx   # posicion local dentro del tile (0 a 1)
                ly = py - ty

                # -----------------------------------
                # WALL N  (borde norte y = 0)
                # -----------------------------------
                if t.wall_n:
                    if abs(ly - 0.0) < radius and 0 <= lx <= 1:
                        return True

                # -----------------------------------
                # WALL S (borde sur y = 1)
                # -----------------------------------
                if t.wall_s:
                    if abs(ly - 1.0) < radius and 0 <= lx <= 1:
                        return True

                # -----------------------------------
                # WALL W (borde oeste x = 0)
                # -----------------------------------
                if t.wall_w:
                    if abs(lx - 0.0) < radius and 0 <= ly <= 1:
                        return True

                # -----------------------------------
                # WALL E (borde este x = 1)
                # -----------------------------------
                if t.wall_e:
                    if abs(lx - 1.0) < radius and 0 <= ly <= 1:
                        return True

                # -----------------------------------
                # DIAGONAL NE  (de (0,0) a (1,1))
                # ecuacion: y = x
                # -----------------------------------
                if getattr(t, "wall_ne", False):
                    dist = abs(ly - lx) / 1.4142
                    if dist < radius and 0 <= lx <= 1 and 0 <= ly <= 1:
                        return True

                # -----------------------------------
                # DIAGONAL SW  (misma geometria que NE)
                # -----------------------------------
                if getattr(t, "wall_sw", False):
                    dist = abs(ly - lx) / 1.4142
                    if dist < radius and 0 <= lx <= 1 and 0 <= ly <= 1:
                        return True

                # -----------------------------------
                # DIAGONAL NW  (de (1,0) a (0,1))
                # ecuacion: y = 1-x
                # -----------------------------------
                if getattr(t, "wall_nw", False):
                    dist = abs((lx + ly) - 1.0) / 1.4142
                    if dist < radius and 0 <= lx <= 1 and 0 <= ly <= 1:
                        return True

                # -----------------------------------
                # DIAGONAL SE (misma geometria que NW)
                # -----------------------------------
                if getattr(t, "wall_se", False):
                    dist = abs((lx + ly) - 1.0) / 1.4142
                    if dist < radius and 0 <= lx <= 1 and 0 <= ly <= 1:
                        return True

                # -----------------------------------
                # OBJETOS BLOQUEANTES
                # -----------------------------------
                if t.objects:
                    if 0 <= lx <= 1 and 0 <= ly <= 1:
                        return True
                    
                if getattr(t, "is_block", False):
                    if actor_z < (t.block_top - 0.08):
                        if 0 <= lx <= 1 and 0 <= ly <= 1:
                            return True

        return False

    def try_move_runtime_actor(self, pack, dx, dy):
        inst = pack["inst"]

        old_gx = pack["gx"]
        old_gy = pack["gy"]

        # ---------------------------------------------
        # posicion mundial actual del actor
        # ---------------------------------------------
        world_x = old_gx + 0.5 + inst.offx
        world_y = old_gy + 0.5 + inst.offy

        # nueva posicion deseada
        new_world_x = world_x + dx
        new_world_y = world_y + dy

        # ---------------------------------------------
        # chequeo de colision geometrica REAL
        # ---------------------------------------------
        blocked = self.runtime_collides(new_world_x, new_world_y, inst.offz, radius=0.28)

        if blocked:
            if self.try_start_mantle(pack, dx, dy):
                return False
            return False

        # ---------------------------------------------
        # recalcular tile contenedor segun nueva posicion
        # ---------------------------------------------
        gx = int(new_world_x)
        gy = int(new_world_y)

        if gx < 0 or gy < 0 or gx >= GRID_W or gy >= GRID_H:
            return

        # ---------------------------------------------
        # recalcular offset local relativo al centro tile
        # ---------------------------------------------
        nx = new_world_x - (gx + 0.5)
        ny = new_world_y - (gy + 0.5)

        # ---------------------------------------------
        # si cambió de tile mover pack de celda runtime
        # ---------------------------------------------
        if gx != old_gx or gy != old_gy:

            old_tile = self.runtime_world.grid[old_gy][old_gx]
            new_tile = self.runtime_world.grid[gy][gx]

            if pack in old_tile.actors:
                old_tile.actors.remove(pack)

            if pack not in new_tile.actors:
                new_tile.actors.append(pack)

        # ---------------------------------------------
        # guardar nueva posicion
        # ---------------------------------------------
        pack["gx"] = gx
        pack["gy"] = gy

        #print(pack["gx"], pack["gy"])
        check_runtime_step_events(self)

        inst.offx = nx
        inst.offy = ny

        self.check_runtime_fall(pack)

    def check_runtime_fall(self, pack):
        inst = pack["inst"]

        if inst.is_mantling:
            return

        if getattr(inst, "is_falling", False):
            return

        world_x = pack["gx"] + 0.5 + inst.offx
        world_y = pack["gy"] + 0.5 + inst.offy

        gx = int(world_x)
        gy = int(world_y)

        if gx < 0 or gy < 0 or gx >= GRID_W or gy >= GRID_H:
            return

        t = self.runtime_world.grid[gy][gx]

        floor_z = t.floor_height

        if getattr(t, "is_block", False):
            floor_z = max(floor_z, t.block_top)

        # si el actor esta mas alto que el suelo actual -> cae
        if inst.ground_z > floor_z + 0.05:
            inst.is_falling = True
            inst.fall_target_z = floor_z
            inst.fall_land_done = False

            if inst.animator and "fall" in inst.animator.clips:
                inst.animator.play("fall")
                inst.animator.frame = 0
                

    def update_actor_mantle(self, pack, dt):
        inst = pack["inst"]
        print(inst.animator.current, inst.animator.frame, inst.animator.finished)
        # ==========================================
        # PHASE 0 - GIRAR CAMARA
        # ==========================================
        if inst.mantle_phase == 0:
            diff = (inst.target_cam_yaw - self.runtime_cam_orbit + 540) % 360 - 180
            self.runtime_cam_orbit += diff * min(1, dt * 6)

            

            if abs(diff) < 3:
                self.runtime_cam_orbit = inst.target_cam_yaw
                inst.mantle_timer = 0.0

                if inst.mantle_low:
                    inst.mantle_phase = 3
                else:
                    inst.mantle_phase = 1
            return

        # ==========================================
        # PHASE 1 - JUMP CONTROLADO POR TIMELINE
        # ==========================================
        if inst.mantle_phase == 1:
            speed = 2.8
            inst.mantle_timer += dt # Usa un timer independiente para el movimiento
            if inst.animator.current != "prepare_to_jump":
                inst.animator.play("prepare_to_jump")
            # Dejamos que Animator.update(dt) haga avanzar los frames solo.
            # Solo chequeamos si ya terminó el clip.
            if inst.animator.finished:
                inst.animator.play("jump")
                inst.mantle_phase = 2
                inst.mantle_timer = 0.0
                print("prepare to jump -> jump")

            return

        # ==========================================
        # PHASE 2 - SALTO (SUAVIZADO)
        # ==========================================
        if inst.mantle_phase == 2:
            # 1. Definimos una duración deseada para la subida (ej: 0.5 segundos)
            duration = 0.6 
            inst.mantle_timer += dt
            
            # 2. Calculamos el progreso (t va de 0.0 a 1.0)
            t = min(1.0, inst.mantle_timer / duration)
            
            # 3. Aplicamos una función de suavizado (Ease Out) 
            # Esto hace que empiece rápido y termine lento.
            smooth_t = 1 - (1 - t) * (1 - t) 
            
            # 4. Interpolamos entre la altura inicial y la final
            # (Necesitarás guardar inst.start_z al iniciar la Phase 2)
            if not hasattr(inst, 'mantle_start_z'):
                inst.mantle_start_z = inst.offz

            final_salto = inst.mantle_end_z - 1
            print("inst.offz " + str(inst.offz))
            print("final_salto " + str(final_salto))
            if (inst.offz <= final_salto):
                print("subiendo")
                inst.offz = inst.mantle_start_z + (inst.mantle_end_z - inst.mantle_start_z) * smooth_t
            
            # 5. Transición a la siguiente fase cuando el tiempo se agota
            if t >= 1.0:
                inst.offz = inst.mantle_end_z # Aseguramos posición final
                del inst.mantle_start_z       # Limpiamos variable temporal
                inst.mantle_phase = 3
                inst.mantle_timer = 0.0
            return
        # ==========================================
        # PHASE 3 - SUBIR (CLAW + MOVIMIENTO)
        # ==========================================
        if inst.mantle_phase == 3:

            # iniciar claw UNA sola vez
            if not getattr(inst, "_claw_started", False):

                inst._claw_started = True

                if "claw" in inst.animator.clips:
                    inst.animator.play("claw")

                else:
                    inst.mantle_phase = 5
                    inst.mantle_timer = 0.0
                    return

            inst.mantle_timer += dt

            clip = inst.animator.clips.get("claw")

            fps = getattr(clip, "fps", 6)

            duration = len(clip.frames) / fps

            t = min(1.0, inst.mantle_timer / duration)

            wx = inst.mantle_edge_x + (inst.mantle_end_x - inst.mantle_edge_x) * t
            wy = inst.mantle_edge_y + (inst.mantle_end_y - inst.mantle_edge_y) * t
            wz = inst.mantle_hang_z + (inst.mantle_end_z - inst.mantle_hang_z) * t

            inst.offx = wx - (inst.mantle_base_gx + 0.5)
            inst.offy = wy - (inst.mantle_base_gy + 0.5)
            inst.offz = wz

            if inst.animator.finished:

                del inst._claw_started

                inst.mantle_phase = 5
                inst.mantle_timer = 0.0

            return

        # ==========================================
        # PHASE 5 - SNAP FINAL (SIN DESLIZAMIENTOS)
        # ==========================================
        if inst.mantle_phase == 5:
            # Actualizamos la posición lógica del actor a la celda final
            inst.mantle_base_gx = int(inst.mantle_end_x)
            inst.mantle_base_gy = int(inst.mantle_end_y)
            new_gx = int(inst.mantle_end_x)
            new_gy = int(inst.mantle_end_y)

            self.move_actor_between_tiles(pack, new_gx, new_gy)

            inst.mantle_base_gx = new_gx
            inst.mantle_base_gy = new_gy
            
            # Ponemos los offsets en 0 inmediatamente para evitar el deslizamiento de la Phase 6
            inst.offx = 0
            inst.offy = 0
            inst.offz = inst.mantle_end_z
            
            if "walk_espalda" in inst.animator.clips:
                inst.animator.play("walk_espalda")
                
            inst.mantle_phase = 7 # <--- Saltamos la Phase 6 (la del lerp/deslizamiento)
            return

        if inst.mantle_phase == 7:

            inst.is_mantling = False

            inst.ground_z = inst.mantle_end_z
            inst.on_ground = True
            inst.vspeed = 0

            self.runtime_camera_locked = False
            self.runtime_camera_catchup = True

            if "idle" in inst.animator.clips:
                inst.animator.play("idle")

            self.runtime_cam_target_pitch = 35
            self.runtime_cam_target_distance = 7
            self.runtime_cam_target_height = 0.8

            if hasattr(inst, "combat_mantle_target") and self.battle_mode:

                tx, ty = inst.combat_mantle_target

                oldtile = self.runtime_world.grid[
                    pack["gy"]
                ][
                    pack["gx"]
                ]

                if pack in oldtile.actors:
                    oldtile.actors.remove(pack)

                pack["gx"] = tx
                pack["gy"] = ty

                newtile = self.runtime_world.grid[
                    ty
                ][
                    tx
                ]

                if pack not in newtile.actors:
                    newtile.actors.append(pack)

                inst.offx = 0
                inst.offy = 0

                del inst.combat_mantle_target

            return

    def try_start_mantle(self, pack, dx, dy):
        self.runtime_camera_locked = True
        inst = pack["inst"]

        if inst.is_mantling:
            return False
            

        cur_x = pack["gx"] + 0.5 + inst.offx
        cur_y = pack["gy"] + 0.5 + inst.offy

        l = math.sqrt(dx*dx + dy*dy)
        if l == 0:
            return False

        dir_x = dx / l
        dir_y = dy / l

        front_x = cur_x + dir_x * 0.7
        front_y = cur_y + dir_y * 0.7

        tgx = int(front_x)
        tgy = int(front_y)

        if tgx < 0 or tgy < 0 or tgx >= GRID_W or tgy >= GRID_H:
            return False

        t = self.runtime_world.grid[tgy][tgx]

        if not getattr(t, "is_block", False):
            return False

        climb_h = t.block_top - inst.offz

        if climb_h <= 1.2:
            inst.mantle_low = True
        else:
            inst.mantle_low = False

        inst.is_mantling = True
        inst.mantle_phase = 0
        inst.mantle_timer = 0.0

        inst.mantle_base_gx = pack["gx"]
        inst.mantle_base_gy = pack["gy"]

        inst.mantle_start_x = cur_x
        inst.mantle_start_y = cur_y
        inst.mantle_start_z = inst.offz

        inst.mantle_edge_x = tgx + 0.5 - dir_x * 0.78
        inst.mantle_edge_y = tgy + 0.5 - dir_y * 0.78

        inst.mantle_hang_z = t.block_top - 0.15

        inst.mantle_end_x = tgx + 0.5 - dir_x * 0.3
        inst.mantle_end_y = tgy + 0.5 - dir_y * 0.3
        inst.mantle_end_z = t.block_top

        inst.target_cam_yaw = self.mantle_camera_yaw_from_dir(dir_x, dir_y)

        # cámara cinematic mantle
        self.runtime_cam_target_pitch = 12
        self.runtime_cam_target_distance = 5
        self.runtime_cam_target_height = 0.25

        return True
        

    def refresh_actor_listbox(self):
        self.actor_listbox.delete(0, 'end')

        for name, actor in self.actors.items():
            label = name
            if actor.is_main:
                label += " [MAIN]"
            self.actor_listbox.insert('end', label)

    def invalidate_gl_textures_for_runtime(self):

        # limpiar cache del texture manager
        if hasattr(self, "texture_manager"):
            self.texture_manager.gl_textures = {}

        # sprites
        for spr in self.sprites.values():
            spr.texture = None

        # assets 3d
        for a in self.assets.values():
            if isinstance(a, dict):
                if "gl_tex" in a:
                    a["gl_tex"] = None
                if "texture" in a:
                    a["texture"] = None

        # tiles
        for row in self.grid:
            for t in row:
                if hasattr(t, "floor_gltex"):
                    t.floor_gltex = None
            if hasattr(t, "wall_gltex"):
                t.wall_gltex = None

    def get_active_grid(self):
        if self.play_mode and self.runtime_world:
            return self.runtime_world.grid
        return self.grid


    def runtime_get_ground_height(self, world_x, world_y):
        gx = int(world_x)
        gy = int(world_y)

        if gx < 0 or gy < 0 or gx >= GRID_W or gy >= GRID_H:
            return 0.0

        t = self.runtime_world.grid[gy][gx]

        best = t.floor_height

        # si hay bloque y el actor está sobre la superficie superior
        if getattr(t, "is_block", False):
            if t.block_top > best:
                best = t.block_top

        return best
    
    def update_runtime_actor_vertical(self, pack, dt):
        inst = pack["inst"]

        if inst.is_mantling:
            return

        wx = pack["gx"] + 0.5 + inst.offx
        wy = pack["gy"] + 0.5 + inst.offy

        inst.ground_z = self.runtime_get_ground_height(wx, wy)

        gravity = 7.0

        inst.was_on_ground = inst.on_ground

        if inst.offz > inst.ground_z + 0.02:
            inst.vspeed -= gravity * dt
            inst.offz += inst.vspeed * dt
            inst.on_ground = False

            if not inst.was_on_ground:
                pass
            else:
                if inst.animator and "fall" in inst.animator.clips:
                    inst.animator.play("fall")

            if inst.offz <= inst.ground_z:
                inst.offz = inst.ground_z
                inst.vspeed = 0
                inst.on_ground = True

        else:
            inst.offz = inst.ground_z
            inst.vspeed = 0
            inst.on_ground = True
    

    def reset_camera(self):
        self.viewport.camera.reset()

    def save_sprite_library(self):
        data = {}

        for name, spr in self.sprites.items():
            data[name] = {
                "image_path": spr.image_path,
                "sheet_cols": spr.sheet_cols,
                "sheet_rows": spr.sheet_rows,
                "width": spr.width,
                "height": spr.height,
                "frame_w": spr.frame_w,
                "frame_h": spr.frame_h,
                "clips": []
            }

            for c in spr.base_clips:
                data[name]["clips"].append({
                    "name": c.name,
                    "frames": c.frames,
                    "fps": c.fps,
                    "loop": c.loop
                })

        print("GUARDANDO SPRITE LIBRARY EN:", os.path.abspath("sprite_library.json"))
        with open("sprite_library.json", "w") as f:
            json.dump(data, f, indent=4)

    def get_all_animation_names(self):

        anims = []

        for sprite_name, sprite in self.sprites.items():

            if not hasattr(sprite, "base_clips"):
                continue

            for clip in sprite.base_clips:

                anim_name = clip.name

                if anim_name not in anims:
                    anims.append(anim_name)

        anims.sort()

        return anims

    def load_sprite_library(self):
        if not os.path.exists("sprite_library.json"):
            return

        print("GUARDANDO SPRITE LIBRARY EN:", os.path.abspath("sprite_library.json"))
        with open("sprite_library.json", "r") as f:
            data = json.load(f)

        for name, sd in data.items():
            spr = SpriteAsset(name, None, sd["image_path"])

            #spr = SpriteAsset(name, tex, sd["image_path"])
            spr.sheet_cols = sd["sheet_cols"]
            spr.sheet_rows = sd["sheet_rows"]
            spr.width = sd["width"]
            spr.height = sd["height"]
            spr.frame_w = sd["frame_w"]
            spr.frame_h = sd["frame_h"]

            print("sprite name " + name)

            print("sprite columns and rows " + str(spr.sheet_cols) + " " + str(spr.sheet_rows))

            for cd in sd["clips"]:
                spr.base_clips.append(
                    AnimationClip(
                        cd["name"],
                        cd["frames"],
                        cd["fps"],
                        cd["loop"]
                    )
                )

            self.sprites[name] = spr
            self.asset_listbox.insert(tk.END, name)

    def open_sprite_animator(self):
        sel = self.asset_listbox.curselection()
        if not sel:
            return

        name = self.asset_listbox.get(sel[0])

        if name not in self.sprites:
            return

        SpriteAnimatorEditor(self, self.sprites[name])

    def move_actor_between_tiles(self, pack, new_gx, new_gy):

        old_gx = pack["gx"]
        old_gy = pack["gy"]

        if old_gx == new_gx and old_gy == new_gy:
            return

        old_tile = self.runtime_world.grid[old_gy][old_gx]
        new_tile = self.runtime_world.grid[new_gy][new_gx]

        if pack in old_tile.actors:
            old_tile.actors.remove(pack)

        if pack not in new_tile.actors:
            new_tile.actors.append(pack)

        pack["gx"] = new_gx
        pack["gy"] = new_gy

    def update_animators(self, dt):

        grid = self.get_active_grid()

        updated = set()

        for y in range(GRID_H):
            for x in range(GRID_W):

                t = grid[y][x]

                if hasattr(t, "sprites"):
                    for spr in t.sprites:

                        if spr.animator:
                            spr.animator.update(dt)

                if hasattr(t, "actors"):
                    for pack in t.actors:

                        inst = pack["inst"]

                        if id(inst) in updated:
                            continue

                        updated.add(id(inst))

                        if inst.animator:
                            inst.animator.update(dt)

    def find_texture_file(self, obj_dir, texname):
        target = os.path.basename(texname).strip().lower()

        search_dirs = [
            obj_dir,
            os.path.join(obj_dir, "textures")
        ]

        print("OBJ DIR =", obj_dir)
        print("TARGET TEX =", target)

        for folder in search_dirs:
            print("CHECK FOLDER =", folder)

            if not os.path.exists(folder):
                print("folder missing")
                continue

            print("FILES =", os.listdir(folder))

            for fname in os.listdir(folder):
                if fname.strip().lower() == target:
                    print("FOUND MATCH =", fname)
                    return os.path.join(folder, fname)

        return None
    
    
    def space_down(self, e):
        self.viewport.space_held = True

    def space_up(self, e):
        self.viewport.space_held = False

    def toggle_camera_view(self, event=None):
        target = None

        if self.play_mode and hasattr(self, "game_view"):
            target = self.game_view
        else:
            target = self.viewport

        target.toggle_camera_mode()

    def import_sprite_sheet_window(self):
        path = filedialog.askopenfilename(filetypes=[("PNG Image","*.png")])
        if not path:
            return None

        preview_win = tk.Toplevel()
        preview_win.title("Import Sprite Sheet")
        preview_win.geometry("420x520")

        img = Image.open(path)
        img_thumb = img.copy()
        img_thumb.thumbnail((320,320))

        tkimg = ImageTk.PhotoImage(img_thumb)
        lbl = tk.Label(preview_win, image=tkimg)
        lbl.image = tkimg
        lbl.pack(pady=10)

        tk.Label(preview_win, text="Asset Name").pack()
        name_entry = tk.Entry(preview_win)
        name_entry.insert(0, os.path.basename(path))
        name_entry.pack(fill="x", padx=10)

        cfg = tk.Frame(preview_win)
        cfg.pack(pady=10)

        tk.Label(cfg, text="Cols").grid(row=0,column=0)
        cols_entry = tk.Entry(cfg, width=6)
        cols_entry.insert(0,"8")
        cols_entry.grid(row=0,column=1)

        tk.Label(cfg, text="Rows").grid(row=0,column=2)
        rows_entry = tk.Entry(cfg, width=6)
        rows_entry.insert(0,"7")
        rows_entry.grid(row=0,column=3)

        tk.Label(cfg, text="Frame W").grid(row=1,column=0)
        fw_entry = tk.Entry(cfg, width=6)
        fw_entry.insert(0,"73")
        fw_entry.grid(row=1,column=1)

        tk.Label(cfg, text="Frame H").grid(row=1,column=2)
        fh_entry = tk.Entry(cfg, width=6)
        fh_entry.insert(0,"65")
        fh_entry.grid(row=1,column=3)

        tk.Label(cfg, text="World Width").grid(row=2,column=0)
        ww_entry = tk.Entry(cfg, width=6)
        ww_entry.insert(0,"0.8")
        ww_entry.grid(row=2,column=1)

        tk.Label(cfg, text="World Height").grid(row=2,column=2)
        wh_entry = tk.Entry(cfg, width=6)
        wh_entry.insert(0,"1.6")
        wh_entry.grid(row=2,column=3)

        result = {"sprite_name": None}

        def do_import():
            name = name_entry.get().strip()
            if not name:
                return

            relative_path = os.path.relpath(path, base_path)
            relative_path = "/" + relative_path.replace("\\", "/")

            spr = SpriteAsset(name, None, relative_path)

            try:
                spr.sheet_cols = int(cols_entry.get())
                spr.sheet_rows = int(rows_entry.get())
                spr.frame_w = int(fw_entry.get())
                spr.frame_h = int(fh_entry.get())

                spr.width = float(ww_entry.get())
                spr.height = float(wh_entry.get())
            except:
                pass

            self.sprites[name] = spr
            self.assets[name] = spr

            if name not in self.asset_listbox.get(0, tk.END):
                self.asset_listbox.insert(tk.END, name)

            self.save_sprite_library()

            result["sprite_name"] = name
            preview_win.destroy()

        tk.Button(preview_win, text="IMPORT SPRITE SHEET", command=do_import).pack(pady=20)

        preview_win.grab_set()
        preview_win.wait_window()

        return result["sprite_name"]

    def import_obj_mesh_asset(self):
        path = filedialog.askopenfilename(filetypes=[("OBJ Model","*.obj")])
        if not path:
            return

        obj_dir = os.path.dirname(path)

        verts = []
        texcoords = []
        faces = []
        face_uvs = []
        face_materials = []

        mtl_file = None
        current_material = None

        # ==========================================
        # PARSE OBJ
        # ==========================================
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for raw in f:
                line = raw.strip()

                if not line:
                    continue

                if line.startswith("mtllib"):
                    parts = line.split(maxsplit=1)
                    if len(parts) > 1:
                        mtl_file = parts[1].strip()

                elif line.startswith("usemtl"):
                    parts = line.split(maxsplit=1)
                    if len(parts) > 1:
                        current_material = parts[1].strip()

                elif line.startswith("v "):
                    p = line.split()
                    verts.append((float(p[1]), float(p[2]), float(p[3])))

                elif line.startswith("vt "):
                    p = line.split()
                    texcoords.append((float(p[1]), float(p[2])))

                elif line.startswith("f "):
                    idxs = []
                    uvs = []

                    parts = line.split()[1:]

                    for pp in parts:
                        sub = pp.split('/')

                        vidx = int(sub[0]) - 1
                        idxs.append(vidx)

                        if len(sub) > 1 and sub[1]:
                            tidx = int(sub[1]) - 1
                            uvs.append(tidx)

                    if len(idxs) >= 3:
                        faces.append(idxs)
                        face_uvs.append(uvs)
                        face_materials.append(current_material)

        if not verts or not faces:
            messagebox.showerror("OBJ Mesh", "No mesh data found.")
            return

        # ==========================================
        # PARSE MTL
        # ==========================================
        material_lib = {}

        if mtl_file:
            mtl_path = os.path.join(obj_dir, mtl_file)

            if os.path.exists(mtl_path):
                active_mat = None

                with open(mtl_path, "r", encoding="utf-8", errors="ignore") as mf:
                    for raw in mf:
                        line = raw.strip()

                        if not line:
                            continue

                        if line.startswith("newmtl"):
                            parts = line.split(maxsplit=1)
                            if len(parts) > 1:
                                active_mat = parts[1].strip()

                        elif line.startswith("map_Kd"):
                            parts = line.split(maxsplit=1)
                            if len(parts) > 1 and active_mat:
                                texname = os.path.basename(parts[1].strip())
                                material_lib[active_mat] = texname

        print("MTL materials =", material_lib)

        # ==========================================
        # COPY TEXTURES FOUND
        # ==========================================
        material_textures = {}

        for matname, texname in material_lib.items():
            tex_src = self.find_texture_file(obj_dir, texname)

            print("SEARCHING:", texname, "->", tex_src)

            if tex_src:
                tex_dst = os.path.join(TEXTURE_FOLDER, texname)

                try:
                    shutil.copy(tex_src, tex_dst)
                except:
                    pass

                material_textures[matname] = texname

        print("FACE MATERIAL TEXTURES =", material_textures)

        # ==========================================
        # NORMALIZE VERTICES TO TILE SPACE
        # ==========================================
        minx = min(v[0] for v in verts)
        maxx = max(v[0] for v in verts)
        miny = min(v[1] for v in verts)
        maxy = max(v[1] for v in verts)
        minz = min(v[2] for v in verts)
        maxz = max(v[2] for v in verts)

        sx = maxx - minx or 1
        sy = maxy - miny or 1
        sz = maxz - minz or 1

        nverts = []

        for vx, vy, vz in verts:
            nx = (vx - minx) / sx
            ny = (vy - miny) / sy
            nz = (vz - minz) / sz
            nverts.append((nx, ny, nz))

        # ==========================================
        # CREATE ASSET
        # ==========================================
        name = os.path.splitext(os.path.basename(path))[0]

        asset = LowPolyAsset(name)
        asset.mode = "mesh"
        asset.mesh_vertices = nverts
        asset.mesh_faces = faces
        asset.mesh_texcoords = texcoords
        asset.mesh_face_uvs = face_uvs
        asset.mesh_face_materials = face_materials
        asset.mesh_material_textures = material_textures
        asset.mesh_tex = None

        self.assets[name] = asset
        self.asset_listbox.insert(tk.END, name)

        messagebox.showinfo("OBJ Mesh", f"Imported textured mesh '{name}'")

    def copy_prefab_region(self):
        if not self.prefab_start or not self.prefab_end:
            return

        x1 = min(self.prefab_start[0], self.prefab_end[0])
        y1 = min(self.prefab_start[1], self.prefab_end[1])
        x2 = max(self.prefab_start[0], self.prefab_end[0])
        y2 = max(self.prefab_start[1], self.prefab_end[1])

        buf = []

        for y in range(y1, y2+1):
            row = []
            for x in range(x1, x2+1):
                row.append(copy.deepcopy(self.grid[y][x]))
            buf.append(row)

        self.prefab_buffer = buf
        messagebox.showinfo("Prefab", "Region copied.")

    def paste_prefab_region(self, gx, gy):
        if not self.prefab_buffer:
            return

        for y,row in enumerate(self.prefab_buffer):
            for x,tile in enumerate(row):
                tx = gx + x
                ty = gy + y

                if 0 <= tx < GRID_W and 0 <= ty < GRID_H:
                    self.grid[ty][tx] = copy.deepcopy(tile)

        self.draw_grid()


    def parse_obj_vertices_faces(self, filepath):
        verts = []
        faces = []

        with open(filepath, 'r') as f:
            for line in f:
                if line.startswith('v '):
                    parts = line.strip().split()
                    verts.append((
                        float(parts[1]),
                        float(parts[2]),
                        float(parts[3])
                    ))

                elif line.startswith('f '):
                    parts = line.strip().split()[1:]
                    idxs = []

                    for p in parts:
                        idx = p.split('/')[0]
                        idxs.append(int(idx)-1)

                    if len(idxs) >= 3:
                        faces.append(idxs)

        return verts, faces
    
    def voxelize_obj(self, verts, faces, resolution=6):
        if not verts:
            return []

        minx = min(v[0] for v in verts)
        maxx = max(v[0] for v in verts)

        miny = min(v[1] for v in verts)
        maxy = max(v[1] for v in verts)

        minz = min(v[2] for v in verts)
        maxz = max(v[2] for v in verts)

        sx = maxx - minx
        sy = maxy - miny
        sz = maxz - minz

        sx = sx if sx != 0 else 1
        sy = sy if sy != 0 else 1
        sz = sz if sz != 0 else 1

        cubes = set()

        for vx,vy,vz in verts:
            gx = int(((vx - minx) / sx) * resolution)
            gy = int(((vz - minz) / sz) * resolution)
            gz = int(((vy - miny) / sy) * resolution)

            cubes.add((gx,gy,gz))

        return list(cubes)
    
    def showParedes(self):
        if self.show_walls:
            # Si ya está abierto, lo cerramos
            self.wall_frame.pack_forget()
            self.show_walls = False
            self.set_tool('smartselect') # O la herramienta por defecto que desees
        else:
            # Al abrir, marcamos que vamos a usar paredes
            self.show_walls = True
            for widget in self.wall_frame.winfo_children():
                widget.destroy()
                
            self.listaParedes(self.wall_frame)
            self.wall_frame.pack(fill='x', after=self.wall_btn) # Aparece debajo del status o donde prefieras
            
            # Deseleccionamos cualquier herramienta previa para que el foco sea "Paredes"
            self.set_tool("wall_n") # Selecciona la primera pared por defecto o mantén el estado
    
    def import_obj_asset(self):
        path = filedialog.askopenfilename(filetypes=[("OBJ Model","*.obj")])
        if not path:
            return

        verts, faces = self.parse_obj_vertices_faces(path)

        cubes = self.voxelize_obj(verts, faces, resolution=6)

        if not cubes:
            messagebox.showerror("OBJ Import","No geometry found.")
            return

        name = os.path.splitext(os.path.basename(path))[0]

        asset = LowPolyAsset(name)
        asset.cubes = cubes

        # texturas default actuales seleccionadas
        asset.tex_top = self.selected_texture
        asset.tex_side = self.selected_texture

        self.assets[name] = asset

        self.asset_listbox.insert(tk.END, name)

        messagebox.showinfo("OBJ Import", f"Imported asset '{name}' with {len(cubes)} voxels.")

    def update_selected_instance_transform(self):
        if not self.selected_instance:
            return

        inst = self.selected_instance["inst"]

        inst["rot_x"] = float(self.obj_rot_x.get())
        inst["rot_y"] = float(self.obj_rot_y.get())
        inst["rot_z"] = float(self.obj_rot_z.get())
        inst["offx"] = float(self.obj_offx.get())
        inst["offy"] = float(self.obj_offy.get())
        inst["offz"] = float(self.obj_offz.get())

        self.draw_grid()

    def cycle_select_object_at_tile(self, gx, gy, tile):
        if not tile.objects:
            return
        
        self.smart_selected_kind = "object"

        if not self.selected_instance or self.selected_instance["inst"] not in tile.objects:
            self.load_instance_into_panel({
                "inst": tile.objects[0],
                "gx": gx,
                "gy": gy
            })
            return

        idx = tile.objects.index(self.selected_instance["inst"])
        idx = (idx + 1) % len(tile.objects)

        self.load_instance_into_panel({
            "inst": tile.objects[idx],
            "gx": gx,
            "gy": gy
        })

    def change_selected_sprite_animation(self, event=None):
        if not self.selected_sprite:
            return

        clip = self.sprite_anim_combo.get()

        if self.selected_sprite.animator:
            self.selected_sprite.animator.play(clip)

    def load_sprite_into_panel(self, inst, gx, gy):
        self.selected_sprite = inst
        self.selected_sprite_gx = gx
        self.selected_sprite_gy = gy

        self.obj_offx.set(inst.offx * 100)
        self.obj_offy.set(inst.offy * 100)
        self.obj_offz.set(inst.offz * 100)

        asset = self.sprites[inst.asset]

        names = [c.name for c in asset.base_clips]
        self.sprite_anim_combo["values"] = names

        if inst.animator and inst.animator.current in names:
            self.sprite_anim_combo.set(inst.animator.current)
        elif names:
            self.sprite_anim_combo.set(names[0])
            if inst.animator:
                inst.animator.play(names[0])
        else:
            self.sprite_anim_combo.set("")

    def load_instance_into_panel(self, picked):
        print("SELECTED OBJECT =", picked)
        if not picked:
            return

        self.selected_instance = picked

        inst = picked["inst"]

        self.obj_offx.set(inst["offx"])
        self.obj_offy.set(inst["offy"])
        self.obj_offz.set(inst["offz"])
        self.obj_rot_x.set(inst["rot_x"])
        self.obj_rot_y.set(inst["rot_y"])
        self.obj_rot_z.set(inst["rot_z"])

        asset = self.assets.get(inst["asset"])
        #self.mostrarConfigObj()

    def delete_selected_instance(self):
        self.open_delete_popup()

    def refresh_asset_list(self):
        self.asset_list.delete(0,'end')
        for k in self.assets.keys():
            self.asset_list.insert('end',k)
    
    def draw_texture_preview(self, texture_name):
        path=os.path.join(TEXTURE_FOLDER, texture_name)
        if not os.path.exists(path):
            return

        img=Image.open(path).convert("RGBA")
        img=img.resize((128,128), Image.NEAREST)

        tk_img=ImageTk.PhotoImage(img)
        self.texture_preview_ref=tk_img

        self.texture_canvas.delete("all")
        self.texture_canvas.create_image(64,64,image=tk_img)
        self.texture_name_label.config(text=texture_name)

    def update_texture_selection(self):
        texture_names=list(self.texture_manager.previews.keys())

        for i,widget in enumerate(self.texture_frame.winfo_children()):
            tex_name=texture_names[i]

            if tex_name==self.selected_texture:
                widget.config(relief="solid",bd=3,bg="yellow")
            else:
                widget.config(relief="flat",bd=2,bg="black")

    def build_texture_browser(self):
        for widget in self.texture_frame.winfo_children():
            widget.destroy()

        self.texture_thumb_refs=[]

        cols=2
        size=64

        texture_names=list(self.texture_manager.previews.keys())

        for i,tex_name in enumerate(texture_names):
            path=os.path.join(TEXTURE_FOLDER, tex_name)
            if not os.path.exists(path):
                continue

            img=Image.open(path).convert("RGBA")
            img=img.resize((size,size), Image.NEAREST)

            tk_img=ImageTk.PhotoImage(img)
            self.texture_thumb_refs.append(tk_img)

            btn=tk.Label(self.texture_frame,image=tk_img,bd=2,relief="flat",bg="black")
            btn.grid(row=i//cols,column=i%cols,padx=2,pady=2)

            def on_click(e,tex_name=tex_name):
                self.selected_texture=tex_name
                self.update_texture_selection()
                self.draw_texture_preview(tex_name)

            btn.bind("<Button-1>", on_click)

        if texture_names and not self.selected_texture:
            self.selected_texture=texture_names[0]
            self.draw_texture_preview(texture_names[0])

        self.update_texture_selection()

    def select_asset(self,e):
        s=self.asset_listbox.curselection()
        if s:
            self.selected_asset=self.asset_listbox.get(s[0])

            if self.selected_asset in self.sprites:
                self.set_tool("placesprite")
            else:
                self.set_tool("placeobj")

    def select_sprite(self,e):
        s=self.asset_listbox.curselection()
        if s:
            self.selected_asset=self.asset_listbox.get(s[0])
            self.set_tool("placesprite")

    def hover_3d(self,e):
        if self.play_mode:
            return
        self.viewport.hover_tile=self.viewport.get_exact_tile(e.x,e.y)

    def paint_3d(self,e):
        if self.play_mode:
            return
        pos=self.viewport.get_exact_tile(e.x,e.y)
        if pos:
            self.apply_tool(*pos)

    def start_rotate(self, e):
        if self.play_mode:
            return
        self.viewport.last_x = e.x
        self.viewport.last_y = e.y

    def viewport_mouse_press(self, event):
        self.viewport.last_mouse_x = event.x
        self.viewport.last_mouse_y = event.y

        picked = self.viewport.pick_object_under_mouse(event.x, event.y)

        if picked:
            self.load_instance_into_panel(picked)

        if self.viewport.is_click_near_gizmo(event.x, event.y):
            self.viewport.dragging_gizmo = True

            if event.state & 0x0001:
                self.viewport.drag_mode = "z"
            else:
                self.viewport.drag_mode = "xy"
        else:
            self.viewport.dragging_gizmo = False
            self.start_rotate(event)

    def viewport_mouse_release(self, event):
        self.viewport.dragging_gizmo = False
        self.viewport.drag_mode = None

    def viewport_mouse_drag(self, event):
        if self.play_mode:
            return
        if self.viewport.space_held:
            self.rotate_camera(event)

    def rotate_camera(self, e):
        if self.play_mode:
            return
        dx = e.x - self.viewport.last_x
        dy = e.y - self.viewport.last_y

        sens = self.cam_rot_speed.get()

        self.viewport.camera.yaw += dx * sens
        self.viewport.camera.pitch -= dy * sens

        self.viewport.camera.pitch = max(-89, min(89, self.viewport.camera.pitch))

        self.viewport.last_x = e.x
        self.viewport.last_y = e.y

    def start_pan(self, e):
        if self.play_mode:
            return
        self.viewport.last_x = e.x
        self.viewport.last_y = e.y

    def is_click_near_gizmo(self, mx, my):
        if not hasattr(self, 'toolkit_ref'):
            return False

        tool = self.toolkit_ref

        if not tool.selected_instance:
            return False

        sel = tool.selected_instance

        if "gx" not in sel or "gy" not in sel:
            return False

        inst = sel["inst"]

        gx = sel["gx"] + inst["offx"] + 0.5
        gz = sel["gy"] + inst["offy"] + 0.5

        screen_x = (gx - gz) * 32 + (self.winfo_width() // 2)
        screen_y = (gx + gz) * 16 + 120

        dx = mx - screen_x
        dy = my - screen_y

        return abs(dx) < 170 and abs(dy) < 170

    def on_mouse_press(self, event):
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        self.manipulating_object = False
        self.dragging_gizmo = False

        picked = self.viewport.pick_object_under_mouse(event.x, event.y)

        if picked:
            # SIEMPRE seleccionar primero
            self.load_instance_into_panel(picked)

            return

    def pan_camera(self, e):
        if self.play_mode:
            return
        dx = e.x - self.viewport.last_x
        dy = e.y - self.viewport.last_y

        speed = 0.03
        yaw = math.radians(self.viewport.camera.yaw)

        right_x = math.cos(yaw)
        right_z = math.sin(yaw)

        forward_x = -math.sin(yaw)
        forward_z = math.cos(yaw)

        self.viewport.camera.x -= right_x * dx * speed
        self.viewport.camera.z -= right_z * dx * speed

        self.viewport.camera.x += forward_x * dy * speed
        self.viewport.camera.z += forward_z * dy * speed

        self.viewport.last_x = e.x
        self.viewport.last_y = e.y

    def zoom_camera(self, e):
        if self.play_mode:
            return
        self.viewport.camera.distance -= (1 if e.delta > 0 else -1)
        self.viewport.camera.distance = max(5, min(100, self.viewport.camera.distance))

    def set_tool(self, toolname):
        self.selected_tool = toolname
        
        # 1. Actualizar texto de estado
        if hasattr(self, "tool_status"):
            self.tool_status.config(text=f"TOOL: {toolname}")

        # 2. Lógica de cierre automático:
        # Si eliges una herramienta que NO empieza con "wall_", cerramos el menú de paredes
        if not toolname.startswith("wall_") and self.show_walls:
            self.wall_frame.pack_forget()
            self.show_walls = False

        # 3. Pintar botones del diccionario
        if hasattr(self, "tool_buttons"):
            for name, btn in self.tool_buttons.items():
                if name == toolname:
                    btn.config(bg="#00aa44", fg="white")
                else:
                    btn.config(bg="#d9d9d9", fg="black")

        # 4. Pintar el botón principal "Pintar paredes"
        # Se pone verde si la herramienta actual es cualquier tipo de pared
        if hasattr(self, "wall_btn"):
            if toolname.startswith("wall_"):
                self.wall_btn.config(bg="#00aa44", fg="white")
                if toolname == "wall_n":
                    self.current_wall_direction = "n"

                elif toolname == "wall_ne":
                        self.current_wall_direction = "ne"

                elif toolname == "wall_nw":
                        self.current_wall_direction = "nw"

                elif toolname == "wall_se":
                        self.current_wall_direction = "se"
                    
                elif toolname == "wall_sw":
                        self.current_wall_direction = "sw"

                elif toolname == "wall_e":
                        self.current_wall_direction = "e"

                elif toolname == "wall_w":
                        self.current_wall_direction = "w"

                elif toolname == "wall_s":
                        self.current_wall_direction = "s"
            else:
                self.wall_btn.config(bg="#d9d9d9", fg="black")
                    
    def auto_return_to_select(self):
        self.set_tool("smartselect")
        self.draw_grid()

    def reload_clips(self, clips):
        current_name = self.current
        self.clips = {c.name: c for c in clips}

        if current_name in self.clips:
            self.current = current_name
        else:
            self.current = None
            self.frame = 0
            self.timer = 0

    def load_actor_into_panel(self, pack, gx, gy):
        inst = pack["inst"]

        self.selected_actor_gx = gx
        self.selected_actor_gy = gy

        if inst.actor_name not in self.actors:
            return

        actor_def = self.actors[inst.actor_name]

        if not getattr(actor_def, "sprite_sheets", []):
            self.sprite_anim_combo["values"] = []
            self.sprite_anim_combo.set("")
            return

        sprname = actor_def.sprite_sheets[0]

        if sprname not in self.sprites:
            self.sprite_anim_combo["values"] = []
            self.sprite_anim_combo.set("")
            return

        sprite_asset = self.sprites[sprname]

        names = [c.name for c in sprite_asset.base_clips]
        self.sprite_anim_combo["values"] = names

        if inst.animator and inst.animator.current:
            self.sprite_anim_combo.set(inst.animator.current)
        elif names:
            self.sprite_anim_combo.set(names[0])
        else:
            self.sprite_anim_combo.set("")

    def apply_tool(self,gx,gy):
        t = self.grid[gy][gx]

        self.last_clicked_gx = gx
        self.last_clicked_gy = gy

        if self.selected_tool == 'floorpaint':
            self.texture_assign_mode.set('floor')
            t.floor_tex = self.selected_texture
            t.floor_height = float(self.current_floor_height.get())
            t.floor_uv_mode = self.uv_mode_combo.get()

        elif self.selected_tool == 'floor_top_paint':
            #self.texture_assign_mode.set('floor')
            t.block_top_tex = self.selected_texture
            #t.top_height = float(self.current_floor_height.get())
            t.top_uv_mode = self.uv_mode_combo.get()

        elif self.selected_tool == 'blockpaint':
            self.build_solid_block(gx, gy)

        elif self.selected_tool == 'wall_n':
            t.wall_n = not t.wall_n
            self.texture_assign_mode.set('wall')
            t.wall_tex = self.selected_texture
            t.wall_n_height = float(self.current_wall_height.get())
            t.wall_n_floor_height = float(self.current_floor_height.get())
            t.wall_uv_mode = self.uv_mode_combo.get()
            self.current_wall_direction = "n"

        elif self.selected_tool == 'wall_s':
            t.wall_s = not t.wall_s
            self.texture_assign_mode.set('wall')
            t.wall_tex = self.selected_texture
            t.wall_s_height = float(self.current_wall_height.get())
            t.wall_s_floor_height = float(self.current_floor_height.get())
            t.wall_uv_mode = self.uv_mode_combo.get()
            self.current_wall_direction = "s"

        elif self.selected_tool == 'wall_e':
            t.wall_e = not t.wall_e
            self.texture_assign_mode.set('wall')
            t.wall_tex = self.selected_texture
            t.wall_e_height = float(self.current_wall_height.get())
            t.wall_e_floor_height = float(self.current_floor_height.get())
            t.wall_uv_mode = self.uv_mode_combo.get()
            self.current_wall_direction = "e"

        elif self.selected_tool == 'wall_w':
            t.wall_w = not t.wall_w
            self.texture_assign_mode.set('wall')
            t.wall_tex = self.selected_texture
            t.wall_w_height = float(self.current_wall_height.get())
            t.wall_w_floor_height = float(self.current_floor_height.get())
            t.wall_uv_mode = self.uv_mode_combo.get()
            self.current_wall_direction = "w"
        
        elif self.selected_tool == 'wall_ne':
            t.wall_ne = not t.wall_ne
            self.texture_assign_mode.set('wall')
            t.wall_tex = self.selected_texture
            t.wall_ne_height = float(self.current_wall_height.get())
            t.wall_ne_floor_height = float(self.current_floor_height.get())
            t.wall_uv_mode = self.uv_mode_combo.get()
            self.current_wall_direction = "ne"

        elif self.selected_tool == 'wall_se':
            t.wall_se = not t.wall_se
            self.texture_assign_mode.set('wall')
            t.wall_tex = self.selected_texture
            t.wall_se_height = float(self.current_wall_height.get())
            t.wall_se_floor_height = float(self.current_floor_height.get())
            t.wall_uv_mode = self.uv_mode_combo.get()
            self.current_wall_direction = "se"

        elif self.selected_tool == 'wall_nw':
            t.wall_nw = not t.wall_nw
            self.texture_assign_mode.set('wall')
            t.wall_tex = self.selected_texture
            t.wall_nw_height = float(self.current_wall_height.get())
            t.wall_nw_floor_height = float(self.current_floor_height.get())
            t.wall_uv_mode = self.uv_mode_combo.get()
            self.current_wall_direction = "nw"

        elif self.selected_tool == 'wall_sw':
            t.wall_sw = not t.wall_sw
            self.texture_assign_mode.set('wall')
            t.wall_tex = self.selected_texture
            t.wall_sw_height = float(self.current_wall_height.get())
            t.wall_sw_floor_height = float(self.current_floor_height.get())
            t.wall_uv_mode = self.uv_mode_combo.get()
            self.current_wall_direction = "sw"

        elif self.selected_tool == 'edit_wall_segments' and self.current_wall_direction != "":
            # Creamos una lista con los estados de las paredes
            walls = [t.wall_n, t.wall_s, t.wall_e, t.wall_w, t.wall_ne, t.wall_nw, t.wall_se, t.wall_sw]
            
            # any() devuelve True si al menos un elemento de la lista es True
            if any(walls):
                self.open_wall_editor(gx, gy, self.current_wall_direction)

        elif self.selected_tool == 'placeobj' and self.selected_asset:
            inst = {
                "asset": self.selected_asset,
                "offx": 0.0,
                "offy": 0.0,
                "offz": 0.0,
                "rot_x": 0,
                "rot_y": 0,
                "rot_z": 0
            }
            t.objects.append(inst)

            self.load_instance_into_panel({
                "inst": inst,
                "gx": gx,
                "gy": gy
            })

            self.set_tool("smartselect")
            self.auto_return_to_select()

        elif self.selected_tool == 'placesprite' and self.selected_asset:
            if self.selected_asset not in self.sprites:
                return

            inst = SpriteInstance(self.selected_asset)

            asset = self.sprites[self.selected_asset]

            inst.animator = Animator(asset.base_clips)

            if asset.base_clips:
                inst.animator.play(asset.base_clips[0].name)

            t.sprites.append(inst)

            self.load_sprite_into_panel(inst, gx, gy)
            self.set_tool("smartselect")
            self.auto_return_to_select()

        elif self.selected_tool == 'smartselect':
            self.smart_select_at_tile(gx, gy, t)

        elif self.selected_tool == 'selectobj':
            self.cycle_select_object_at_tile(gx, gy, t)

        elif self.selected_tool == 'selectsprite':
            self.cycle_select_sprite_at_tile(gx, gy, t)

        elif self.selected_tool == 'placeactor' and self.selected_actor_asset:

            if self.selected_actor_asset not in self.actors:
                return

            actor_def = self.actors[self.selected_actor_asset]

            inst = ActorInstance(self.selected_actor_asset)

            # ==========================================
            # SPRITE SHEET PRINCIPAL SI EXISTE
            # ==========================================
            if getattr(actor_def, "sprite_sheets", []):

                sprname = actor_def.sprite_sheets[0]

                if sprname in self.sprites:
                    sprite_asset = self.sprites[sprname]

                    inst.animator = Animator(self.clone_clips(sprite_asset.base_clips))

                    if sprite_asset.base_clips:
                        inst.animator.play(sprite_asset.base_clips[0].name)

            pack = {
                "inst": inst,
                "gx": gx,
                "gy": gy
            }

            t.actors.append(pack)

            self.load_actor_into_panel(pack, gx, gy)
            self.draw_grid()
            self.set_tool("smartselect")
            self.auto_return_to_select()

        elif self.selected_tool == 'selectactor':
            self.cycle_select_actor_at_tile(gx, gy, t)

        elif self.selected_tool == 'prefab_start':
            self.prefab_start = (gx, gy)

        elif self.selected_tool == 'prefab_end':
            self.prefab_end = (gx, gy)
            self.copy_prefab_region()

        elif self.selected_tool == 'prefab_paste':
            self.paste_prefab_region(gx, gy)

        elif self.selected_tool == "place_event_tile":
            self.event_tile_editor.open(gx, gy, t)
            self.auto_return_to_select()

        self.draw_grid()

    def build_solid_block(self, gx, gy):
        t = self.grid[gy][gx]

        h = float(self.current_wall_height.get())

        t.is_block = True
        t.block_bottom = t.floor_height
        t.block_top = t.floor_height + h

        t.block_side_tex = self.selected_texture
        t.block_top_tex = self.selected_texture
        t.block_uv_mode = self.uv_mode_combo.get()

        print("BUILD BLOCK", gx, gy)

    def get_tile_connection_height(self, tile, dx, dy):

        # bloque sólido
        if getattr(tile, "is_block", True):
            return tile.block_top

        # pared relevante según dirección
        if dy == -1 and getattr(tile, "wall_n", True):
            return tile.wall_n_height

        if dy == 1 and getattr(tile, "wall_s", True):
            return tile.wall_s_height

        if dx == -1 and getattr(tile, "wall_w", True):
            return tile.wall_w_height

        if dx == 1 and getattr(tile, "wall_e", True):
            return tile.wall_e_height

        # piso normal
        return tile.floor_height

    def same_autotile_group(self, x1, y1, x2, y2):

        if x2 < 0 or y2 < 0 or x2 >= GRID_W or y2 >= GRID_H:
            return False

        g = self.get_active_grid()

        a = g[y1][x1]
        b = g[y2][x2]

        # misma textura
        if a.floor_tex != b.floor_tex:
            return False

        dx = x2 - x1
        dy = y2 - y1

        top_a = self.get_tile_connection_height(a, dx, dy)
        top_b = self.get_tile_connection_height(b, -dx, -dy)

        # misma altura
        if abs(top_a - top_b) > 0.01:
            return False

        return True
    
    def is_autotile_texture(self, path):
        if not path:
            return False
        name = os.path.basename(path).lower()
        return "_auto" in name
    
        

    def tile_is_column(self, t):
        return getattr(t, "is_column", False)
    
    def recompute_column_faces(self, gx, gy):
        if gx < 0 or gy < 0 or gx >= GRID_W or gy >= GRID_H:
            return

        t = self.grid[gy][gx]

        if not getattr(t, "is_column", False):
            return

        h = t.wall_n_height

        # reset base
        t.wall_n = True
        t.wall_s = True
        t.wall_e = True
        t.wall_w = True

        # vecino norte
        if gy > 0 and getattr(self.grid[gy-1][gx], "is_column", False):
            t.wall_n = False

        # vecino sur
        if gy < GRID_H-1 and getattr(self.grid[gy+1][gx], "is_column", False):
            t.wall_s = False

        # vecino oeste
        if gx > 0 and getattr(self.grid[gy][gx-1], "is_column", False):
            t.wall_w = False

        # vecino este
        if gx < GRID_W-1 and getattr(self.grid[gy][gx+1], "is_column", False):
            t.wall_e = False

        # asegurar alturas
        t.wall_n_height = h
        t.wall_s_height = h
        t.wall_e_height = h
        t.wall_w_height = h

    def cycle_select_sprite_at_tile(self, gx, gy, t):
        if not hasattr(t, "sprites"):
            return

        if not t.sprites:
            return
        
        self.smart_selected_kind = "sprites"

        key = (gx, gy)

        idx = self.sprite_cycle_index.get(key, 0)

        if idx >= len(t.sprites):
            idx = 0

        inst = t.sprites[idx]

        self.load_sprite_into_panel(inst, gx, gy)

        idx += 1
        if idx >= len(t.sprites):
            idx = 0

        self.sprite_cycle_index[key] = idx

        self.draw_grid()

        print("SELECTED SPRITE:", inst.asset, "INDEX", idx)
    
    def open_wall_editor(self, gx, gy, direction):
        t = self.grid[gy][gx]
        WallSegmentEditor(self.root, t, direction, self)

    def paint_2d(self,e):
        gx=e.x//CELL_PIXELS
        gy=e.y//CELL_PIXELS
        if 0<=gx<GRID_W and 0<=gy<GRID_H:
            self.apply_tool(gx,gy)

    def serialize_object_instance(self, inst):
        return {
            "asset": inst["asset"],
            "offx": inst.get("offx",0),
            "offy": inst.get("offy",0),
            "offz": inst.get("offz",0),
            "rot_x": inst.get("rot_x",0),
            "rot_y": inst.get("rot_y",0),
            "rot_z": inst.get("rot_z",0)
        }
    
    def serialize_sprite_instance(self, spr):
        return {
            "asset": spr.asset,
            "offx": spr.offx,
            "offy": spr.offy,
            "offz": spr.offz,
            "state": spr.state,
            "current_anim": spr.animator.current if spr.animator else None,
            "frame": spr.animator.frame if spr.animator else 0
        }
    
    def ensure_project_maps(self):
        if not hasattr(self, "maps") or not self.maps:
            self.maps = {"Map001": self.grid}
            self.current_map_id = "Map001"

        if not hasattr(self, "current_map_id") or self.current_map_id not in self.maps:
            self.current_map_id = next(iter(self.maps))

        self.grid = self.maps[self.current_map_id]

    def sync_current_map(self):
        self.ensure_project_maps()
        self.maps[self.current_map_id] = self.grid

    def get_map_names(self):
        self.ensure_project_maps()
        return list(self.maps.keys())

    def refresh_map_selector(self):
        if not hasattr(self, "map_combo"):
            return

        self.ensure_project_maps()
        names = self.get_map_names()
        self.map_combo["values"] = names
        self.current_map_var.set(self.current_map_id)

        if hasattr(self, "map_status_label"):
            index = names.index(self.current_map_id) + 1
            self.map_status_label.configure(text=f"{index}/{len(names)} mapas")

    def reset_map_edit_selection(self):
        self.selected_instance = None
        self.selected_sprite = None
        self.selected_sprite_gx = None
        self.selected_sprite_gy = None
        self.selected_actor = None
        self.prefab_start = None
        self.prefab_end = None
        self.drag_start = None
        self.drag_end = None

    def switch_map(self, map_name):
        self.ensure_project_maps()

        if map_name not in self.maps or map_name == self.current_map_id:
            return

        if self.play_mode:
            messagebox.showwarning("Mapas", "No se puede cambiar de mapa mientras el runtime está activo.")
            self.current_map_var.set(self.current_map_id)
            return

        self.sync_current_map()
        self.current_map_id = map_name
        self.grid = self.maps[map_name]
        self.reset_map_edit_selection()
        self.refresh_map_selector()
        self.draw_grid()

    def on_map_combo_selected(self, event=None):
        self.switch_map(self.current_map_var.get())

    def make_unique_map_name(self, base="Map"):
        self.ensure_project_maps()
        existing = set(self.maps.keys())
        i = 1

        while True:
            name = f"{base}{i:03d}"
            if name not in existing:
                return name
            i += 1

    def ask_map_name(self, title, prompt, initialvalue=""):
        name = simpledialog.askstring(title, prompt, initialvalue=initialvalue, parent=self.root)

        if name is None:
            return None

        name = name.strip()
        if not name:
            messagebox.showwarning("Mapas", "El nombre del mapa no puede estar vacío.")
            return None

        return name

    def create_map(self):
        self.sync_current_map()
        default_name = self.make_unique_map_name()
        name = self.ask_map_name("Nuevo mapa", "Nombre del nuevo mapa:", default_name)

        if not name:
            return

        if name in self.maps:
            messagebox.showerror("Mapas", f"Ya existe un mapa llamado '{name}'.")
            return

        self.maps[name] = [[Tile() for _ in range(GRID_W)] for _ in range(GRID_H)]
        self.switch_map(name)

    def duplicate_current_map(self):
        self.sync_current_map()
        default_name = self.make_unique_map_name(f"{self.current_map_id}_copy")
        name = self.ask_map_name("Duplicar mapa", "Nombre de la copia:", default_name)

        if not name:
            return

        if name in self.maps:
            messagebox.showerror("Mapas", f"Ya existe un mapa llamado '{name}'.")
            return

        self.maps[name] = copy.deepcopy(self.grid)
        self.switch_map(name)

    def rename_current_map(self):
        self.sync_current_map()
        old_name = self.current_map_id
        new_name = self.ask_map_name("Renombrar mapa", "Nuevo nombre del mapa:", old_name)

        if not new_name or new_name == old_name:
            return

        if new_name in self.maps:
            messagebox.showerror("Mapas", f"Ya existe un mapa llamado '{new_name}'.")
            return

        self.maps[new_name] = self.maps.pop(old_name)
        self.current_map_id = new_name
        self.grid = self.maps[new_name]
        self.refresh_map_selector()
        self.draw_grid()

    def delete_current_map(self):
        self.ensure_project_maps()

        if len(self.maps) <= 1:
            messagebox.showwarning("Mapas", "El proyecto debe conservar al menos un mapa.")
            return

        if not messagebox.askyesno("Eliminar mapa", f"¿Eliminar el mapa '{self.current_map_id}'?"):
            return

        names = self.get_map_names()
        current_index = names.index(self.current_map_id)
        del self.maps[self.current_map_id]
        next_names = self.get_map_names()
        self.current_map_id = next_names[min(current_index, len(next_names) - 1)]
        self.grid = self.maps[self.current_map_id]
        self.reset_map_edit_selection()
        self.refresh_map_selector()
        self.draw_grid()

    def previous_map(self):
        names = self.get_map_names()
        if not names:
            return

        index = names.index(self.current_map_id)
        self.switch_map(names[(index - 1) % len(names)])

    def next_map(self):
        names = self.get_map_names()
        if not names:
            return

        index = names.index(self.current_map_id)
        self.switch_map(names[(index + 1) % len(names)])

    def serialize_tile(self, t):
        td = {
            "floor_tex": t.floor_tex,
            "wall_tex": t.wall_tex,
            "floor_height": getattr(t,"floor_height",0),
            "floor_uv_mode": getattr(t,"floor_uv_mode","tile"),
            "wall_uv_mode": getattr(t,"wall_uv_mode","tile"),
            "wall_n": getattr(t,"wall_n",False),
            "wall_s": getattr(t,"wall_s",False),
            "wall_e": getattr(t,"wall_e",False),
            "wall_w": getattr(t,"wall_w",False),
            "wall_ne": getattr(t,"wall_ne",False),
            "wall_nw": getattr(t,"wall_nw",False),
            "wall_se": getattr(t,"wall_se",False),
            "wall_sw": getattr(t,"wall_sw",False),
            "wall_n_height": getattr(t,"wall_n_height",1),
            "wall_s_height": getattr(t,"wall_s_height",1),
            "wall_e_height": getattr(t,"wall_e_height",1),
            "wall_w_height": getattr(t,"wall_w_height",1),
            "wall_ne_height": getattr(t,"wall_ne_height",1),
            "wall_se_height": getattr(t,"wall_se_height",1),
            "wall_nw_height": getattr(t,"wall_nw_height",1),
            "wall_sw_height": getattr(t,"wall_sw_height",1),
            "wall_segments": getattr(t,"wall_segments",{"n":[],"s":[],"e":[],"w":[],"ne":[],"nw":[],"se":[],"sw":[]}),
            "is_block" : getattr(t,"is_block",False),
            "block_bottom" : getattr(t,"block_bottom", 0.0),
            "block_top" : getattr(t,"block_top", 1.0),
            "block_side_tex" : getattr(t,"block_side_tex", None),
            "block_top_tex" : getattr(t,"block_top_tex", None),
            "block_uv_mode" : getattr(t,"block_uv_mode", "tile"),
            "objects": [],
            "sprites": [],
            "actors": [],
            "event_data": copy.deepcopy(getattr(t, "event_data", {}))
        }

        for inst in getattr(t, "objects", []):
            td["objects"].append(self.serialize_object_instance(inst))

        for spr in getattr(t, "sprites", []):
            td["sprites"].append(self.serialize_sprite_instance(spr))

        for pack in getattr(t, "actors", []):
            inst = pack["inst"]
            td["actors"].append({
                "actor_name": inst.actor_name,
                "offx": inst.offx,
                "offy": inst.offy,
                "offz": inst.offz,
                "rot": inst.rot,
                "state": inst.state,
                "facing": getattr(inst, "facing", "espalda"),
                "visual_facing": getattr(inst, "visual_facing", "espalda"),
                "current_anim": inst.animator.current if inst.animator else "",
                "frame": inst.animator.frame if inst.animator else 0,
                "timer": inst.animator.timer if inst.animator else 0,
                "is_npc" : getattr(inst, "is_npc", False),
                "npc_name" : getattr(inst, "npc_name", inst.actor_name),
                "interact_radius" : getattr(inst, "interact_radius", 1.2),
                "interact_text" : getattr(inst, "interact_text", "..."),
                "interact_once" : getattr(inst, "interact_once", False),
                "interacted" : getattr(inst, "interacted", False),
                "trigger_combat" : getattr(inst, "trigger_combat", False),
                "trigger_event" : getattr(inst, "trigger_event", ""),
                "vspeed" : getattr(inst, "vspeed", 0),
                "ground_z" : getattr(inst, "ground_z", 0),
                "on_ground" : getattr(inst, "on_ground", True),
                "is_jumping" : getattr(inst, "is_jumping", False),
                "jump_vspeed" : getattr(inst, "jump_vspeed", 0),
                "jump_gravity" : getattr(inst, "jump_gravity", 0),
                "jump_target_z" : getattr(inst, "jump_target_z", 0),
                "jump_land_done" : getattr(inst, "jump_land_done", False),
                "mantle_dest_gx" : getattr(inst, "mantle_dest_gx", 0),
                "mantle_dest_gy" : getattr(inst, "mantle_dest_gy", 0),
                "battle_team" : getattr(inst, "battle_team", "player"),
                "battle_moved" : getattr(inst, "battle_moved", False),
                "battle_acted" : getattr(inst, "battle_acted", False),
                "battle_dead" : getattr(inst, "battle_dead", False),
                "is_battle_moving" : getattr(inst, "is_battle_moving", False),
                "battle_move_timer" : getattr(inst, "battle_move_timer", 0)
            })

        return td

    def serialize_grid(self, grid):
        return [[self.serialize_tile(t) for t in row] for row in grid]

    def deserialize_tile(self, td, x, y):
        t = Tile()
        t.floor_tex = td.get("floor_tex")
        t.wall_tex = td.get("wall_tex")
        t.floor_height = td.get("floor_height", 0)
        t.floor_uv_mode = td.get("floor_uv_mode", "tile")
        t.wall_uv_mode = td.get("wall_uv_mode", "tile")
        t.wall_n = td.get("wall_n", False)
        t.wall_s = td.get("wall_s", False)
        t.wall_e = td.get("wall_e", False)
        t.wall_w = td.get("wall_w", False)
        t.wall_ne = td.get("wall_ne", False)
        t.wall_nw = td.get("wall_nw", False)
        t.wall_se = td.get("wall_se", False)
        t.wall_sw = td.get("wall_sw", False)
        t.wall_n_height = td.get("wall_n_height", 1)
        t.wall_s_height = td.get("wall_s_height", 1)
        t.wall_e_height = td.get("wall_e_height", 1)
        t.wall_w_height = td.get("wall_w_height", 1)
        t.wall_ne_height = td.get("wall_ne_height", 1)
        t.wall_se_height = td.get("wall_se_height", 1)
        t.wall_nw_height = td.get("wall_nw_height", 1)
        t.wall_sw_height = td.get("wall_sw_height", 1)
        t.wall_segments = td.get("wall_segments", {"n":[],"s":[],"e":[],"w":[],"ne":[],"nw":[],"se":[],"sw":[]})
        t.is_block = td.get("is_block", False)
        t.block_bottom = td.get("block_bottom", 0.0)
        t.block_top = td.get("block_top", 1.0)
        t.block_side_tex = td.get("block_side_tex", None)
        t.block_top_tex = td.get("block_top_tex", None)
        t.block_uv_mode = td.get("block_uv_mode", "tile")

        default_event = {
            "enabled": False,
            "trigger": "step",
            "scene": "",
            "dialog": "",
            "script": [],
            "teleport": None,
            "combat": False,
            "once": False,
            "done": False,
            "switch_required": "",
            "switch_set": "",
            "enemy_id": "",
            "item_required": "",
            "facing_lock": False
        }
        t.event_data = td.get("event_data", default_event.copy())
        t.events = td.get("events", [])

        if "event_data" not in td:
            if td.get("step_event", ""):
                t.event_data["enabled"] = True
                t.event_data["trigger"] = "step"
                t.event_data["scene"] = td.get("step_event", "")

            if td.get("action_event", ""):
                t.event_data["enabled"] = True
                t.event_data["trigger"] = "action"
                t.event_data["scene"] = td.get("action_event", "")

        t.objects = []
        for od in td.get("objects", []):
            t.objects.append({
                "asset": od.get("asset"),
                "offx": od.get("offx",0),
                "offy": od.get("offy",0),
                "offz": od.get("offz",0),
                "rot_x": od.get("rot_x",0),
                "rot_y": od.get("rot_y",0),
                "rot_z": od.get("rot_z",0)
            })

        t.sprites = []
        for sd in td.get("sprites", []):
            sprinst = SpriteInstance(sd.get("asset"))
            sprinst.offx = sd.get("offx",0)
            sprinst.offy = sd.get("offy",0)
            sprinst.offz = sd.get("offz",0)
            sprinst.state = sd.get("state","idle")

            if sprinst.asset in self.sprites:
                asset = self.sprites[sprinst.asset]
                sprinst.animator = Animator(self.clone_clips(asset.base_clips))
                current_anim = sd.get("current_anim")
                saved_frame = sd.get("frame",0)
                saved_timer = sd.get("timer",0)

                if current_anim:
                    sprinst.animator.play(current_anim)

                    if current_anim in sprinst.animator.clips:
                        maxf = len(sprinst.animator.clips[current_anim].frames)-1
                        sprinst.animator.frame = min(saved_frame, maxf)
                        sprinst.animator.timer = saved_timer
                elif asset.base_clips:
                    sprinst.animator.play(asset.base_clips[0].name)

            t.sprites.append(sprinst)

        t.actors = []
        for ad in td.get("actors", []):
            actor_name = ad.get("actor_name")

            if actor_name not in self.actors:
                continue

            inst = ActorInstance(actor_name)
            inst.offx = ad.get("offx", 0)
            inst.offy = ad.get("offy", 0)
            inst.offz = ad.get("offz", 0)
            inst.rot = ad.get("rot", 180)
            inst.state = ad.get("state", "idle")
            inst.facing = ad.get("facing", "espalda")
            inst.visual_facing = ad.get("visual_facing", "espalda")
            inst.battle_team = ad.get("battle_team", "player")
            inst.battle_moved = ad.get("battle_moved", False)
            inst.battle_acted = ad.get("battle_acted", False)
            inst.battle_dead = ad.get("battle_dead", False)
            inst.trigger_combat = ad.get("trigger_combat", False)
            inst.trigger_event = ad.get("trigger_event", "")
            inst.interact_radius = ad.get("interact_radius", 1.2)
            inst.interact_text = ad.get("interact_text", "...")
            inst.interact_once = ad.get("interact_once", False)
            inst.is_npc = ad.get("is_npc", False)
            inst.npc_name = ad.get("npc_name", actor_name)
            inst.interacted = ad.get("interacted", getattr(inst, "interacted", False))

            actor_def = self.actors[actor_name]

            if actor_def.sprite_sheets:
                sprname = actor_def.sprite_sheets[0]

                if sprname in self.sprites:
                    sprite_asset = self.sprites[sprname]
                    inst.animator = Animator(self.clone_clips(sprite_asset.base_clips))

                    if sprite_asset.base_clips:
                        current_anim = ad.get("current_anim", sprite_asset.base_clips[0].name)
                        inst.animator.play(current_anim)

                        if current_anim in inst.animator.clips:
                            maxf = len(inst.animator.clips[current_anim].frames)-1
                            inst.animator.frame = min(ad.get("frame",0), maxf)
                            inst.animator.timer = ad.get("timer",0)

            t.actors.append({"inst": inst, "gx": x, "gy": y})

        return t

    def deserialize_grid(self, grid_data):
        grid = [[Tile() for _ in range(GRID_W)] for _ in range(GRID_H)]

        for y, row in enumerate(grid_data[:GRID_H]):
            for x, td in enumerate(row[:GRID_W]):
                grid[y][x] = self.deserialize_tile(td, x, y)

        return grid

    def load_project_maps(self, data):
        loaded_maps = {}
        maps_data = data.get("maps", {})

        if maps_data:
            for map_name, map_data in maps_data.items():
                grid_data = map_data.get("grid", map_data if isinstance(map_data, list) else [])
                loaded_maps[map_name] = self.deserialize_grid(grid_data)
        else:
            loaded_maps["Map001"] = self.deserialize_grid(data.get("grid", []))

        if not loaded_maps:
            loaded_maps["Map001"] = [[Tile() for _ in range(GRID_W)] for _ in range(GRID_H)]

        requested_map = data.get("current_map")
        self.maps = loaded_maps
        self.current_map_id = requested_map if requested_map in self.maps else next(iter(self.maps))
        self.grid = self.maps[self.current_map_id]

    def save_project(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Project","*.json")]
        )
        if not path:
            return

        data = {
            "grid": [],
            "assets": {},
            "sprites": {},
            "actors": {},
            "skills": {},
            "items": {}
        }

        # =========================================
        # GRID / MAP SERIALIZATION
        # =========================================
        self.sync_current_map()
        data["project_version"] = 2
        data["current_map"] = self.current_map_id
        data["maps"] = {}

        for map_name, grid in self.maps.items():
            data["maps"][map_name] = {
                "name": map_name,
                "grid": self.serialize_grid(grid)
            }

        # Retrocompatibilidad: mantiene el mapa activo en la clave antigua.
        data["grid"] = data["maps"][self.current_map_id]["grid"]

        # =========================================
        # SAVE ASSETS (VOXEL/MESH)
        # =========================================
        for name, a in self.assets.items():

            if getattr(a,"mode","voxel") == "sprite":
                continue

            data["assets"][name] = {
                "mode": a.mode,
                "cubes": getattr(a,"cubes",[]),
                "tex_top": getattr(a,"tex_top",None),
                "tex_side": getattr(a,"tex_side",None),

                "mesh_vertices": getattr(a,"mesh_vertices",[]),
                "mesh_faces": getattr(a,"mesh_faces",[]),
                "mesh_uvs": getattr(a,"mesh_uvs",[]),
                "mesh_tex": getattr(a,"mesh_tex",None),
                "mesh_texcoords": getattr(a,"mesh_texcoords",[]),
                "mesh_face_uvs": getattr(a,"mesh_face_uvs",[]),
                "mesh_face_materials": getattr(a,"mesh_face_materials",[]),
                "mesh_material_textures": getattr(a,"mesh_material_textures",{})
            }

        # =========================================
        # SAVE SPRITES
        # =========================================
        for name, spr in self.sprites.items():
            image_path =  spr.image_path
            #nuevo_path = image_path[1:] 
            data["sprites"][name] = {
                "image_path": image_path,
                "sheet_cols": spr.sheet_cols,
                "sheet_rows": spr.sheet_rows,
                "frame_w": spr.frame_w,
                "frame_h": spr.frame_h,
                "width": spr.width,
                "height": spr.height,
                "clips":[]
            }

            for c in spr.base_clips:
                data["sprites"][name]["clips"].append({
                    "name": c.name,
                    "frames": c.frames,
                    "fps": c.fps,
                    "loop": c.loop
                })

        # =========================================
        # SAVE SKILLS DATABASE
        # =========================================

        for name, skill  in self.skills.items():
            data["skills"][name] = {
                "name": skill.name,
                "description": skill.description,
                "sp_cost": skill.sp_cost,
                "range": skill.range,
                "target_type": skill.target_type,
                "effect_type": skill.effect_type,
                "target_shape": skill.target_shape,
                "power": skill.power,
                "animation_sprite": skill.animation_sprite,
                "animation_clip_dere": skill.animation_clip_dere,
                "animation_clip_izq": skill.animation_clip_izq,
                "status_effect": skill.status_effect,
                "script": skill.script

            }

        # =========================================
        # SAVE ITEMS DATABASE
        # =========================================

        for name, item  in self.items.items():
            data["items"][name] = {
                "name": item.name,
                "description": item.description,
                "target_type": item.target_type,
                "effect_type": item.effect_type,
                "target_shape": item.target_shape,
                "power": item.power,
                "price": item.price,
                "consumable": item.consumable,
                "range": item.range,
                "script": item.script

            }

        # =========================================
        # SAVE ACTORS DATABASE
        # =========================================
        for name, a in self.actors.items():
            data["actors"][name] = {
                "name": a.name,
                "sprite_sheets": getattr(a,"sprite_sheets",[]),
                "kind": getattr(a,"kind","npc"),
                "event_file": getattr(a,"event_file",""),
                "is_main": getattr(a,"is_main",False),
                "interactive" : getattr(a,"interactive",True),
                # =========================
                # RPG STATS
                # =========================
                "level" : getattr(a,"level",1),

                "hp" : getattr(a,"hp",100),
                "max_hp" : getattr(a,"max_hp",100),

                "sp" : getattr(a,"sp",25),
                "max_sp" : getattr(a,"max_sp",25),

                "atk" : getattr(a,"atk",10),
                "defense" : getattr(a,"defense",5),
                "magic" : getattr(a,"magic",5),
                "resistance" : getattr(a,"resistance",5),
                "speed" : getattr(a,"speed",5),

                "move_range" : getattr(a,"move_range",4),

                "attack_range" : getattr(a,"attack_range",1),

                "initiative" : getattr(a,"initiative",10),

                "attack_bonus" : getattr(a,"attack_bonus",2),

                "armor_class" : getattr(a,"armor_class",10),

                "damage_max" : getattr(a,"damage_max",6),

                "body_type" : getattr(a,"body_type","normal"),

                # =========================
                # BATTLE
                # =========================
                "team" : getattr(a,"team","neutral"),
                "ai_mode" : getattr(a,"ai_mode","idle"),

                # =========================
                # INVENTORY
                # =========================
                "inventory" : getattr(a,"inventory",[]),

                # =========================
                # EQUIPMENT
                # =========================
                "weapon" : getattr(a,"weapon",""),
                "armor" : getattr(a,"armor",""),
                "accessory" : getattr(a,"accessory",""),

                # =========================
                # SKILLS
                # =========================
                "skills" : getattr(a,"skills",[]),

                # =========================
                # GROWTH
                # =========================
                "exp_reward" : getattr(a,"exp_reward",0),
                "gold_reward" : getattr(a,"gold_reward",0),

                # soporte multiple sprite sheets
                "sprite_sheets" : getattr(a,"sprite_sheets",[]),

            }

        with open(path,"w") as f:
            json.dump(data,f,indent=4)

        messagebox.showinfo("Save","Project saved.")

    def clone_clips(self, clips):
        out = []

        for c in clips:
            nc = AnimationClip(
                c.name,
                list(c.frames),
                c.fps,
                c.loop
            )
            out.append(nc)

        return out
        
    def load_project(self):
        path = filedialog.askopenfilename(filetypes=[("JSON Project","*.json")])
        if not path:
            return

        with open(path,"r") as f:
            data = json.load(f)

        # =========================================
        # RESET TOTAL
        # =========================================
        self.grid = [[Tile() for _ in range(GRID_W)] for _ in range(GRID_H)]
        self.assets = {}
        self.sprites = {}
        self.actors = {}

        self.asset_listbox.delete(0, tk.END)
        self.actor_listbox.delete(0, tk.END)

        # =========================================
        # LOAD ASSETS (VOXEL + MESH)
        # =========================================
        for name, ad in data.get("assets", {}).items():
            a = LowPolyAsset(name)

            a.mode = ad.get("mode", "voxel")

            a.cubes = ad.get("cubes", [])
            a.tex_top = ad.get("tex_top")
            a.tex_side = ad.get("tex_side")

            a.mesh_vertices = ad.get("mesh_vertices", [])
            a.mesh_faces = ad.get("mesh_faces", [])
            a.mesh_uvs = ad.get("mesh_uvs", [])
            a.mesh_tex = ad.get("mesh_tex")
            a.mesh_texcoords = ad.get("mesh_texcoords", [])
            a.mesh_face_uvs = ad.get("mesh_face_uvs", [])
            a.mesh_face_materials = ad.get("mesh_face_materials", [])
            a.mesh_material_textures = ad.get("mesh_material_textures", {})

            self.assets[name] = a
            self.asset_listbox.insert(tk.END, name)

        # =========================================
        # LOAD SPRITES
        # =========================================
        for name, sd in data.get("sprites", {}).items():

            spr = SpriteAsset(name, None, sd.get("image_path"))

            spr.image_path = sd.get("image_path")
            spr.sheet_cols = sd.get("sheet_cols", 1)
            spr.sheet_rows = sd.get("sheet_rows", 1)
            spr.frame_w = sd.get("frame_w", 64)
            spr.frame_h = sd.get("frame_h", 64)
            spr.width = sd.get("width", 1)
            spr.height = sd.get("height", 1)

            if spr.image_path and os.path.exists(spr.image_path):
                spr.texture = self.texture_manager.load_gl_texture(spr.image_path)
            else:
                spr.texture = None

            spr.base_clips = []

            for cd in sd.get("clips", []):
                clip = AnimationClip(
                    cd.get("name","clip"),
                    cd.get("frames",[]),
                    cd.get("fps",5),
                    cd.get("loop",True)
                )
                spr.base_clips.append(clip)

            self.sprites[name] = spr
            self.assets[name] = spr
            self.asset_listbox.insert(tk.END, name)

        # =========================================
        # LOAD ITEM DEFINITIONS
        # =========================================
        self.items = {}

        for name, ad in data.get("items", {}).items():
            item = ItemAsset(name)

            item.description = ad.get("description", "")
            item.target_type = ad.get("target_type", "ally")
            item.effect_type = ad.get("effect_type", "heal")
            item.target_shape = ad.get("target_shape", "diamond")
            item.power = ad.get("power", 25)
            item.price = ad.get("price", 0)
            item.consumable = ad.get("consumable", True)
            item.range = ad.get("range", 0)
            item.script = ad.get("script", [])

            self.items[name] = item
            #self.asset_listbox.insert(tk.END, name)

        # =========================================
        # LOAD SKILL DEFINITIONS
        # =========================================
        self.skills = {}

        for name, ad in data.get("skills", {}).items():
            skill = SkillAsset(name)

            skill.description = ad.get("description", "")
            skill.sp_cost = ad.get("sp_cost", 0)
            skill.range = ad.get("range", 1)
            skill.target_type = ad.get("target_type", "enemy")
            skill.effect_type = ad.get("effect_type", "damage")
            skill.target_shape = ad.get("target_shape", "diamond")
            skill.power = ad.get("power", 10)
            skill.animation_sprite = ad.get("animation_sprite", "")
            skill.animation_clip_dere = ad.get("animation_clip_dere", "")
            skill.animation_clip_izq = ad.get("animation_clip_izq", "")
            skill.status_effect = ad.get("status_effect", "")
            skill.script = ad.get("script", [])

            self.skills[name] = skill

        # =========================================
        # LOAD ACTOR DEFINITIONS
        # =========================================
        self.actors = {}

        for name, ad in data.get("actors", {}).items():
            actor = ActorAsset(name)

            actor.kind = ad.get("kind", "npc")
            actor.is_main = ad.get("is_main", False)
            actor.interactive = ad.get("interactive", True)
            actor.event_file = ad.get("event_file", "")
            
            actor.level = ad.get("level", 1)
            actor.hp = ad.get("hp", 100)
            actor.max_hp = ad.get("max_hp", 100)
            actor.sp = ad.get("sp", 25)
            actor.max_sp = ad.get("max_sp", 25)
            actor.atk = ad.get("atk", 10)
            actor.defense = ad.get("defense", 5)
            actor.magic = ad.get("defense", 5)
            actor.resistance = ad.get("resistance", 5)
            actor.speed = ad.get("speed", 5)

            actor.move_range = ad.get("move_range", 4)
            actor.attack_range = ad.get("attack_range", 1)

            actor.initiative = ad.get("initiative", 10)

            actor.attack_bonus = ad.get("attack_bonus", 2)

            actor.armor_class = ad.get("armor_class", 10)

            actor.damage_max = ad.get("damage_max", 6)

            actor.body_type = ad.get("body_type", "normal")

            # =========================
            # BATTLE
            # =========================
            actor.team = ad.get("team", "neutral")
            actor.ai_mode = ad.get("ai_mode", "idle")

            # =========================
            # INVENTORY
            # =========================
            actor.inventory = ad.get("inventory", [])

            # =========================
            # EQUIPMENT
            # =========================
            actor.weapon = ad.get("weapon", "")
            actor.armor = ad.get("armor", "")
            actor.accessory = ad.get("accessory", "")

            # =========================
            # SKILLS
            # =========================
            actor.skills = ad.get("skills", [])

            # =========================
            # GROWTH
            # =========================
            actor.exp_reward = ad.get("exp_reward", 0)
            actor.gold_reward = ad.get("gold_reward", 0)


            actor.sprite_sheets = ad.get("sprite_sheets", [])

            if not actor.sprite_sheets:
                oldspr = ad.get("sprite_asset", "")
                if oldspr:
                    actor.sprite_sheets = [oldspr]

            self.actors[name] = actor

        # =========================================
        # LOAD MAPS / GRID
        # =========================================
        self.load_project_maps(data)

        self.selected_instance = None
        self.selected_sprite = None
        self.refresh_actor_listbox()
        self.refresh_map_selector()
        self.draw_grid()

        messagebox.showinfo("Load","Project loaded.")

    def build_merged_floors(self):
        visited = [[False for _ in range(GRID_W)] for _ in range(GRID_H)]
        merged = []
        grid = self.get_active_grid()

        for y in range(GRID_H):
            for x in range(GRID_W):
                if visited[y][x]:
                    continue

                t = grid[y][x]

                if not t.floor_tex:
                    continue

                if "_" in t.floor_tex.lower():
                    continue

                tex = t.floor_tex
                h = t.floor_height

                width = 1
                while x + width < GRID_W:
                    nt = grid[y][x + width]
                    if visited[y][x + width]:
                        break
                    if nt.floor_tex != tex or abs(nt.floor_height - h) > 0.001:
                        break
                    if "_auto" in nt.floor_tex.lower():
                        break
                    width += 1

                height = 1
                can_expand = True

                while y + height < GRID_H and can_expand:
                    for xx in range(x, x + width):
                        nt = grid[y + height][xx]
                        if visited[y + height][xx]:
                            can_expand = False
                            break
                        if nt.floor_tex != tex or abs(nt.floor_height - h) > 0.001:
                            can_expand = False
                            break
                        if "_auto" in nt.floor_tex.lower():
                            can_expand = False
                            break
                    if can_expand:
                        height += 1

                for yy in range(y, y + height):
                    for xx in range(x, x + width):
                        visited[yy][xx] = True

                merged.append((x, y, width, height, tex, h))

        return merged
    
    
    def get_autotile_indices(self, x, y, texname):

        W = self.same_autotile_group(x,y,x-1,y)
        N = self.same_autotile_group(x,y,x,y-1)
        E = self.same_autotile_group(x,y,x+1,y)
        S = self.same_autotile_group(x,y,x,y+1)

        NW = self.same_autotile_group(x,y,x-1,y-1)
        NE = self.same_autotile_group(x,y,x+1,y-1)
        SW = self.same_autotile_group(x,y,x-1,y+1)
        SE = self.same_autotile_group(x,y,x+1,y+1)

##        out = [0,0,0,0]
        out = [8,11,20,23]

        # =========================
        # NW
        # =========================
        if N == 1 and W == 1 and NW == 0:
            out[0] = 2   # interior
        elif N == 0 and W == 1:
            out[0] = 10   # borde vertical
        elif N == 1 and W == 0:
            out[0] = 16   # borde horizontal
        elif N == 1 and W == 1 and NW==1:
            out[0] = 18   # esquina exterior

        # =========================
        # NE
        # =========================
        if N == 1 and E == 1 and NE == 0:
            out[1] = 3
        elif N == 0 and E == 1:
            out[1] = 9
        elif N == 1 and E == 0:
            out[1] = 19
        elif N == 1 and E == 1 and NE == 1:
            out[1] = 14

        # =========================
        # SW
        # =========================
        if S == 1 and W == 1 and SW == 0:
            out[2] = 6
        elif S == 0 and W == 1:
            out[2] = 22
        elif S == 1 and W == 0:
            out[2] = 12
        elif S == 1 and W == 1 and SW == 1:
            out[2] = 17

        # =========================
        # SE
        # =========================
        if S == 1 and E == 1 and SE == 0:
            out[3] = 7  
        elif S == 0 and E == 1:
            out[3] = 21
        elif S == 1 and E == 0:
            out[3] = 15
        elif S == 1 and E == 1 and SE == 1:
            out[3] = 13

        return out
    
    def autotile_match(self, x, y, texname):
        if x < 0 or y < 0 or x >= GRID_W or y >= GRID_H:
            return False

        t = self.get_active_grid()[y][x]

        if not t.floor_tex:
            return False

        return t.floor_tex == texname
    
    def build_merged_walls(self):
        walls = []

        # NORTH/SOUTH horizontal strips
        for side in ['n','s']:
            visited = [[False for _ in range(GRID_W)] for _ in range(GRID_H)]

            for y in range(GRID_H):
                for x in range(GRID_W):
                    if visited[y][x]:
                        continue

                    t = self.grid[y][x]
                    active = getattr(t, f'wall_{side}')
                    h = getattr(t, f'wall_{side}_height')

                    if not active:
                        continue

                    tex = t.wall_tex
                    fh = t.floor_height

                    width = 1
                    while x + width < GRID_W:
                        nt = self.grid[y][x + width]
                        if visited[y][x + width]:
                            break
                        if not getattr(nt, f'wall_{side}'):
                            break
                        if nt.wall_tex != tex:
                            break
                        if abs(getattr(nt, f'wall_{side}_height') - h) > 0.001:
                            break
                        if abs(nt.floor_height - fh) > 0.001:
                            break
                        width += 1

                    for xx in range(x, x + width):
                        visited[y][xx] = True

                    walls.append((side, x, y, width, tex, fh, h))

        # EAST/WEST vertical strips
        for side in ['e','w']:
            visited = [[False for _ in range(GRID_W)] for _ in range(GRID_H)]

            for y in range(GRID_H):
                for x in range(GRID_W):
                    if visited[y][x]:
                        continue

                    t = self.grid[y][x]
                    active = getattr(t, f'wall_{side}')
                    h = getattr(t, f'wall_{side}_height')

                    if not active:
                        continue

                    tex = t.wall_tex
                    fh = t.floor_height

                    heightrun = 1
                    while y + heightrun < GRID_H:
                        nt = self.grid[y + heightrun][x]
                        if visited[y + heightrun][x]:
                            break
                        if not getattr(nt, f'wall_{side}'):
                            break
                        if nt.wall_tex != tex:
                            break
                        if abs(getattr(nt, f'wall_{side}_height') - h) > 0.001:
                            break
                        if abs(nt.floor_height - fh) > 0.001:
                            break
                        heightrun += 1

                    for yy in range(y, y + heightrun):
                        visited[yy][x] = True

                    walls.append((side, x, y, heightrun, tex, fh, h))

        return walls
    
    def build_visible_asset_faces(self, asset, tile_x, tile_y, floor_h):
        faces = []
        cubeset = set(tuple(c) for c in asset.cubes)
        s = 0.2

        directions = [
            ((1,0,0), 'xp'),
            ((-1,0,0), 'xn'),
            ((0,1,0), 'yp'),
            ((0,-1,0), 'yn'),
            ((0,0,1), 'zp'),
            ((0,0,-1), 'zn')
        ]

        for vx,vy,vz in cubeset:
            bx = tile_x + vx * s
            by = floor_h + vz * s
            bz = tile_y + vy * s

            for (dx,dy,dz), faceid in directions:
                neighbor = (vx+dx, vy+dy, vz+dz)

                if neighbor in cubeset:
                    continue

                if faceid == 'xp':
                    quad = [
                        (bx+s,by,bz),
                        (bx+s,by,bz+s),
                        (bx+s,by+s,bz+s),
                        (bx+s,by+s,bz)
                    ]

                elif faceid == 'xn':
                    quad = [
                        (bx,by,bz),
                        (bx,by+s,bz),
                        (bx,by+s,bz+s),
                        (bx,by,bz+s)
                    ]

                elif faceid == 'yp':
                    quad = [
                        (bx,by,bz+s),
                        (bx+s,by,bz+s),
                        (bx+s,by+s,bz+s),
                        (bx,by+s,bz+s)
                    ]

                elif faceid == 'yn':
                    quad = [
                        (bx,by,bz),
                        (bx,by+s,bz),
                        (bx+s,by+s,bz),
                        (bx+s,by,bz)
                    ]

                elif faceid == 'zp':
                    quad = [
                        (bx,by+s,bz),
                        (bx+s,by+s,bz),
                        (bx+s,by+s,bz+s),
                        (bx,by+s,bz+s)
                    ]

                elif faceid == 'zn':
                    quad = [
                        (bx,by,bz),
                        (bx+s,by,bz),
                        (bx+s,by,bz+s),
                        (bx,by,bz+s)
                    ]

                faces.append(quad)

        return faces
    
    def add_export_quad(self, lines, p1, p2, p3, p4, texname):
        texname = os.path.basename(texname) if texname else "none.png"

        lines.append("{")
        lines.append(
            f'{{{{{p1[0]},{p1[1]},{p1[2]},0,0}},'
            f'{{{p2[0]},{p2[1]},{p2[2]},1,0}},'
            f'{{{p3[0]},{p3[1]},{p3[2]},1,1}},'
            f'{{{p4[0]},{p4[1]},{p4[2]},0,1}}}},'
        )
        lines.append(f'"{texname}"')
        lines.append("},")

    def export_dreamcast(self):
        header = []
        header.append("#ifndef GAME_DATA_H")
        header.append("#define GAME_DATA_H")
        header.append("")
        header.append("// =====================================")
        header.append("// AUTO GENERATED DREAMCAST GAME DATA")
        header.append("// =====================================")
        header.append("")

        header.append("typedef struct { float x,y,z,u,v; } DCVTX;")
        header.append("typedef struct { DCVTX v[4]; char tex[64]; } DCQUAD;")
        header.append("typedef struct { float x,y,z,w,h; char tex[64]; int cols; int rows; } DCSPRITE;")
        header.append("typedef struct {")
        header.append("float x,y,z;")
        header.append("char name[64];")
        header.append("char kind[32];")
        header.append("char tex[64];")
        header.append("char event_file[128];")
        header.append("int cols;")
        header.append("int rows;")
        header.append("int is_main;")
        header.append("int interactive;")
        header.append("int hp,mp,atk,defense,speed;")
        header.append("} DCACTOR;")
        header.append('typedef struct { int gx,gy; char trigger[32]; char scene[128]; } DCEVENT;')
        header.append("")

        export_path = filedialog.askdirectory(title="Seleccionar carpeta export runtime Dreamcast")
        if not export_path:
            return

        tex_folder = os.path.join(export_path, "textures")
        os.makedirs(tex_folder, exist_ok=True)

        used_textures = set()

        # ======================================================
        # RECOLECTAR TEXTURAS USADAS
        # ======================================================
        for row in self.grid:
            for t in row:
                if t.floor_tex: used_textures.add(t.floor_tex)
                if t.wall_tex: used_textures.add(t.wall_tex)

                for segdir in ["n","s","e","w"]:
                    for seg in t.wall_segments.get(segdir, []):
                        if seg.get("tex"):
                            used_textures.add(seg["tex"])

        for a in self.assets.values():
            if getattr(a,"mode","voxel") == "sprite":
                continue

            if getattr(a,"tex_top",None): used_textures.add(a.tex_top)
            if getattr(a,"tex_side",None): used_textures.add(a.tex_side)
            if getattr(a,"mesh_tex",None): used_textures.add(a.mesh_tex)

            for mt in getattr(a,"mesh_material_textures",{}).values():
                if mt:
                    used_textures.add(mt)

        for spr in self.sprites.values():
            if spr.image_path:
                used_textures.add(spr.image_path)

        # copiar texturas
        for tex in used_textures:
            if os.path.isabs(tex):
                src = tex
                dst = os.path.join(tex_folder, os.path.basename(tex))
            else:
                src = os.path.join(TEXTURE_FOLDER, tex)
                dst = os.path.join(tex_folder, os.path.basename(tex))

            if os.path.exists(src):
                try:
                    Image.open(src).save(dst)
                except:
                    pass

        with open(os.path.join(export_path, "texture_manifest.h"), "w") as f:
            for tex in used_textures:
                f.write(os.path.basename(tex) + "\n")

        # ======================================================
        # EXPORT GEOMETRY
        # ======================================================
        geo = []
        geo.append("// DREAMCAST STATIC GEOMETRY")
        geo.append("typedef struct { float x,y,z,u,v; } DCVTX;")
        geo.append('typedef struct { DCVTX v[4]; char tex[64]; } DCQUAD;')
        geo.append("DCQUAD scene_quads[] = {")

        for gy in range(GRID_H):
            for gx in range(GRID_W):
                t = self.grid[gy][gx]
                fh = t.floor_height

                # FLOOR
                self.add_export_quad(
                    geo,
                    (gx,fh,gy),
                    (gx+1,fh,gy),
                    (gx+1,fh,gy+1),
                    (gx,fh,gy+1),
                    t.floor_tex
                )

                # NORMAL WALLS + SEGMENTS
                for side in ["n","s","e","w"]:
                    if t.wall_segments.get(side):
                        base = fh
                        for seg in t.wall_segments[side]:
                            h0 = base
                            h1 = base + seg.get("h",1)
                            tex = seg.get("tex", t.wall_tex)

                            if side == "n":
                                self.add_export_quad(geo,(gx,h0,gy),(gx+1,h0,gy),(gx+1,h1,gy),(gx,h1,gy),tex)
                            elif side == "s":
                                self.add_export_quad(geo,(gx,h0,gy+1),(gx+1,h0,gy+1),(gx+1,h1,gy+1),(gx,h1,gy+1),tex)
                            elif side == "e":
                                self.add_export_quad(geo,(gx+1,h0,gy),(gx+1,h0,gy+1),(gx+1,h1,gy+1),(gx+1,h1,gy),tex)
                            elif side == "w":
                                self.add_export_quad(geo,(gx,h0,gy),(gx,h0,gy+1),(gx,h1,gy+1),(gx,h1,gy),tex)

                            base = h1
                    else:
                        h = fh + 1.0

                        if t.wall_n and side=="n":
                            self.add_export_quad(geo,(gx,fh,gy),(gx+1,fh,gy),(gx+1,h,gy),(gx,h,gy),t.wall_tex)
                        if t.wall_s and side=="s":
                            self.add_export_quad(geo,(gx,fh,gy+1),(gx+1,fh,gy+1),(gx+1,h,gy+1),(gx,h,gy+1),t.wall_tex)
                        if t.wall_e and side=="e":
                            self.add_export_quad(geo,(gx+1,fh,gy),(gx+1,fh,gy+1),(gx+1,h,gy+1),(gx+1,h,gy),t.wall_tex)
                        if t.wall_w and side=="w":
                            self.add_export_quad(geo,(gx,fh,gy),(gx,fh,gy+1),(gx,h,gy+1),(gx,h,gy),t.wall_tex)

                # DIAGONALS
                h = fh + 1.0

                if t.wall_ne:
                    self.add_export_quad(geo,(gx,fh,gy),(gx+1,fh,gy+1),(gx+1,h,gy+1),(gx,h,gy),t.wall_tex)

                if t.wall_nw:
                    self.add_export_quad(geo,(gx+1,fh,gy),(gx,fh,gy+1),(gx,h,gy+1),(gx+1,h,gy),t.wall_tex)

                if t.wall_se:
                    self.add_export_quad(geo,(gx,fh,gy+1),(gx+1,fh,gy),(gx+1,h,gy),(gx,h,gy+1),t.wall_tex)

                if t.wall_sw:
                    self.add_export_quad(geo,(gx,fh,gy),(gx+1,fh,gy+1),(gx+1,h,gy+1),(gx,h,gy),t.wall_tex)

                # OBJECTS
                for inst in t.objects:
                    asset_name = inst["asset"]
                    if asset_name not in self.assets:
                        continue

                    asset = self.assets[asset_name]

                    if asset.mode == "mesh":
                        for face in asset.mesh_faces:
                            pts = []
                            for idx in face[:4]:
                                vx,vy,vz = asset.mesh_vertices[idx]
                                lx,ly,lz = rotate_3d(vx,vy,vz,inst["rot_x"],inst["rot_y"],inst["rot_z"])
                                pts.append((gx+inst["offx"]+lx, fh+inst["offz"]+ly, gy+inst["offy"]+lz))

                            if len(pts)==3:
                                pts.append(pts[2])

                            self.add_export_quad(geo, pts[0],pts[1],pts[2],pts[3], asset.mesh_tex)
                    else:
                        faces = self.build_visible_asset_faces(asset,0,0,0)

                        for quad in faces:
                            transformed=[]
                            for px,py,pz in quad:
                                lx,ly,lz = rotate_3d(px,py,pz,inst["rot_x"],inst["rot_y"],inst["rot_z"])
                                transformed.append((gx+inst["offx"]+lx, fh+inst["offz"]+ly, gy+inst["offy"]+lz))

                            self.add_export_quad(
                                geo,
                                transformed[0],transformed[1],transformed[2],transformed[3],
                                asset.tex_side or asset.tex_top
                            )

        geo.append("};")

        with open(os.path.join(export_path,"scene_runtime.c"),"w") as f:
            f.write("\n".join(geo))

        # ======================================================
        # EXPORT DECORATIVE SPRITES
        # ======================================================
        spr = []
        spr.append("// DREAMCAST DECORATIVE SPRITES")
        spr.append('typedef struct { float x,y,z,w,h; char tex[64]; int cols; int rows; } DCSPRITE;')
        spr.append("DCSPRITE scene_sprites[] = {")

        for gy in range(GRID_H):
            for gx in range(GRID_W):
                t = self.grid[gy][gx]

                for s in t.sprites:
                    if s.asset not in self.sprites:
                        continue

                    asset = self.sprites[s.asset]

                    wx = gx + s.offx
                    wy = t.floor_height + s.offz
                    wz = gy + s.offy

                    spr.append(
                        f'{{{wx},{wy},{wz},{asset.width},{asset.height},"{os.path.basename(asset.image_path)}",{asset.sheet_cols},{asset.sheet_rows}}},'
                    )

        spr.append("};")

        with open(os.path.join(export_path,"sprite_runtime.c"),"w") as f:
            f.write("\n".join(spr))

        exported_scene_files = set()

        def export_scene_script_recursive(scene_path):
            if not scene_path:
                return ""

            if not os.path.exists(scene_path):
                scene_try = os.path.join("scenes", scene_path)
            else:
                scene_try = scene_path

            if not os.path.exists(scene_try):
                return scene_path

            base = os.path.basename(scene_try)

            if base in exported_scene_files:
                return base

            exported_scene_files.add(base)

            with open(scene_try, "r", encoding="utf8") as sf:
                try:
                    sdata = json.load(sf)
                except:
                    return base

            # -----------------------------
            # background
            # -----------------------------
            if "background" in sdata:
                newbg = safe_copy_runtime_file(sdata["background"], media_folder)
                sdata["background"] = os.path.join("media", newbg)

            # -----------------------------
            # sprites portraits VN
            # -----------------------------
            for spr in sdata.get("sprites", []):
                if "texture" in spr:
                    newspr = safe_copy_runtime_file(spr["texture"], media_folder)
                    spr["texture"] = os.path.join("media", newspr)

            # -----------------------------
            # script actions
            # -----------------------------
            for cmd in sdata.get("script", []):

                if "music" in cmd:
                    nm = safe_copy_runtime_file(cmd["music"], media_folder)
                    cmd["music"] = os.path.join("media", nm)

                if "sound" in cmd:
                    ns = safe_copy_runtime_file(cmd["sound"], media_folder)
                    cmd["sound"] = os.path.join("media", ns)

                if "voice" in cmd:
                    nv = safe_copy_runtime_file(cmd["voice"], media_folder)
                    cmd["voice"] = os.path.join("media", nv)

                if cmd.get("action") == "next_scene":
                    nxt = cmd.get("scene_new", "")
                    exported = export_scene_script_recursive(nxt)
                    cmd["scene_new"] = os.path.join("scenes", exported)

            # guardar json reescrito
            outpath = os.path.join(scene_folder, base)

            with open(outpath, "w", encoding="utf8") as outf:
                json.dump(sdata, outf, indent=4)

            return base

        def safe_copy_runtime_file(srcfile, dstfolder):
            if not srcfile:
                return ""

            if os.path.isabs(srcfile):
                src = srcfile
            else:
                src = srcfile

            if not os.path.exists(src):
                return srcfile

            dst = os.path.join(dstfolder, os.path.basename(src))

            try:
                shutil.copy(src, dst)
            except:
                pass

            return os.path.basename(src)

        # ======================================================
        # EXPORT ACTORS
        # ======================================================
        act = []
        act.append("// DREAMCAST ACTOR RUNTIME")
        act.append('typedef struct {')
        act.append('float x,y,z;')
        act.append('char name[64];')
        act.append('char kind[32];')
        act.append('char tex[64];')
        act.append('char event_file[128];')
        act.append('int cols;')
        act.append('int rows;')
        act.append('int is_main;')
        act.append('int interactive;')
        act.append('int hp,mp,atk,defense,speed;')
        act.append('} DCACTOR;')
        act.append("DCACTOR scene_actors[] = {")

        for gy in range(GRID_H):
            for gx in range(GRID_W):
                t = self.grid[gy][gx]

                for pack in t.actors:
                    inst = pack["inst"]

                    if inst.actor_name not in self.actors:
                        continue

                    actor = self.actors[inst.actor_name]

                    if not actor.sprite_sheets:
                        continue

                    sprname = actor.sprite_sheets[0]

                    if sprname not in self.sprites:
                        continue

                    sprite = self.sprites[sprname]

                    wx = gx + inst.offx
                    wy = t.floor_height + inst.offz
                    wz = gy + inst.offy

                    act.append(
                        f'{{{wx},{wy},{wz},"{actor.name}","{actor.kind}","{os.path.basename(sprite.image_path)}","{actor.event_file}",'
                        f'{sprite.sheet_cols},{sprite.sheet_rows},{1 if actor.is_main else 0},{1 if actor.interactive else 0},'
                        f'{actor.hp},{actor.mp},{actor.atk},{actor.defense},{actor.speed}}},'
                    )

        act.append("};")

        with open(os.path.join(export_path,"actor_runtime.c"),"w") as f:
            f.write("\n".join(act))

        # ======================================================
        # EXPORT EVENT TILES
        # ======================================================
        evt = []
        evt.append("// DREAMCAST EVENT TILE RUNTIME")
        evt.append('typedef struct { int gx,gy; char trigger[32]; char scene[128]; } DCEVENT;')
        evt.append("DCEVENT scene_events[] = {")

        for gy in range(GRID_H):
            for gx in range(GRID_W):
                t = self.grid[gy][gx]
                

                #for ev in getattr(t, "events", []):
                 #   trigger = ev.get("trigger","on_enter")
                  #  scene = ev.get("scene","")

                   # evt.append(f'{{{gx},{gy},"{trigger}","{scene}"}},')

        evt.append("};")

        with open(os.path.join(export_path,"event_runtime.c"),"w") as f:
            f.write("\n".join(evt))

        header.append(f"#define SCENE_QUAD_COUNT {len([x for x in geo if x.strip().startswith('{{')])}")
        header.append(f"#define SCENE_SPRITE_COUNT {len([x for x in spr if x.strip().startswith('{{')])}")
        header.append(f"#define SCENE_ACTOR_COUNT {len([x for x in act if x.strip().startswith('{{')])}")
        header.append(f"#define SCENE_EVENT_COUNT {len([x for x in evt if x.strip().startswith('{{')])}")
        header.append("")

        header.append("DCQUAD scene_quads[] = {")
        header.extend(geo)
        header.append("};")
        header.append("")

        header.append("DCSPRITE scene_sprites[] = {")
        header.extend(spr)
        header.append("};")
        header.append("")

        header.append("DCACTOR scene_actors[] = {")
        header.extend(act)
        header.append("};")
        header.append("")

        header.append("DCEVENT scene_events[] = {")
        header.extend(evt)
        header.append("};")
        header.append("")

        header.append(f"#define TEXTURE_COUNT {len(used_textures)}")
        header.append("char* texture_manifest[] = {")
        for tex in used_textures:
            header.append(f'"{os.path.basename(tex)}",')
        header.append("};")
        header.append("")
        header.append("#endif")

        with open(os.path.join(export_path,"game_data.h"),"w", encoding="utf8") as f:
            f.write("\n".join(header))

        print("EXPORT DREAMCAST FULL COMPLETADO:", export_path)
        messagebox.showinfo("Export", "Dreamcast runtime export completed.")

    def export_standard_walls(self, geo, gx, gy, t):
        fh = t.floor_height

        if t.wall_n:
            self.add_export_quad(geo,(gx,fh,gy),(gx+1,fh,gy),(gx+1,fh+t.wall_n_height,gy),(gx,fh+t.wall_n_height,gy),t.wall_tex)

        if t.wall_s:
            self.add_export_quad(geo,(gx,fh,gy+1),(gx+1,fh,gy+1),(gx+1,fh+t.wall_s_height,gy+1),(gx,fh+t.wall_s_height,gy+1),t.wall_tex)

        if t.wall_e:
            self.add_export_quad(geo,(gx+1,fh,gy),(gx+1,fh,gy+1),(gx+1,fh+t.wall_e_height,gy+1),(gx+1,fh+t.wall_e_height,gy),t.wall_tex)

        if t.wall_w:
            self.add_export_quad(geo,(gx,fh,gy),(gx,fh,gy+1),(gx,fh+t.wall_w_height,gy+1),(gx,fh+t.wall_w_height,gy),t.wall_tex)

    def export_segmented_walls(self, geo, gx, gy, t):
        for side in ["n","s","e","w"]:
            base = t.floor_height

            for seg in t.wall_segments.get(side, []):
                h0 = base
                h1 = base + seg.get("h",1.0)
                tex = seg.get("tex")

                if side == "n":
                    self.add_export_quad(geo,(gx,h0,gy),(gx+1,h0,gy),(gx+1,h1,gy),(gx,h1,gy),tex)

                elif side == "s":
                    self.add_export_quad(geo,(gx,h0,gy+1),(gx+1,h0,gy+1),(gx+1,h1,gy+1),(gx,h1,gy+1),tex)

                elif side == "e":
                    self.add_export_quad(geo,(gx+1,h0,gy),(gx+1,h0,gy+1),(gx+1,h1,gy+1),(gx+1,h1,gy),tex)

                elif side == "w":
                    self.add_export_quad(geo,(gx,h0,gy),(gx,h0,gy+1),(gx,h1,gy+1),(gx,h1,gy),tex)

                base = h1

    def export_objects_to_geo(self, geo, gx, gy, t, fh):
        for inst in t.objects:
            asset_name = inst["asset"]

            if asset_name not in self.assets:
                continue

            asset = self.assets[asset_name]

            if asset.mode == "mesh":
                for face in asset.mesh_faces:
                    pts = []

                    for idx in face[:4]:
                        vx,vy,vz = asset.mesh_vertices[idx]
                        lx,ly,lz = rotate_3d(vx,vy,vz,inst["rot_x"],inst["rot_y"],inst["rot_z"])
                        pts.append((gx+inst["offx"]+lx, fh+inst["offz"]+ly, gy+inst["offy"]+lz))

                    if len(pts) == 3:
                        pts.append(pts[2])

                    self.add_export_quad(geo, pts[0], pts[1], pts[2], pts[3], asset.mesh_tex)

            else:
                faces = self.build_visible_asset_faces(asset,0,0,0)

                for quad in faces:
                    transformed = []

                    for px,py,pz in quad:
                        lx,ly,lz = rotate_3d(px,py,pz,inst["rot_x"],inst["rot_y"],inst["rot_z"])
                        transformed.append((gx+inst["offx"]+lx, fh+inst["offz"]+ly, gy+inst["offy"]+lz))

                    self.add_export_quad(
                        geo,
                        transformed[0],
                        transformed[1],
                        transformed[2],
                        transformed[3],
                        asset.tex_side or asset.tex_top
                    )

    def export_sprite_runtime(self, export_path):
        spr = []
        spr.append('// DREAMCAST SPRITE RUNTIME')
        spr.append('typedef struct {')
        spr.append('float x,y,z;')
        spr.append('float w,h;')
        spr.append('char tex[64];')
        spr.append('int cols,rows;')
        spr.append('int anim;')
        spr.append('int frame;')
        spr.append('} DCSPRITE;')
        spr.append('DCSPRITE scene_sprites[] = {')

        for gy in range(GRID_H):
            for gx in range(GRID_W):
                t = self.grid[gy][gx]

                for s in t.sprites:
                    if s.asset not in self.sprites:
                        continue

                    asset = self.sprites[s.asset]

                    wx = gx + s.offx
                    wy = t.floor_height + s.offz
                    wz = gy + s.offy

                    spr.append(
                        f'{{{wx},{wy},{wz},{asset.width},{asset.height},"{os.path.basename(asset.image_path)}",{asset.sheet_cols},{asset.sheet_rows},0,0}},'
                    )

        spr.append('};')

        with open(os.path.join(export_path,'sprite_runtime.c'),'w') as f:
            f.write('\n'.join(spr))

    def export_actor_runtime(self, export_path):
        act = []
        act.append('// DREAMCAST ACTOR RUNTIME')
        act.append('typedef struct {')
        act.append('float x,y,z;')
        act.append('char actor_name[64];')
        act.append('int actor_type;')
        act.append('char linked_script[128];')
        act.append('} DCACTOR;')
        act.append('DCACTOR scene_actors[] = {')

        for gy in range(GRID_H):
            for gx in range(GRID_W):
                t = self.grid[gy][gx]

                for pack in t.actors:
                    inst = pack["inst"]

                    if inst.actor_name not in self.actors:
                        continue

                    actor = self.actors[inst.actor_name]

                    wx = pack["gx"] + inst.offx
                    wy = self.grid[pack["gy"]][pack["gx"]].floor_height + inst.offz
                    wz = pack["gy"] + inst.offy

                    atype = 0
                    if actor.actor_type == "main":
                        atype = 1
                    elif actor.actor_type == "npc":
                        atype = 2
                    elif actor.actor_type == "enemy":
                        atype = 3
                    elif actor.actor_type == "party":
                        atype = 4

                    scriptname = actor.script_json if actor.script_json else ""

                    act.append(
                        f'{{{wx},{wy},{wz},"{actor.name}",{atype},"{os.path.basename(scriptname)}"}},'
                    )

        act.append('};')

        with open(os.path.join(export_path,'actor_runtime.c'),'w') as f:
            f.write('\n'.join(act))

    def export_event_runtime(self, export_path):
        ev = []
        ev.append('// DREAMCAST EVENT TILE RUNTIME')
        ev.append('typedef struct {')
        ev.append('int gx,gy;')
        ev.append('int trigger_type;')
        ev.append('char action[64];')
        ev.append('char linked_script[128];')
        ev.append('} DCEVENT;')
        ev.append('DCEVENT scene_events[] = {')

        for gy in range(GRID_H):
            for gx in range(GRID_W):
                t = self.grid[gy][gx]

                for e in getattr(t, "events", []):

                    trig = 0
                    if e["trigger"] == "touch":
                        trig = 1
                    elif e["trigger"] == "interact":
                        trig = 2
                    elif e["trigger"] == "autorun":
                        trig = 3

                    action = e.get("action","")

                    scriptname = e.get("script","")

                    ev.append(
                        f'{{{gx},{gy},{trig},"{action}","{os.path.basename(scriptname)}"}},'
                    )

        ev.append('};')

        with open(os.path.join(export_path,'event_runtime.c'),'w') as f:
            f.write('\n'.join(ev))

    def export_actor_definitions(self, export_path):
        db = []
        db.append('// DREAMCAST ACTOR DATABASE')
        db.append('typedef struct {')
        db.append('char name[64];')
        db.append('char sprite_tex[64];')
        db.append('int cols,rows;')
        db.append('float w,h;')
        db.append('int actor_type;')
        db.append('char script_json[128];')
        db.append('} DCACTORDEF;')
        db.append('DCACTORDEF actor_database[] = {')

        for name, actor in self.actors.items():

            if not actor.sprite_assets:
                continue

            sprname = actor.sprite_assets[0]

            if sprname not in self.sprites:
                continue

            spr = self.sprites[sprname]

            atype = 0
            if actor.actor_type == "main":
                atype = 1
            elif actor.actor_type == "npc":
                atype = 2
            elif actor.actor_type == "enemy":
                atype = 3
            elif actor.actor_type == "party":
                atype = 4

            scriptname = actor.script_json if actor.script_json else ""

            db.append(
                f'{{"{actor.name}","{os.path.basename(spr.image_path)}",{spr.sheet_cols},{spr.sheet_rows},{spr.width},{spr.height},{atype},"{os.path.basename(scriptname)}"}},'
            )

        db.append('};')

        with open(os.path.join(export_path,'actor_database.c'),'w') as f:
            f.write('\n'.join(db))

    def open_delete_popup(self):
        gx = getattr(self, "last_clicked_gx", None)
        gy = getattr(self, "last_clicked_gy", None)

        if gx is None or gy is None:
            return

        t = self.grid[gy][gx]

        print("DELETE POPUP CELL:", gx, gy)

        print("OBJECTS:", len(t.objects))
        print("SPRITES:", len(t.sprites) if hasattr(t,"sprites") else 0)
        print("ACTORS:", len(t.actors) if hasattr(t,"actors") else 0)
        print("STEP:", getattr(t,"step_event",""))
        print("ACTION:", getattr(t,"action_event",""))

        win = tk.Toplevel()
        win.title(f"Delete Tile Content ({gx},{gy})")
        win.geometry("260x420")

        tk.Label(win, text=f"CELL [{gx},{gy}]", font=("Arial",12,"bold")).pack(pady=10)

        # ==========================================
        # DELETE OBJECTS
        # ==========================================
        if t.objects:
            tk.Button(win, text=f"Delete Mesh Objects ({len(t.objects)})",
                    command=lambda:self.delete_meshes_in_tile(gx,gy,win)).pack(fill="x", padx=20, pady=4)

        # ==========================================
        # DELETE SPRITES
        # ==========================================
        if hasattr(t, "sprites") and t.sprites:
            tk.Button(win, text=f"Delete Sprites ({len(t.sprites)})",
                    command=lambda:self.delete_sprites_in_tile(gx,gy,win)).pack(fill="x", padx=20, pady=4)

        # ==========================================
        # DELETE ACTORS
        # ==========================================
        if hasattr(t, "actors") and t.actors:
            tk.Button(win, text=f"Delete Actors ({len(t.actors)})",
                    command=lambda:self.delete_actors_in_tile(gx,gy,win)).pack(fill="x", padx=20, pady=4)

        # ==========================================
        # DELETE EVENTS
        # ==========================================
        if getattr(t, "step_event", ""):
            tk.Button(win, text="Delete Step Event",
                    command=lambda:self.delete_step_event(gx,gy,win)).pack(fill="x", padx=20, pady=4)

        if getattr(t, "action_event", ""):
            tk.Button(win, text="Delete Action Event",
                    command=lambda:self.delete_action_event(gx,gy,win)).pack(fill="x", padx=20, pady=4)

        # ==========================================
        # DELETE FLOOR
        # ==========================================
        if t.floor_tex or abs(t.floor_height) > 0.01:
            tk.Button(win, text="Reset Floor Tile",
                    command=lambda:self.delete_floor_tile(gx,gy,win)).pack(fill="x", padx=20, pady=4)

        # ==========================================
        # DELETE WALLS
        # ==========================================
        if t.wall_n or t.wall_s or t.wall_e or t.wall_w:
            tk.Button(win, text="Delete All Walls",
                    command=lambda:self.delete_walls_tile(gx,gy,win)).pack(fill="x", padx=20, pady=4)
            
        # ==========================================
        # DELETE BLOCK
        # ==========================================
        if t.is_block:
            tk.Button(
                win,
                text="Delete Block",
                command=lambda:self.delete_block_tile(gx,gy,win)
            ).pack(fill="x", padx=20, pady=4)

        # ==========================================
        # FULL NUKE
        # ==========================================
        tk.Button(win, text="FULL TILE CLEAR",
                bg="red", fg="white",
                command=lambda:self.full_clear_tile(gx,gy,win)).pack(fill="x", padx=20, pady=20)
        
    def delete_meshes_in_tile(self, gx, gy, win=None):
        self.grid[gy][gx].objects.clear()
        self.after_delete_refresh(win)

    def delete_block_tile(self, gx, gy, win=None):
        t = self.grid[gy][gx]

        t.is_block = False

        t.block_bottom = 0.0
        t.block_top = 1.0

        t.block_side_tex = None
        t.block_top_tex = None

        t.block_uv_mode = "tile"

        self.after_delete_refresh(win)

    def delete_sprites_in_tile(self, gx, gy, win=None):
        if hasattr(self.grid[gy][gx], "sprites"):
            self.grid[gy][gx].sprites.clear()
        self.after_delete_refresh(win)

    def delete_actors_in_tile(self, gx, gy, win=None):
        if hasattr(self.grid[gy][gx], "actors"):
            self.grid[gy][gx].actors.clear()
        self.after_delete_refresh(win)

    def delete_step_event(self, gx, gy, win=None):
        self.grid[gy][gx].step_event = ""
        self.after_delete_refresh(win)

    def delete_action_event(self, gx, gy, win=None):
        self.grid[gy][gx].action_event = ""
        self.after_delete_refresh(win)

    def delete_floor_tile(self, gx, gy, win=None):
        t = self.grid[gy][gx]
        t.floor_tex = None
        t.floor_height = 0
        self.after_delete_refresh(win)

    def delete_walls_tile(self, gx, gy, win=None):
        t = self.grid[gy][gx]

        t.wall_n = False
        t.wall_s = False
        t.wall_e = False
        t.wall_w = False

        t.wall_ne = False
        t.wall_nw = False
        t.wall_se = False
        t.wall_sw = False

        t.wall_segments = {"n":[],"s":[],"e":[],"w":[]}

        self.after_delete_refresh(win)

    def full_clear_tile(self, gx, gy, win=None):
        t = self.grid[gy][gx]

        t.objects.clear()

        if hasattr(t, "sprites"):
            t.sprites.clear()

        if hasattr(t, "actors"):
            t.actors.clear()

        t.step_event = ""
        t.action_event = ""

        t.floor_tex = None
        t.floor_height = 0

        t.wall_n = t.wall_s = t.wall_e = t.wall_w = False
        t.wall_ne = t.wall_nw = t.wall_se = t.wall_sw = False
        t.wall_segments = {"n":[],"s":[],"e":[],"w":[]}

        # RESET BLOCK
        t.is_block = False

        t.block_bottom = 0.0
        t.block_top = 1.0

        t.block_side_tex = None
        t.block_top_tex = None

        t.block_uv_mode = "tile"

        self.after_delete_refresh(win)

    def after_delete_refresh(self, win=None):
        if win:
            win.destroy()

        self.selected_instance = {"inst":None}
        self.selected_sprite = None
        self.selected_actor_gx = None
        self.selected_actor_gy = None

        self.draw_grid()

        if hasattr(self, "viewport"):
            self.viewport.redraw()

    def draw_grid(self):
        self.grid_canvas.delete('all')
        for y in range(GRID_H):
            for x in range(GRID_W):
                px=x*CELL_PIXELS
                py=y*CELL_PIXELS
                t=self.grid[y][x]
                base = 60 + int((t.floor_height + 2) * 25)
                base = max(30, min(180, base))

                if t.floor_tex:
                    c = f'#{base:02x}{base:02x}{base:02x}'
                else:
                    c = f'#{base//2:02x}{base//2:02x}{base//2:02x}'
                self.grid_canvas.create_rectangle(px,py,px+CELL_PIXELS,py+CELL_PIXELS,fill=c,outline='#202020')

                if t.objects:
                    self.grid_canvas.create_oval(
                        px+10, py+10,
                        px+CELL_PIXELS-10, py+CELL_PIXELS-10,
                        outline='cyan',
                        width=2
                    )

                    if self.selected_instance and self.selected_instance.get("inst") and self.selected_instance["inst"] in t.objects:
                        self.grid_canvas.create_rectangle(
                            px+4, py+4,
                            px+CELL_PIXELS-4, py+CELL_PIXELS-4,
                            outline='yellow',
                            width=3
                        )

                    self.grid_canvas.create_text(
                        px+CELL_PIXELS//2,
                        py+CELL_PIXELS//2,
                        text=str(len(t.objects)),
                        fill='cyan',
                        font=('Arial',8,'bold')
                    )

                if hasattr(t, "sprites") and t.sprites:
                    self.grid_canvas.create_oval(
                        px+22, py+22,
                        px+CELL_PIXELS-22, py+CELL_PIXELS-22,
                        outline='magenta',
                        width=2
                    )

                    self.grid_canvas.create_text(
                        px+CELL_PIXELS//2,
                        py+CELL_PIXELS//2 + 10,
                        text="S"+str(len(t.sprites)),
                        fill='magenta',
                        font=('Arial',8,'bold')
                    )

                    if self.selected_sprite in t.sprites:
                        self.grid_canvas.create_rectangle(
                            px+7, py+7,
                            px+CELL_PIXELS-7, py+CELL_PIXELS-7,
                            outline='lime',
                            width=3
                        )
                if abs(t.floor_height) > 0.01:
                    self.grid_canvas.create_text(
                        px + CELL_PIXELS//2,
                        py + CELL_PIXELS//2,
                        text=str(round(t.floor_height,1)),
                        fill='white',
                        font=('Arial',7)
                )
                    
                if hasattr(t, "actors") and t.actors:

                    first_pack = t.actors[0]
                    inst = first_pack["inst"]

                    acol = "lime"
                    letter = "N"

                    if inst.actor_name in self.actors:
                        ad = self.actors[inst.actor_name]

                        if ad.kind == "main":
                            acol = "green"
                            letter = "P"
                        elif ad.kind == "enemy":
                            acol = "red"
                            letter = "E"
                        elif ad.kind == "party":
                            acol = "cyan"
                            letter = "M"
                        else:
                            acol = "lime"
                            letter = "N"

                    self.grid_canvas.create_rectangle(
                        px+6, py+6,
                        px+CELL_PIXELS-6, py+CELL_PIXELS-6,
                        outline=acol,
                        width=2
                    )

                    self.grid_canvas.create_text(
                        px+CELL_PIXELS//2,
                        py+CELL_PIXELS//2 + 10,
                        text=letter + str(len(t.actors)),
                        fill=acol,
                        font=('Arial',8,'bold')
                    )

                if hasattr(self, "selected_actor_gx") and self.selected_actor_gx == x and self.selected_actor_gy == y:
                    self.grid_canvas.create_rectangle(
                        px+2, py+2,
                        px+CELL_PIXELS-2, py+CELL_PIXELS-2,
                        outline='white',
                        width=3       
                    )

                if getattr(t, "event_data", {}).get("enabled", False):

                    trig = t.event_data.get("trigger", "step")

                    if trig == "step":
                        self.grid_canvas.create_rectangle(
                            px+12, py+12,
                            px+CELL_PIXELS-12, py+CELL_PIXELS-12,
                            fill='yellow',
                            stipple='gray50',
                            outline=''
                        )

                        self.grid_canvas.create_text(
                            px+CELL_PIXELS//2,
                            py+CELL_PIXELS//2 - 10,
                            text="ST",
                            fill='black',
                            font=('Arial',7,'bold')
                        )

                    elif trig == "action":
                        self.grid_canvas.create_rectangle(
                            px+16, py+16,
                            px+CELL_PIXELS-16, py+CELL_PIXELS-16,
                            fill='orange',
                            stipple='gray50',
                            outline=''
                        )

                        self.grid_canvas.create_text(
                            px+CELL_PIXELS//2,
                            py+CELL_PIXELS//2 - 10,
                            text="AC",
                            fill='black',
                            font=('Arial',7,'bold')
                        )

                    elif trig == "autorun":
                        self.grid_canvas.create_rectangle(
                            px+10, py+10,
                            px+CELL_PIXELS-10, py+CELL_PIXELS-10,
                            fill='red',
                            stipple='gray50',
                            outline=''
                        )

                        self.grid_canvas.create_text(
                            px+CELL_PIXELS//2,
                            py+CELL_PIXELS//2 - 10,
                            text="AU",
                            fill='white',
                            font=('Arial',7,'bold')
                        )

                if t.wall_n:self.grid_canvas.create_line(px,py,px+CELL_PIXELS,py,fill='red',width=2)
                if t.wall_s:self.grid_canvas.create_line(px,py+CELL_PIXELS,px+CELL_PIXELS,py+CELL_PIXELS,fill='red',width=2)
                if t.wall_e:self.grid_canvas.create_line(px+CELL_PIXELS,py,px+CELL_PIXELS,py+CELL_PIXELS,fill='red',width=2)
                if t.wall_w:self.grid_canvas.create_line(px,py,px,py+CELL_PIXELS,fill='red',width=2)
                if getattr(t, "wall_ne", False):
                    self.grid_canvas.create_line(
                        px, py,
                        px+CELL_PIXELS, py+CELL_PIXELS,
                        fill='orange', width=2
                    )

                if getattr(t, "wall_nw", False):
                    self.grid_canvas.create_line(
                        px+CELL_PIXELS, py,
                        px, py+CELL_PIXELS,
                        fill='orange', width=2
                    )

                if getattr(t, "wall_se", False):
                    self.grid_canvas.create_line(
                        px+CELL_PIXELS, py,
                        px, py+CELL_PIXELS,
                        fill='yellow', width=2
                    )

                if getattr(t, "wall_sw", False):
                    self.grid_canvas.create_line(
                        px, py,
                        px+CELL_PIXELS, py+CELL_PIXELS,
                        fill='yellow', width=2
                    )

                if getattr(t, "is_block", False):
                    self.grid_canvas.create_rectangle(
                        px+6, py+6,
                        px+CELL_PIXELS-6, py+CELL_PIXELS-6,
                        outline='#00ffff',
                        width=2
                    )

                    self.grid_canvas.create_text(
                        px + CELL_PIXELS//2,
                        py + CELL_PIXELS//2,
                        text='B' + str(round(t.block_top - t.block_bottom,1)),
                        fill='#00ffff',
                        font=('Arial',8,'bold')
                    )

                # =====================================
                # DRAG SELECTION PREVIEW
                # =====================================

                if self.drag_painting and self.drag_start and self.drag_end:

                    x1 = min(self.drag_start[0], self.drag_end[0])
                    y1 = min(self.drag_start[1], self.drag_end[1])

                    x2 = max(self.drag_start[0], self.drag_end[0])
                    y2 = max(self.drag_start[1], self.drag_end[1])

                    px1 = x1 * CELL_PIXELS
                    py1 = y1 * CELL_PIXELS

                    px2 = (x2 + 1) * CELL_PIXELS
                    py2 = (y2 + 1) * CELL_PIXELS

                    self.grid_canvas.create_rectangle(
                        px1,
                        py1,
                        px2,
                        py2,
                        outline="yellow",
                        width=3,
                        dash=(4, 2)
                    )
                    

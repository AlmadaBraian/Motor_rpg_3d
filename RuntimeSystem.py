import copy
import time
import tkinter as tk

from CameraAnimator import CameraAnimator
from OpglManager import GLViewport

from EventManager import (
    check_runtime_autorun_events,
    execute_runtime_tile_event,
    get_near_event_cell,
    get_near_interactive_actor,
    runtime_position_blocked,
    start_world_event
)

from RuntimeWorld import RuntimeWorld
from SceneManager import get_runtime_scene_manager

from SpriteManager import Animator
from config import GRID_H, GRID_W, SCREEN_H, SCREEN_W
from VisualNovelScene import VisualNovelSceneState, has_visual_novel_layer


class RuntimeSystem:

    def __init__(self, toolkit):

        self.toolkit = toolkit

    # =====================================================
    # OPEN GAME
    # =====================================================

    def open_game_runtime(self):

        tkref = self.toolkit

        if tkref.play_mode:
            return

        tkref.runtime_cam_orbit = 0

        tkref.screen_fade_alpha = 1

        tkref.runtime_last_event_tile = None
        tkref.runtime_event_cooldown = 0
        tkref._last_step_audio_tile = None
        tkref._last_step_audio_time = 0.0

        tkref.play_mode = True
        tkref.viewport.preview_paused = True

        tkref.game_over = False

        tkref.runtime_event_cooldown = 0.0
        tkref.world_event_running = False
        tkref.dialog_visible = False
        tkref.event_wait_input = False
        tkref.dialog_pages = []
        tkref.dialog_index = 0
        tkref.show_ui = True

        if not hasattr(tkref, "visual_novel_scene"):
            tkref.visual_novel_scene = VisualNovelSceneState()
        else:
            tkref.visual_novel_scene.reset()
        tkref.event_wait_vn_animation = False

        if hasattr(tkref, "ensure_project_maps"):
            tkref.ensure_project_maps()

        initial_scene_file = getattr(
            tkref,
            "initial_scene_file",
            "scenes/visual_novel_example.json"
        )

        scene_manager = get_runtime_scene_manager(tkref)
        initial_scene_data, initial_scene_path = scene_manager.load_scene_data(
            initial_scene_file
        )
        initial_map_id = scene_manager.get_scene_start_map(initial_scene_data)
        initial_is_vn = scene_manager.is_visual_novel_scene(initial_scene_data)

        if initial_scene_data is None:
            initial_scene_path = ""

        tkref.current_runtime_map_id = initial_map_id
        tkref.runtime_initial_scene_file = initial_scene_file
        tkref.runtime_initial_scene_path = initial_scene_path
        tkref.runtime_initial_scene_data = initial_scene_data or {}
        tkref.runtime_scene_mode = "visual_novel" if initial_is_vn else "world"

        if initial_is_vn:
            tkref.visual_novel_scene.load_from_scene_data(initial_scene_data or {})
            tkref.runtime_world = None
            tkref.show_ui = False
        else:
            if has_visual_novel_layer(initial_scene_data):
                tkref.visual_novel_scene.load_from_scene_data(initial_scene_data or {})

            if not initial_map_id:
                initial_map_id = getattr(tkref, "current_map_id", "Map001")

            if not hasattr(tkref, "maps") or initial_map_id not in tkref.maps:
                print("INITIAL MAP NOT FOUND, USING EDITOR MAP:", initial_map_id)
                initial_map_id = getattr(tkref, "current_map_id", "Map001")

            tkref.current_runtime_map_id = initial_map_id
            tkref.runtime_world = self.build_runtime_world_copy(tkref.current_runtime_map_id)

            player_start = scene_manager.get_scene_player_start(initial_scene_data)
            if player_start:
                self.apply_runtime_player_start(player_start)

        # ==========================================
        # WINDOW
        # ==========================================

        tkref.game_win = tk.Toplevel()
        tkref.game_win.title("GAME RUNTIME")

        # ==========================================
        # HUD
        # ==========================================

        tkref.runtime_hint_label = tk.Label(
            tkref.game_win,
            text="",
            font=("Arial",14,"bold"),
            bg="black",
            fg="white"
        )

        tkref.runtime_hint_label.place(x=20,y=20)

        tkref.runtime_dialog_label = tk.Label(
            tkref.game_win,
            text="",
            font=("Arial",14),
            bg="navy",
            fg="white",
            wraplength=550,
            justify="left"
        )

        tkref.runtime_dialog_label.place(x=20,y=420)

        #tkref.update_battle_unit_facings()

        # ==========================================
        # VIEWPORT
        # ==========================================

        world_cam = tkref.camera_presets["world"]

        tkref.runtime_cam_target_pitch = world_cam["pitch"]
        tkref.runtime_cam_target_distance = world_cam["distance"]
        tkref.runtime_cam_target_height = world_cam["y"]
        tkref.runtime_cam_orbit = world_cam["yaw"]

        tkref.game_view = GLViewport(
            tkref.game_win,
            toolkit=tkref,
            width=SCREEN_W,
            height=SCREEN_H
        )

        tkref.game_view.pack(fill='both', expand=True)

        tkref.game_view.toolkit_ref = tkref
        tkref.game_view.master_toolkit = tkref

        tkref.game_win.bind("<KeyPress>", self.game_key_down)
        tkref.game_win.bind("<KeyRelease>", self.game_key_up)

        tkref.game_win.protocol(
            "WM_DELETE_WINDOW",
            self.close_game_runtime
        )

        tkref.game_win.after(
            250,
            self.finish_game_runtime_setup
        )

    # =====================================================
    # FINISH SETUP
    # =====================================================

    def finish_game_runtime_setup(self):

        tkref = self.toolkit

        tkref.game_view.editor_camera = copy.deepcopy(
            tkref.viewport.editor_camera
        )

        tkref.game_view.game_camera = copy.deepcopy(
            tkref.viewport.game_camera
        )

        tkref.game_view.camera = tkref.game_view.game_camera
        tkref.game_view.active_camera_mode = "game"

        tkref.game_view.game_cam_anim = CameraAnimator(
            tkref.game_view.game_camera
        )

        tkref.game_view.last_anim_time = time.time()

        tkref.game_view.bind(
            "<KeyPress>",
            self.game_key_down
        )

        tkref.game_view.bind(
            "<KeyRelease>",
            self.game_key_up
        )

        tkref.game_win.after(
            100,
            lambda: tkref.game_view.focus_set()
        )

        initial_scene_path = getattr(tkref, "runtime_initial_scene_path", "")

        if initial_scene_path:
            start_world_event(tkref, initial_scene_path)
        else:
            check_runtime_autorun_events(tkref)

    # =====================================================
    # PLAYER START
    # =====================================================

    def apply_runtime_player_start(self, player_start):

        tkref = self.toolkit

        if not tkref.runtime_world:
            return

        pack = tkref.runtime_world.main_actor

        if not pack:
            return

        x = int(player_start.get("x", player_start.get("gx", pack["gx"])))
        y = int(player_start.get("y", player_start.get("gy", pack["gy"])))

        if x < 0 or y < 0 or x >= GRID_W or y >= GRID_H:
            print("INVALID INITIAL PLAYER START:", x, y)
            return

        old_tile = tkref.runtime_world.grid[pack["gy"]][pack["gx"]]

        if pack in old_tile.actors:
            old_tile.actors.remove(pack)

        pack["gx"] = x
        pack["gy"] = y
        pack["inst"].offx = 0
        pack["inst"].offy = 0

        facing = player_start.get("facing", "")

        if facing:
            pack["inst"].facing = facing

        new_tile = tkref.runtime_world.grid[y][x]

        if pack not in new_tile.actors:
            new_tile.actors.append(pack)

        print("INITIAL PLAYER START:", x, y)

    # =====================================================
    # BUILD RUNTIME COPY
    # =====================================================

    def build_runtime_world_copy(self, map_id=None):

        tkref = self.toolkit

        rw = RuntimeWorld()
        source_grid = tkref.grid

        if map_id and hasattr(tkref, "maps") and map_id in tkref.maps:
            source_grid = tkref.maps[map_id]
            rw.map_id = map_id
        else:
            rw.map_id = getattr(tkref, "current_map_id", "Map001")

        rw.assets = tkref.assets
        rw.sprites = tkref.sprites
        rw.actors = tkref.actors
        rw.texture_manager = tkref.texture_manager
        rw.grid = []
        rw.main_actor = None

        # ==========================================
        # COPIA BASE GRID + SPRITES + ACTORS
        # ==========================================
        for y in range(GRID_H):
            row = []

            for x in range(GRID_W):
                src = source_grid[y][x]
                t = copy.deepcopy(src)
                t.gx = x
                t.gy = y

                # ----------------------------
                # reiniciar animadores sprites
                # ----------------------------
                if hasattr(t, "sprites"):
                    for spr in t.sprites:
                        if spr.asset in rw.sprites:
                            asset = rw.sprites[spr.asset]

                            spr.animator = Animator(asset.base_clips)

                            if asset.base_clips:
                                spr.animator.play(asset.base_clips[0].name)

                # ----------------------------
                # reconstruir actors como packs runtime actor_runtime
                # ----------------------------
                new_actor_list = []

                if hasattr(src, "actors"):
                    new_actor_list = []

                    for pack in src.actors:
                        inst = pack["inst"]

                        if inst.actor_name not in tkref.actors:
                            continue

                        actor_asset = tkref.actors[inst.actor_name]

                        inst.is_mantling = False
                        inst.mantle_timer = 0.0
                        inst.mantle_total = 0.8

                        inst.mantle_start_x = 0
                        inst.mantle_start_y = 0
                        inst.mantle_end_x = 0
                        inst.mantle_end_y = 0

                        inst.mantle_start_z = 0
                        inst.mantle_end_z = 0

                        inst.saved_cam_yaw = None

                        inst.mantle_dir_x = 0
                        inst.mantle_dir_y = 0
                        inst.mantle_phase = 0
                        inst.was_on_ground = True

                        new_inst = copy.deepcopy(inst)

                        # =====================================
                        # reconstruir animator runtime
                        # =====================================
                        if actor_asset.sprite_sheets:
                            sprname = actor_asset.sprite_sheets[0]

                            if sprname in tkref.sprites:
                                sprite_asset = tkref.sprites[sprname]

                                new_inst.animator = Animator(tkref.clone_clips(sprite_asset.base_clips))

                                if sprite_asset.base_clips:
                                    new_inst.animator.play(sprite_asset.base_clips[0].name)

                        new_pack = {
                            "inst": new_inst,
                            "gx": pack["gx"],
                            "gy": pack["gy"]
                        }

                        new_actor_list.append(new_pack)

                        # detectar main actor runtime
                        if actor_asset.is_main:
                            rw.main_actor = new_pack
                            
                            print("MAIN ACTOR FOUND:", new_inst.actor_name)

                    t.actors = new_actor_list

                row.append(t)

            rw.grid.append(row)
        return rw

    # =====================================================
    # INPUT
    # =====================================================

    def advance_runtime_dialog(self):

        tkref = self.toolkit

        if not tkref.dialog_pages or tkref.dialog_index >= len(tkref.dialog_pages):
            tkref.dialog_visible = False
            tkref.event_wait_input = False
            tkref.dialog_index = 0
            return

        page = tkref.dialog_pages[tkref.dialog_index]

        if tkref.dialog_visible_chars < len(page):
            tkref.dialog_visible_chars = len(page)
            return

        print("SPACE DIALOG")
        print("INDEX:", tkref.dialog_index)
        print("LEN:", len(tkref.dialog_pages))

        if tkref.dialog_index < len(tkref.dialog_pages) - 1:
            tkref.dialog_index += 1
            tkref.dialog_visible_chars = 0
            tkref.dialog_char_timer = 0
            print("NEXT PAGE:", tkref.dialog_index)
            return

        print("END DIALOG")
        tkref.dialog_visible = False
        tkref.event_wait_input = False
        tkref.dialog_index = 0

    def game_key_down(self, event):

        tkref = self.toolkit

        k = event.keysym.lower()

        # =====================================
        # RUNTIME MENU
        # =====================================

        menu = tkref.runtime_menu

        if menu.visible:

            self.handle_runtime_menu_input(event)

        if event.keysym == "space":

            # evitar autorepeat
            if tkref.space_pressed:
                return

            tkref.space_pressed = True

            if tkref.world_event_running and tkref.event_wait_input:
                if tkref.dialog_visible:
                    self.advance_runtime_dialog()
                else:
                    #tkref.dialog_visible = False
                    tkref.event_wait_input = False
                    #tkref.dialog_index = 0
                return
            if tkref.world_event_running:
                tkref.show_ui = False
                return
            else:
                tkref.show_ui = True

            if tkref.runtime_event_cooldown > 0:
                return

            # NPC interactivo
            near_npc = get_near_interactive_actor(tkref)
            if near_npc:
                if near_npc.event_file:
                    start_world_event(tkref,near_npc.event_file)
                    tkref.runtime_event_cooldown = 0.40
                    return

            # EVENT TILE ACTION
            near_evt = get_near_event_cell(tkref)
            if near_evt:
                execute_runtime_tile_event(tkref, near_evt)
                return

        # =====================================
        # WAIT INPUT EVENT
        # =====================================

        if not tkref.runtime_world or not tkref.runtime_world.main_actor:
            return
        
        if tkref.battle_mode:
            tkref.runtime_combat.handle_battle_input(event)
            return
        

        p = tkref.runtime_world.main_actor["inst"]

        if not tkref.world_event_running:

            if k == "w":
                p.move_b = True
            if k == "s":
                p.move_f = True
            if k == "a":
                p.move_l = True
            if k == "d":
                p.move_r = True

            if k == "q":
                p.rot_l = True
            if k == "e":
                p.rot_r = True

    def game_key_up(self, event):

        tkref = self.toolkit

        k = event.keysym.lower()

        if event.keysym == "space":
            tkref.space_pressed = False

        if k in ("w", "s", "up", "down"):
            tkref.menu_down_pressed = False

        if not tkref.runtime_world or not tkref.runtime_world.main_actor:
            return
        
        if tkref.battle_mode:
            tkref.runtime_combat.game_key_up(event)
            return

        p = tkref.runtime_world.main_actor["inst"]

        

        movement_released = False

        if k == "w":
            p.move_b = False
            movement_released = True
        if k == "s":
            p.move_f = False
            movement_released = True
        if k == "a":
            p.move_l = False
            movement_released = True
        if k == "d":
            p.move_r = False
            movement_released = True

        if (
            movement_released
            and not p.move_f
            and not p.move_b
            and not p.move_l
            and not p.move_r
            and hasattr(tkref, "play_runtime_actor_idle")
        ):
            tkref.play_runtime_actor_idle(p)

        if k == "q":
            p.rot_l = False
        if k == "e":
            p.rot_r = False
        
        if event.keysym == "space":
            tkref.space_pressed = False

    def open_runtime_menu(
        self,
        items,
        title="",
        x=100,
        y=100,
        w=8
    ):
        
        print("OPEN_RUNTIME_MENU CALLED")
        tkref = self.toolkit

        menu = tkref.runtime_menu

        print("OPEN MENU:", title, items)

        menu.visible = True
        menu.title = title

        menu.items = items
        menu.index = 0

        menu.x = x
        menu.y = y

        menu.w = w

    def handle_runtime_menu_input(self, event):

        menu = self.toolkit.runtime_menu

        if not menu.visible:
            return

        k = event.keysym.lower()

        if not hasattr(self.toolkit, "menu_down_pressed"):
            self.toolkit.menu_down_pressed = False

        if k in ("up","w"):
            
            if self.toolkit.menu_down_pressed:
                return

            self.toolkit.menu_down_pressed = True

            menu.index -= 1
            menu.index %= len(menu.items)

            return

        elif k in ("down","s"):
            if self.toolkit.menu_down_pressed:
                return

            self.toolkit.menu_down_pressed = True

            menu.index += 1
            menu.index %= len(menu.items)

            return
        
        elif k == "space":

            if menu.on_select:

                menu.on_select(
                    menu.items[menu.index]
                )

        elif k in ("escape","b"):

            if menu.on_cancel:
                menu.on_cancel()


        menu.index %= len(menu.items)

    def main_menu_selected(option):

        if option == "Nuevo Juego":
            print("nuevo juego")
            #start_game()

        elif option == "Cargar Partida":
            print("cargar juego")
            #load_game()

        elif option == "Opciones":
            print("menu opciones")
            #open_options()

        elif option == "Salir":
            print("salir")
            #root.destroy()

    # =====================================================
    # UPDATE
    # =====================================================

    def update_runtime_world(self, dt):

        tkref = self.toolkit

        if not tkref.runtime_world:
            return

        p = tkref.runtime_world.main_actor

        dx = 0
        dz = 0

        if p.move_f: dz -= p.speed * dt
        if p.move_b: dz += p.speed * dt
        if p.move_l: dx -= p.speed * dt
        if p.move_r: dx += p.speed * dt

        nx = p.x + dx
        nz = p.z + dz

        if not runtime_position_blocked(tkref, nx, p.z):
            p.x = nx

        if not runtime_position_blocked(tkref, p.x, nz):
            p.z = nz

        if hasattr(tkref, "game_view"):

            cam = tkref.game_view.game_camera

            # =====================================
            # NO seguir player en combate
            # =====================================
            if tkref.battle_mode == False:

                preset = tkref.camera_presets["world"]

                cam.y = preset["y"]
                cam.yaw = preset["yaw"]
                cam.pitch = preset["pitch"]
                cam.distance = preset["distance"]

        if tkref.camera_preview_dirty:
            tkref.preview_camera_preset()
            tkref.camera_preview_dirty = False


        print(
            "RUNTIME CAMERA",
            cam.yaw,
            cam.pitch,
            cam.distance
        )

        if tkref.dialog_visible:

            page = tkref.dialog_pages[tkref.dialog_index]
            if hasattr(tkref, "dialog_continue_actor"):
                tkref.dialog_continue_actor.animator.update(dt)

            if tkref.dialog_visible_chars < len(page):

                tkref.dialog_char_timer += dt

                while tkref.dialog_char_timer >= tkref.dialog_char_speed:

                    tkref.dialog_char_timer -= tkref.dialog_char_speed
                    tkref.dialog_visible_chars += 1

                    if tkref.dialog_visible_chars >= len(page):
                        tkref.dialog_visible_chars = len(page)
                        break

    # =====================================================
    # CLOSE
    # =====================================================

    def close_game_runtime(self):

        tkref = self.toolkit

        tkref.play_mode = False
        tkref.battle_mode = False
        tkref.show_ui = False

        tkref.game_over = False

        tkref.runtime_world = None
        if hasattr(tkref, "visual_novel_scene"):
            tkref.visual_novel_scene.reset()
        tkref.runtime_scene_mode = "world"
        tkref.event_wait_vn_animation = False

        tkref.viewport.preview_paused = False

        tkref.runtime_event_cooldown = 0.0

        # =====================================
        # FLAGS GENERALES
        # =====================================
        tkref.play_mode = False
        tkref.battle_mode = False

        tkref.world_event_running = False
        tkref.world_event_locked = False

        tkref.dialog_visible = False
        tkref.event_wait_input = False

        # =====================================
        # RUNTIME
        # =====================================
        if hasattr(tkref, "audio_manager"):
            tkref.audio_manager.stop()

        tkref.runtime_world = None

        tkref.runtime_event_cooldown = 0
        tkref.runtime_last_event_tile = None

        tkref.runtime_mantle = False
        tkref.runtime_climb_action = False

        # =====================================
        # COMBATE
        # =====================================
        tkref.battle_units = []

        tkref.battle_turn_order = []
        tkref.battle_turn_index = 0

        tkref.battle_current_unit = None
        tkref.battle_selected_unit = None

        tkref.battle_move_tiles = []
        tkref.combat_move_tiles = []
        tkref.battle_target_tiles = []

        tkref.combat_path = []

        tkref.combat_actor_moving = False
        tkref.combat_move_queue = []
        tkref.combat_moving_unit = None

        tkref.battle_state = "idle"

        tkref.battle_cam_target_x = 0
        tkref.battle_cam_target_z = 0
        tkref.battle_cam_active = False

        tkref.button_A_command = "Interactuar"
        tkref.button_X_command = ""
        tkref.button_Y_command = ""
        tkref.button_B_command = "Cancelar"

        # =====================================
        # INPUTS
        # =====================================
        tkref.battle_input_cooldown = 0

        # =====================================
        # CAMARAS
        # =====================================
        tkref.runtime_camera_locked = False
        tkref.runtime_cam_orbit = 0

        # =====================================
        # VIEWPORT EDITOR
        # =====================================
        tkref.viewport.preview_paused = False


        if tkref.game_win:
            tkref.game_win.destroy()
            tkref.game_win = None
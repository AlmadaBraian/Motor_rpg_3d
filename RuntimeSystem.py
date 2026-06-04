import copy
import time
import tkinter as tk

from CameraAnimator import CameraAnimator
from OpglManager import GLViewport

from EventManager import (
    execute_runtime_tile_event,
    get_near_event_cell,
    get_near_interactive_actor,
    runtime_position_blocked,
    start_world_event
)

from RuntimeWorld import RuntimeWorld

from SpriteManager import Animator
from config import CAMERA_PRESETS, GRID_H, GRID_W, SCREEN_H, SCREEN_W


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

        tkref.runtime_last_event_tile = None
        tkref.runtime_event_cooldown = 0

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

        tkref.current_runtime_map_id = getattr(tkref, "current_map_id", "Map001")
        tkref.runtime_world = self.build_runtime_world_copy(tkref.current_runtime_map_id)

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

        tkref.game_view = GLViewport(
            tkref.game_win,
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

    def game_key_down(self, event):

        tkref = self.toolkit

        if not tkref.runtime_world:
            return

        if not tkref.runtime_world.main_actor:
            return
        
        if tkref.battle_mode:
            tkref.runtime_combat.handle_battle_input(event)
            return

        p = tkref.runtime_world.main_actor["inst"]

        k = event.keysym.lower()

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

        if event.keysym == "space":

            # evitar autorepeat
            if tkref.space_pressed:
                return

            tkref.space_pressed = True

            if tkref.world_event_running and tkref.event_wait_input:

                page = tkref.dialog_pages[tkref.dialog_index]

                if tkref.dialog_visible_chars < len(page):

                    tkref.dialog_visible_chars = len(page)

                else:

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

    def game_key_up(self, event):

        tkref = self.toolkit

        if not tkref.runtime_world:
            return

        if not tkref.runtime_world.main_actor:
            return
        
        if tkref.battle_mode:
            tkref.runtime_combat.game_key_up(event)
            return

        p = tkref.runtime_world.main_actor["inst"]

        k = event.keysym.lower()

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

                preset = CAMERA_PRESETS["world"]

                cam.y = preset["y"]
                cam.yaw = preset["yaw"]
                cam.pitch = preset["pitch"]
                cam.distance = preset["distance"]

        if tkref.camera_preview_dirty:
            tkref.preview_camera_preset()
            tkref.camera_preview_dirty = False

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
        tkref.button_X_command = "Guardia"
        tkref.button_Y_command = "Items"
        tkref.button_B_command = "Especial"

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
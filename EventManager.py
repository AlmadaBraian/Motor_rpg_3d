import math
import os
from SceneManager import get_runtime_scene_manager
from SceneManager import resolve_runtime_scene_path as central_resolve_runtime_scene_path
from ActorInstance import ActorInstance
from CameraAnimator import CameraAnimator
from CameraKeyframe import CameraKeyframe
from RuntimeCombat import RuntimeCombat
from RuntimeMusic import play_runtime_audio, stop_runtime_audio
from SpriteManager import Animator
from config import *


def resolve_runtime_scene_path(scene_file):
        return central_resolve_runtime_scene_path(scene_file)


def start_world_event(self, jsonfile):
        manager = get_runtime_scene_manager(self)
        manager.start_world_event(self, jsonfile)

def start_world_script(
    self,
    script
):

    manager = get_runtime_scene_manager(self)
    manager.start_world_script(self, script)

def update_world_event(self, dt):
        if not self.world_event_running:
            return
        
        if self.event_wait_move:
            return

        self.space_icon_blink += dt

        # wait timer
        if self.event_wait_timer > 0:
            self.event_wait_timer -= dt
            return

        # wait input dialog
        if self.event_wait_input:
            return
        
        # evitar avanzar script el mismo frame
        if self.event_advance_block:
            self.event_advance_block = False
            return

        if self.current_event_index >= len(self.current_event_script):
            end_world_event(self)
            return
        
        if self.event_wait_camera:
            return
        
        if self.event_wait_fade:
            return

        cmd = self.current_event_script[self.current_event_index]
        self.current_event_index += 1

        print("RUN CMD:", cmd)

        run_world_event_command(self,cmd)

def end_world_event(self):
        self.world_event_running = False
        self.world_event_locked = False

        self.current_event_data = None
        self.current_event_script = []
        self.current_event_index = 0

        self.dialog_visible = False
        self.event_wait_input = False
        self.event_wait_timer = 0
        self.event_wait_move = None

        if self.pending_combat_enemy:
            enemy = self.pending_combat_enemy
            self.pending_combat_enemy = False

            self.runtime_combat.start_runtime_combat()

        print("WORLD EVENT END")

def run_world_event_command(self, cmd):
        action = cmd.get("action", "")

        # ==========================
        # WAIT
        # ==========================
        if action == "wait":
            self.event_wait_timer = cmd.get("time", 1000) / 1000.0
            return
        
        if action == "play_animation":

            clip = cmd.get("animation_clip", "")
            actor_name = cmd.get("actor_name", "")

            inst = self.find_actor_by_name(actor_name)

            if not inst:
                print("ACTOR NO ENCONTRADO:", actor_name)
                return

            if not inst.animator:
                print("SIN ANIMATOR")
                return

            if clip not in inst.animator.clips:
                print("CLIP NO EXISTE:", clip)
                return

            inst.scripted_animation = True

            inst.animator.play(clip)

            print("PLAYING:", clip)

            return
        if action == "audio_play":
            play_runtime_audio(self, cmd, source="world")
            return

        if action == "audio_pause":
            if hasattr(self, "audio_manager"):
                self.audio_manager.pause(cmd.get("track", cmd.get("track_id")))
            return

        if action in ("audio_resume", "audio_unpause"):
            if hasattr(self, "audio_manager"):
                self.audio_manager.resume(cmd.get("track", cmd.get("track_id")))
            return

        if action == "audio_stop":
            stop_runtime_audio(self, cmd)
            return

        if action == "audio_set_volume":
            if hasattr(self, "audio_manager"):
                self.audio_manager.set_volume(
                    cmd.get("track", cmd.get("track_id", "master")),
                    cmd.get("volume", 1.0)
                )
            return

        if action == "audio_change_volume":
            if hasattr(self, "audio_manager"):
                self.audio_manager.change_volume(
                    cmd.get("track", cmd.get("track_id", "master")),
                    cmd.get("delta", 0.0)
                )
            return

        if action == "audio_fade_volume":
            if hasattr(self, "audio_manager"):
                self.audio_manager.fade_volume(
                    cmd.get("track", cmd.get("track_id", "master")),
                    cmd.get("volume", cmd.get("target_volume", 0.0)),
                    duration=cmd.get("duration", 1.0),
                    stop_on_finish=cmd.get("stop", False)
                )
            return

        if action == "set_floor_audio":
            if hasattr(self, "set_floor_audio_link"):
                self.set_floor_audio_link(
                    cmd.get("texture", cmd.get("floor_tex", "")),
                    cmd.get("sound", ""),
                    volume=cmd.get("volume", 0.8),
                    cooldown=cmd.get("cooldown", 0.25)
                )
            return

        if action == "camera_follow_player":

            self.runtime_camera_locked = False

            return
        
        if action == "camera_look_actor":


            actor_name = cmd.get("actor", "")

            pack = self.find_actor_pack_by_name(actor_name)

            if not pack:
                return

            camx = pack["gx"]
            camz = pack["gy"]

            if not hasattr(self.game_view, "game_cam_anim"):

                self.game_view.game_cam_anim = CameraAnimator(
                    self.game_view.game_camera
                )

            anim = self.game_view.game_cam_anim

            cam = self.game_view.game_camera

            anim = self.game_view.game_cam_anim

            anim.clear()

            cam = self.game_view.game_camera

            anim.add_key(
                CameraKeyframe(
                    cam.x,
                    cam.y,
                    cam.z,
                    cam.yaw,
                    cam.pitch,
                    cam.distance,
                    0
                )
            )

            anim.add_key(
                CameraKeyframe(
                    camx,
                    cmd.get("height", 1.0),
                    camz,
                    cmd.get("yaw", 180),
                    cmd.get("pitch", 25),
                    cmd.get("distance", 5),
                    cmd.get("duration", 2.0)
                )
            )

            self.runtime_camera_locked = True

            anim.play()

            self.event_wait_camera = True

            return
        
        if action == "camera_move":
            

            if not hasattr(self.game_view, "game_cam_anim"):

                self.game_view.game_cam_anim = CameraAnimator(
                    self.game_view.game_camera
                )

            anim = self.game_view.game_cam_anim

            cam = self.game_view.game_camera

            anim = self.game_view.game_cam_anim

            anim.clear()

            # key actual
            cam = self.game_view.game_camera

            anim.add_key(
                CameraKeyframe(
                    cam.x,
                    cam.y,
                    cam.z,
                    cam.yaw,
                    cam.pitch,
                    cam.distance,
                    0
                )
            )

            # key destino
            anim.add_key(
                CameraKeyframe(
                    cmd.get("x", cam.x),
                    cmd.get("y", cam.y),
                    cmd.get("z", cam.z),
                    cmd.get("yaw", cam.yaw),
                    cmd.get("pitch", cam.pitch),
                    cmd.get("distance", cam.distance),
                    cmd.get("duration", 2.0)
                )
            )
            self.runtime_camera_locked = True

            anim.play()

            self.event_wait_camera = True

            return
        
        # ==========================
        # FADE OUT
        # ==========================
        if action == "fade_out":

            duration = cmd.get(
                "duration",
                1.0
            )

            self.event_wait_fade = True

            self.start_fade_out(
                callback=self.on_event_fade_finished,
                speed=1.0 / max(0.01, duration)
            )

            return
        
        # ==========================
        # FADE IN
        # ==========================
        if action == "fade_in":

            duration = cmd.get(
                "duration",
                1.0
            )

            self.event_wait_fade = True

            self.start_fade_in(
                callback=self.on_event_fade_finished,
                speed=1.0 / max(0.01, duration)
            )

            return
        
        if action == "deploy_party":

            leader = self.runtime_world.main_actor

            lx = leader["gx"]
            ly = leader["gy"]

            reserved = set()

            for actor_name in self.party:

                if actor_name == leader["inst"].actor_name:
                    continue

                pack = spawn_party_actor(
                    self,
                    actor_name
                )

                if not pack:
                    continue

                tx, ty = find_free_near_tile(
                    self,
                    lx,
                    ly,
                    reserved
                )

                reserved.add((tx, ty))

                inst = pack["inst"]

                inst.world_move_queue = [
                    (tx, ty)
                ]

                inst.is_world_moving = True

            return
        
        if action == "withdraw_party":

            leader = self.runtime_world.main_actor

            lx = leader["gx"]
            ly = leader["gy"]

            for pack in self.runtime_world.runtime_party_actors:

                inst = pack["inst"]

                inst.withdraw_after_move = True

                inst.world_move_queue = [
                    (lx, ly)
                ]

                inst.is_world_moving = True

            return
        
        
        if action == "all_play_idle":

            for pack in self.runtime_world.runtime_party_actors:

                inst = pack["inst"]

                clip="idle"

                if not inst:
                    print("ACTOR NO ENCONTRADO:", actor_name)
                    return

                if not inst.animator:
                    print("SIN ANIMATOR")
                    return

                if clip not in inst.animator.clips:
                    print("CLIP NO EXISTE:", clip)
                    return

                inst.scripted_animation = True

                inst.animator.play(clip)

                print("PLAYING:", clip)
        
        if action == "move_actor":

            actor_name = cmd.get("actor", "")
            direction = cmd.get("direction", "down")
            tiles = cmd.get("tiles", 1)

            pack = self.find_actor_pack_by_name(actor_name)

            if not pack:
                print("ACTOR NO ENCONTRADO")
                return

            inst = pack["inst"]

            start_x = pack["gx"]
            start_y = pack["gy"]

            dx = 0
            dy = 0

            if direction == "left":
                dx = -1

            elif direction == "right":
                dx = 1

            elif direction == "up":
                dy = -1

            elif direction == "down":
                dy = 1

            queue = []

            cx = start_x
            cy = start_y

            for i in range(tiles):

                nx = cx + dx
                ny = cy + dy

                queue.append((nx, ny))

                cx = nx
                cy = ny

            inst.world_move_queue = queue

            inst.is_world_moving = True

            inst.event_move_actor = True

            self.event_wait_move = True

            return

        # ==========================
        # DIALOG
        # ==========================
        if action == "show_dialog":
            from RuntimeActor import RuntimeActor
            
            self.dialog_visible = True
            self.dialog_pages = cmd.get("text", [""])
            self.dialog_index = 0
            self.dialog_speaker = cmd.get("speaker", "")
            self.dialog_visible_chars = 0
            self.dialog_char_timer = 0
            self.dialog_char_speed = 0.03
            self.event_wait_input = True

            if not hasattr(self, "dialog_continue_actor"):

                spr = self.sprites["botones.png"]

                self.dialog_continue_actor = RuntimeActor(self)

                self.dialog_continue_actor.animator = Animator(
                    spr.base_clips
                )

                self.dialog_continue_actor.animator.play("latir_a")

            print("SHOW DIALOG")
            print(cmd.get("text", [""]))
            return
        
        if action == "lock_player":
            self.player_input_locked = True
            return

        if action == "unlock_player":
            self.player_input_locked = False
            return
        
        # ==========================
        # COMBAT
        # ==========================
        if action == "start_combat":

            self.pending_combat_enemy = True

            end_world_event(self)

            return
        # ==========================
        # CHANGE SCENE
        # ==========================
        if action in ("next_scene", "change_scene"):

            scene_file = cmd.get(
                "scene_new",
                cmd.get("scene", cmd.get("file", ""))
            )

            if not scene_file:
                print("NEXT SCENE WITHOUT TARGET")
                return

            manager = get_runtime_scene_manager(self)
            manager.change_world_scene(self, scene_file)

            return

        # ==========================
        # END EVENT
        # ==========================
        if action == "end_event":
            end_world_event(self)
            return
        
def spawn_party_actor(self, actor_name):

        actor_def = self.actors.get(actor_name)

        if not actor_def:
            return None

        inst = ActorInstance(actor_name)

        inst.world_move_queue = []
        inst.is_world_moving = False
        inst.withdraw_after_move = False

        # animator
        if actor_def.sprite_sheets:

            sprname = actor_def.sprite_sheets[0]

            if sprname in self.sprites:

                sprite_asset = self.sprites[sprname]

                inst.animator = Animator(
                    self.clone_clips(
                        sprite_asset.base_clips
                    )
                )

                if "idle_frente" in inst.animator.clips:
                    inst.animator.play("idle_frente")

        leader = self.runtime_world.main_actor

        pack = {
            "inst": inst,
            "gx": leader["gx"],
            "gy": leader["gy"]
        }

        tile = self.runtime_world.grid[
            leader["gy"]
        ][
            leader["gx"]
        ]

        tile.actors.append(pack)

        self.runtime_world.runtime_party_actors.append(pack)

        return pack

def find_free_near_tile(
    self,
    gx,
    gy,
    reserved=None
):

    if reserved is None:
        reserved = set()

    offsets = [
        (1,0),
        (-1,0),
        (0,1),
        (0,-1),
        (1,1),
        (-1,1),
        (1,-1),
        (-1,-1)
    ]

    for ox, oy in offsets:

        tx = gx + ox
        ty = gy + oy

        if tx < 0 or ty < 0:
            continue

        if tx >= GRID_W or ty >= GRID_H:
            continue

        if (tx, ty) in reserved:
            continue

        t = self.runtime_world.grid[ty][tx]

        blocked = False

        for p in t.actors:
            blocked = True
            break

        if not blocked:
            return (tx, ty)

    return (gx, gy)
        
def update_world_actor_move(self, pack, dt):

    if not pack:
        return

    inst = pack["inst"]

    # =====================================
    # INIT
    # =====================================

    if not hasattr(inst, "world_move_queue"):
        inst.world_move_queue = []

    if not hasattr(inst, "is_world_moving"):
        inst.is_world_moving = False

    # =====================================
    # NO MOVEMENT
    # =====================================

    if not inst.is_world_moving:
        return

    # =====================================
    # FIN MOVIMIENTO
    # =====================================

    if not inst.world_move_queue:

        inst.is_world_moving = False
        # =====================================
        # WITHDRAW / DESPAWN
        # =====================================

        if getattr(inst, "withdraw_after_move", False):

            tile = self.runtime_world.grid[
                pack["gy"]
            ][
                pack["gx"]
            ]

            if pack in tile.actors:
                tile.actors.remove(pack)

            if pack in self.runtime_world.runtime_party_actors:
                self.runtime_world.runtime_party_actors.remove(pack)

            print("PARTY ACTOR REMOVED:", inst.actor_name)

            return

        # solo liberar wait si este actor
        # estaba siendo esperado por evento
        if getattr(inst, "event_move_actor", False):

            inst.event_move_actor = False

            self.event_wait_move = False

        print(
            "WORLD MOVE FINISHED:",
            inst.actor_name
        )

        # =====================================
        # IDLE FINAL
        # =====================================

        face = getattr(
            inst,
            "visual_facing",
            "frente"
        )

        idlemap = {
            "frente": "idle_frente",
            "espalda": "idle_espalda",
            "dere": "idle_perfil_dere",
            "izq": "idle_perfil_izq"
        }

        idle_anim = idlemap.get(
            face,
            "idle_frente"
        )

        if inst.animator:

            if idle_anim in inst.animator.clips:
                inst.animator.play(idle_anim)

        return

    # =====================================
    # TARGET TILE
    # =====================================

    tx, ty = inst.world_move_queue[0]

    speed = getattr(
        inst,
        "world_move_speed",
        3.0
    )

    dx = tx - (pack["gx"] + inst.offx)
    dy = ty - (pack["gy"] + inst.offy)

    dist = math.sqrt(dx * dx + dy * dy)

    # =====================================
    # WALK ANIMATION
    # =====================================

    if dist > 0.001:

        chosen = "walk_frente"

        # horizontal
        if abs(dx) > abs(dy):

            if dx > 0:

                chosen = "walk_perfil_dere"

                inst.visual_facing = "dere"

            else:

                chosen = "walk_perfil_izq"

                inst.visual_facing = "izq"

        # vertical
        else:

            if dy > 0:

                chosen = "walk_frente"

                inst.visual_facing = "frente"

            else:

                chosen = "walk_espalda"

                inst.visual_facing = "espalda"

        if inst.animator:

            if inst.animator.current != chosen:

                if chosen in inst.animator.clips:
                    inst.animator.play(chosen)

            inst.animator.update(dt)

    # =====================================
    # ARRIVAL
    # =====================================

    if dist < 0.05:

        oldtile = self.runtime_world.grid[
            pack["gy"]
        ][
            pack["gx"]
        ]

        if pack in oldtile.actors:
            oldtile.actors.remove(pack)

        pack["gx"] = tx
        pack["gy"] = ty

        inst.offx = 0
        inst.offy = 0

        newtile = self.runtime_world.grid[
            ty
        ][
            tx
        ]

        if pack not in newtile.actors:
            newtile.actors.append(pack)

        if hasattr(self, "play_runtime_floor_step"):
            self.play_runtime_floor_step(newtile, pack)

        inst.world_move_queue.pop(0)

        # =====================================
        # STEP IDLE
        # =====================================

        if not inst.world_move_queue:

            face = getattr(
                inst,
                "visual_facing",
                "frente"
            )

            idlemap = {
                "frente": "idle_frente",
                "espalda": "idle_espalda",
                "dere": "idle_perfil_dere",
                "izq": "idle_perfil_izq"
            }

            idle_anim = idlemap.get(
                face,
                "idle_frente"
            )

            if inst.animator:

                if idle_anim in inst.animator.clips:
                    inst.animator.play(idle_anim)

        return

    # =====================================
    # MOVE
    # =====================================

    inst.offx += (
        (dx / dist)
        * speed
        * dt
    )

    inst.offy += (
        (dy / dist)
        * speed
        * dt
    )

def check_runtime_autorun_events(self):
    if not hasattr(self, "runtime_world"):
        return False

    if not self.runtime_world:
        return False

    if self.world_event_running:
        return False

    if self.runtime_event_cooldown > 0:
        return False

    for row in self.runtime_world.grid:
        for t in row:
            ed = getattr(t, "event_data", None)

            if not ed:
                continue

            if not ed.get("enabled", False):
                continue

            if ed.get("trigger", "") != "autorun":
                continue

            execute_runtime_tile_event(self, t)
            return True

    return False

def check_runtime_proximity_events(self):

    if self.world_event_running:
        return

    pack = self.runtime_world.main_actor

    if not pack:
        return

    gx = pack["gx"]
    gy = pack["gy"]

    for row in self.runtime_world.grid:

        for t in row:

            ed = getattr(t, "event_data", None)

            if not ed:
                continue

            if not ed.get("enabled", False):
                continue

            if ed.get("trigger") != "proximity":
                continue

            tx = t.gx
            ty = t.gy

            dist = abs(tx - gx) + abs(ty - gy)

            trigger_dist = ed.get(
                "distance",
                ed.get("radius", 2)
            )

            if dist <= trigger_dist:

                execute_runtime_tile_event(
                    self,
                    t
                )

                return
        
def get_near_event_cell(self):

    if not self.runtime_world:
        return None

    pack = self.runtime_world.main_actor

    if not pack:
        return None

    gx = pack["gx"]
    gy = pack["gy"]

    inst = pack["inst"]

    dx = 0
    dy = 0

    if inst.facing == "espalda":
        dy = -1

    elif inst.facing == "frente":
        dy = 1

    elif inst.facing == "izquierda":
        dx = -1

    elif inst.facing == "derecha":
        dx = 1

    tx = gx + dx
    ty = gy + dy

    if tx < 0 or ty < 0:
        return None

    if tx >= GRID_W or ty >= GRID_H:
        return None

    t = self.runtime_world.grid[ty][tx]

    ed = getattr(t, "event_data", None)

    if not ed:
        return None

    if not ed.get("enabled", False):
        return None

    if ed.get("trigger", "") != "action":
        return None

    return t
    
def check_runtime_step_events(self):
        if not hasattr(self, "runtime_world"):
            return

        if not self.runtime_world:
            return

        if not self.runtime_world.main_actor:
            return

        if self.world_event_running:
            return

        if self.runtime_event_cooldown > 0:
            return

        pack = self.runtime_world.main_actor
        gx = pack["gx"]
        gy = pack["gy"]

        t = self.runtime_world.grid[gy][gx]

        ed = getattr(t, "event_data", None)
        if not ed:
            return

        if not ed.get("enabled", False):
            return

        if ed.get("trigger", "") != "step":
            return
        
        print(
            "AUTORUN:",
            ed.get("once"),
            ed.get("done")
        )

        execute_runtime_tile_event(self,t)

def execute_runtime_tile_event(self, t):
        if not t:
            return

        ed = getattr(t, "event_data", None)
        if not ed:
            return

        if not ed.get("enabled", False):
            return

        if self.runtime_event_cooldown > 0:
            return

        if ed.get("once", False) and ed.get("done", False):
            return

        req = ed.get("switch_required", "")
        if req:
            if not hasattr(self, "runtime_switches"):
                self.runtime_switches = {}

            if not self.runtime_switches.get(req, False):
                return

        dlg = ed.get("dialog", "")
        if dlg:
            self.show_runtime_dialog(dlg)

        script = ed.get("script", [])
        if script:
            start_world_script(self, script)

        scene_file = resolve_runtime_scene_path(ed.get("scene", ""))
        if scene_file and os.path.exists(scene_file):
            start_world_event(self, scene_file)

        tp = ed.get("teleport", None)
        if tp:
            runtime_teleport_player(self, tp)

        if ed.get("combat", False):

            enemy_id = ed.get("enemy_id", "")

            if self.world_event_running:
                self.pending_combat_enemy = True
            else:
                self.runtime_combat.start_runtime_combat(enemy_id)

        swset = ed.get("switch_set", "")
        if swset:
            if not hasattr(self, "runtime_switches"):
                self.runtime_switches = {}
            self.runtime_switches[swset] = True

        if ed.get("once", False):
            ed["done"] = True

        self.runtime_event_cooldown = 0.40

def runtime_teleport_player(self, tp):
        if not self.runtime_world:
            return

        target_map = tp.get("map") or tp.get("map_id") or tp.get("map_name")

        if target_map and hasattr(self, "maps") and target_map in self.maps:
            current_runtime_map = getattr(self.runtime_world, "map_id", getattr(self, "current_runtime_map_id", None))

            if target_map != current_runtime_map:
                self.current_runtime_map_id = target_map
                self.runtime_world = self.runtime.build_runtime_world_copy(target_map)

        if not self.runtime_world.main_actor:
            return

        nx = tp.get("x", 0)
        ny = tp.get("y", 0)

        if nx < 0 or ny < 0 or nx >= GRID_W or ny >= GRID_H:
            return

        self.runtime_world.main_actor["gx"] = nx
        self.runtime_world.main_actor["gy"] = ny

        print("PLAYER TELEPORTED:", getattr(self.runtime_world, "map_id", "Map001"), nx, ny)

def execute_tile_event(self, t):
        t.event_done = True

        if t.event_text:
            self.runtime_message = t.event_text
            self.runtime_message_timer = 3.0

        if t.event_script:
            print("RUN TILE SCRIPT:", t.event_script)

        if t.event_teleport:
            tx, ty = t.event_teleport
            pack = self.runtime_world.main_actor
            pack["gx"] = tx
            pack["gy"] = ty
            pack["inst"].offx = 0
            pack["inst"].offy = 0

def try_interact_npc(self):

        npc_pack = get_near_interactive_actor(self)

        if npc_pack:
            inst = npc_pack["inst"]

            if not (inst.interact_once and inst.interacted):
                inst.interacted = True
                self.runtime_message = f"{inst.npc_name}: {inst.interact_text}"
                self.runtime_message_timer = 3.0

                if inst.trigger_event:
                    print("EVENT:", inst.trigger_event)

                return

        evt = get_near_event_cell(self)
        if evt:
            execute_tile_event(self, evt)

def runtime_position_blocked(self, nx, nz):
        gx = int(nx)
        gy = int(nz)

        if gx < 0 or gy < 0 or gx >= GRID_W or gy >= GRID_H:
            return True

        t = self.runtime_world.grid[gy][gx]

        # si el tile está completamente encerrado por walls lo tratamos bloqueado
        # y además chequeamos paredes según borde

        margin = 0.18

        localx = nx - gx
        localz = nz - gy

        if t.wall_w and localx < margin:
            return True
        if t.wall_e and localx > 1.0 - margin:
            return True
        if t.wall_n and localz < margin:
            return True
        if t.wall_s and localz > 1.0 - margin:
            return True

        return False

def get_near_interactive_actor(self):
        if not hasattr(self, "runtime_world"):
            return None

        if not self.runtime_world:
            return None

        if not self.runtime_world.main_actor:
            return None

        pack = self.runtime_world.main_actor
        gx = pack["gx"]
        gy = pack["gy"]
        inst = pack["inst"]

        dx = 0
        dy = 0

        if inst.facing == "espalda":
            dy = -1
        elif inst.facing == "frente":
            dy = 1
        elif inst.facing == "izquierda":
            dx = -1
        elif inst.facing == "derecha":
            dx = 1

        tx = gx + dx
        ty = gy + dy

        if tx < 0 or ty < 0 or tx >= GRID_W or ty >= GRID_H:
            return None

        t = self.runtime_world.grid[ty][tx]

        for pack2 in getattr(t, "actors", []):
            npc = pack2["inst"]

            if npc.actor_name not in self.actors:
                continue

            actor_def = self.actors[npc.actor_name]

            if actor_def.interactive:
                return actor_def

        return None
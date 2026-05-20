import json
import os
from RuntimeCombat import RuntimeCombat
from SpriteManager import Animator
from config import *


def start_world_event(self, jsonfile):
        if not os.path.exists(jsonfile):
            print("EVENT FILE NOT FOUND:", jsonfile)
            return

        with open(jsonfile, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.current_event_data = data
        self.current_event_script = data.get("script", [])
        self.current_event_index = 0

        self.world_event_running = True
        self.world_event_locked = True

        self.event_wait_timer = 0
        self.event_wait_input = False
        self.event_wait_move = None
        self.event_advance_block = False

        print("WORLD EVENT START:", jsonfile)

def update_world_event(self, dt):
        if not self.world_event_running:
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

        # wait actor movement
        if self.event_wait_move is not None:
            if self.event_wait_move["done"]:
                self.event_wait_move = None
            else:
                return

        if self.current_event_index >= len(self.current_event_script):
            end_world_event(self)
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
            self.pending_combat_enemy = None

            self.runtime_combat.start_runtime_combat(enemy)

        print("WORLD EVENT END")

def run_world_event_command(self, cmd):
        action = cmd.get("action", "")

        # ==========================
        # WAIT
        # ==========================
        if action == "wait":
            self.event_wait_timer = cmd.get("time", 1000) / 1000.0
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
        
        # ==========================
        # COMBAT
        # ==========================
        if action == "start_combat":
            pack = self.runtime_world.main_actor
            gx = pack["gx"]
            gy = pack["gy"]
            t = self.runtime_world.grid[gy][gx]
            ed = getattr(t, "event_data", None)
            enemy_id = ed.get("enemy_id", "")

            if self.world_event_running:
                self.pending_combat_enemy = enemy_id
            else:
                self.runtime_combat.start_runtime_combat(enemy_id)
            return
        # ==========================
        # END EVENT
        # ==========================
        if action == "end_event":
            end_world_event(self)
            return
        
def get_near_event_cell(self):
        if not hasattr(self, "runtime_world"):
            return None

        if not self.runtime_world:
            return None

        if not self.runtime_world.main_actor:
            return None

        pack = self.runtime_world.main_actor
        gx = pack["gx"]
        gy = pack["gy"]

        dirs = [
            (0,0),
            (0,0),
            (0,0),
            (0,0)
        ]

        for dx,dy in dirs:
            tx = gx + dx
            ty = gy + dy

            if tx < 0 or ty < 0 or tx >= GRID_W or ty >= GRID_H:
                continue

            t = self.runtime_world.grid[ty][tx]

            if getattr(t, "event_data", {}).get("enabled", False):
                if t.event_data.get("trigger") == "action":
                    return t

        return None
    
def check_runtime_step_events(self):
        print("step event")
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

        scene_file = ed.get("scene", "")
        if scene_file and os.path.exists(scene_file):
            start_world_event(self,scene_file)

        tp = ed.get("teleport", None)
        if tp:
            runtime_teleport_player(self, tp)

        if ed.get("combat", False):

            enemy_id = ed.get("enemy_id", "")

            if self.world_event_running:
                self.pending_combat_enemy = enemy_id
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

        if not self.runtime_world.main_actor:
            return

        nx = tp.get("x", 0)
        ny = tp.get("y", 0)

        if nx < 0 or ny < 0 or nx >= GRID_W or ny >= GRID_H:
            return

        self.runtime_world.main_actor["gx"] = nx
        self.runtime_world.main_actor["gy"] = ny

        print("PLAYER TELEPORTED:", nx, ny)

def execute_tile_event(self, t):
        t.event_done = True

        if t.event_text:
            self.runtime_message = t.event_text
            self.runtime_message_timer = 3.0

        if t.event_combat:
            ed = getattr(t, "event_data", None)
            self.runtime_combat.start_runtime_combat(ed.get("enemy_id", ""))
            print("TILE COMBAT START")

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

                if inst.trigger_combat:
                    pack = self.runtime_world.main_actor
                    gx = pack["gx"]
                    gy = pack["gy"]
                    t = self.runtime_world.grid[gy][gx]
                    ed = getattr(t, "event_data", None)
                    self.runtime_combat.start_runtime_combat(ed.get("enemy_id", ""))
                    print("COMBAT TRIGGERED")

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
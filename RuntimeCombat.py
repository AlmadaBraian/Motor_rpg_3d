import math
from collections import Counter, deque

from ActorInstance import ActorInstance
import IA
from RuntimeSkill import RuntimeSkill
from SpriteManager import Animator
from config import GRID_H, GRID_W, SETTINGS
from motor_rpg.domain.combat import CombatRules, actor_stats_from_object
from BasicScripts import NORMAL_ATTACK_SCRIPT, GUN_ATTACK_SCRIPT
from SceneManager import get_runtime_scene_manager
import random



class RuntimeCombat:

    def __init__(self, owner):
        self.owner = owner
        self.battle_camera_mode = 0
        self.runtime_attack_camera = False
        self.runtime_attack_cam_target = None
        self.attack_anim_inst = None
        self.damage_anim_inst = None
        self.performing_attack = False
        self.attack_performed = False
        self.attack_anim_side = "izq"
        self.attack_result_type = "normal"
        self.turn_camera_lock = 0
        self.charge_attack_active = False
        self.charge_attack_user = None
        self.charge_attack_target = None
        self.charge_attack_action = None
        self.charge_attack_push_tile = None
        self.charge_attack_camera = False
        self.runtime_charge_camera = False
        self.mantle_skill_active = False
        self.mantle_skill_user = None
        self.mantle_skill_action = None
        self.mantle_skill_target_tile = None
        self.charge_phase = None
        self.charge_phase_timer = 0.0
        self.previous_camera_orbit = None
        self.last_attack_attacker = None
        self.last_attack_target = None
        self.counter_attack_in_progress = False
        self.current_attack_is_counter = False
        self.actual_damage = 0
        self.combat_text_popups = []
        self.attack_popup_spawned = False
        self.battle_pause_timer = 0.0
        self.active_runtime_skill = None
        self.current_attack_context = None
        self.turn_end_timer = 0
        self.pending_turn_end = False
        self.combat_end_state = None
        self.combat_result = None
        

    # =========================================================
    # START COMBAT
    # =========================================================

    def start_runtime_combat(self, enemy_id=""):

        o = self.owner

        if o.battle_mode:
            return
        
        print("START COMBAT!!!")
        
        if o.runtime_cam_orbit is None:
            o.runtime_cam_orbit = 0
        
        self.previous_camera_orbit = o.runtime_cam_orbit

        o.battle_mode = True

        o.battle_units = []

        o.combat_move_tiles = []
        o.combat_path = []

        o.combat_actor_moving = False
        o.combat_move_queue = []

        self.reset_runtime_actor_motion()

        o.battle_input_cooldown = 0

        o.battle_cam_target_x = 0
        o.battle_cam_target_z = 0
        o.battle_cam_active = True
        self.battle_camera_mode = 0

        o.button_A_command = "Seleccionar"
        o.button_X_command = ""
        o.button_Y_command = ""
        o.button_B_command = ""

        o.party_menu = o.party.copy()
        o.party_menu_index = 0
        o.battle_state = "party_menu"

        o.show_ui = True

        # =====================================
        # PARTY
        # =====================================

        #o.battle_state = "deploy_party"

        o.battle_deploy_party = []
        o.battle_deploy_index = 0
        o.battle_deploy_tiles = []
        self.create_battle_party_units()
        self.build_deploy_tiles()

        leader = o.runtime_world.main_actor

        tile = o.runtime_world.grid[
            leader["gy"]
        ][
            leader["gx"]
        ]

        if leader in tile.actors:
            tile.actors.remove(leader)

        for row in o.runtime_world.grid:
            for t in row:
                for pack in t.actors:

                    inst = pack["inst"]

                    if inst.actor_name not in o.actors:
                        continue

                    actor_def = o.actors[inst.actor_name]

                    team = getattr(actor_def, "team", "npc")


                    if team not in ["player", "ally", "enemy"]:
                        continue

                    inst.battle_team = team

                    o.battle_units.append(pack)

                    print(
                        "BATTLE UNIT:",
                        inst.actor_name,
                        "TEAM:",
                        inst.battle_team,
                        "POS:",
                        pack["gx"],
                        pack["gy"]
                    )

        first = o.battle_deploy_tiles[0]

        o.battle_cursor_x = first[0]
        o.battle_cursor_y = first[1]
        

    def finish_combat_victory(self):

        print("SCREEN ALPHA:",
            self.owner.screen_fade_alpha)

        self.remove_party_members()

        self.end_runtime_combat()

        self.owner.start_fade_in()

    def build_battle_turn_order(self):

        o = self.owner

        for pack in o.battle_units:

            inst = pack["inst"]

            base_init = getattr(
                o.actors[inst.actor_name],
                "speed",
                5
            )

            speed = getattr(
                o.actors[inst.actor_name],
                "initiative",
                10
            )

            roll = random.randint(1, 20)

            inst.battle_initiative = (
                base_init + roll + speed
            )

            print(
                inst.actor_name,
                "INIT:",
                base_init,
                "+",
                roll,
                "+",
                speed,
                "=",
                inst.battle_initiative
            )

        o.battle_turn_order = sorted(
            o.battle_units,
            key=lambda p: p["inst"].battle_initiative,
            reverse=True
        )

        o.update_battle_unit_facings()

        o.battle_turn_index = 0

    def create_battle_party_units(self):

        o = self.owner

        o.battle_deploy_party = []

        for actor_name in o.party:

            inst = ActorInstance(actor_name)

            actor_def = o.actors.get(actor_name)

            if actor_def:

                inst.hp = actor_def.hp
                inst.max_hp = actor_def.max_hp

                inst.sp = actor_def.sp
                inst.max_sp = actor_def.max_sp

                inst.atk = actor_def.atk
                inst.defense = actor_def.defense

            if actor_name == o.runtime_world.main_actor["inst"].actor_name:

                pack = o.runtime_world.main_actor
                pack["inst"].battle_team = "player"

                o.battle_deploy_party.append(pack)
                continue

            # animator
            if getattr(actor_def, "sprite_sheets", []):

                sprname = actor_def.sprite_sheets[0]

                if sprname in o.sprites:

                    sprite_asset = o.sprites[sprname]

                    inst.animator = Animator(
                        o.clone_clips(
                            sprite_asset.base_clips
                        )
                    )

                    if sprite_asset.base_clips:

                        default_idle = "idle_dere"

                        if default_idle in inst.animator.clips:
                            inst.animator.play(default_idle)

                        else:
                            first = sprite_asset.base_clips[0].name
                            inst.animator.play(first)

            inst.battle_team = "player"

            pack = {
                "inst": inst,
                "gx": 0,
                "gy": 0
            }

            o.battle_deploy_party.append(pack)


    def place_next_party_member(self):

        o = self.owner

        idx = o.battle_deploy_index

        if idx >= len(o.battle_deploy_party):
            return

        pack = o.battle_deploy_party[idx]

        # si es el líder existente del mundo
        if pack == o.runtime_world.main_actor:

            self.remove_actor_from_current_tile(pack)

        pack["gx"] = o.battle_cursor_x
        pack["gy"] = o.battle_cursor_y

        for tx, ty in o.battle_deploy_tiles:

            blocked = False

            for p in o.battle_units:

                if (
                    p["gx"] == o.battle_cursor_x
                    and
                    p["gy"] == o.battle_cursor_y
                ):
                    return

            pack["gx"] = o.battle_cursor_x
            pack["gy"] = o.battle_cursor_y

            o.battle_units.append(pack)
            tile = o.runtime_world.grid[
                pack["gy"]
            ][
                pack["gx"]
            ]

            if pack not in tile.actors:
                tile.actors.append(pack)

            o.battle_deploy_index += 1

            if not blocked:
                o.battle_cursor_x = tx
                o.battle_cursor_y = ty
                break

        if o.battle_deploy_index >= len(o.battle_deploy_party):

            o.battle_deploy_tiles = []

            o.battle_state = "idle"

            # build turn order acá
            self.build_battle_turn_order()

            self.begin_battle_turn()

            print("TACTICAL COMBAT START")

    def place_party_member(self, actor_name, pos):

        o = self.owner

        tx, ty = pos

        # Buscar el pack correspondiente
        pack = None

        for p in o.battle_deploy_party:

            if p["inst"].actor_name == actor_name:
                pack = p
                break

        if not pack:
            return False

        # Tile ocupado
        for p in o.battle_units:

            if p["gx"] == tx and p["gy"] == ty:
                return False

        # Caso especial: líder
        if pack == o.runtime_world.main_actor:

            self.remove_actor_from_current_tile(pack)

        pack["gx"] = tx
        pack["gy"] = ty

        tile = o.runtime_world.grid[ty][tx]

        if pack not in tile.actors:
            tile.actors.append(pack)

        if pack not in o.battle_units:
            o.battle_units.append(pack)

        return True

    def skill_charge_camera(
    self,
    runtime_skill
    ):

        user_pack = runtime_skill.user_pack
        target_pack = runtime_skill.target_pack

        self.start_attack_camera(
            user_pack,
            target_pack
        )

        runtime_skill.flags[
            "camera_finished"
        ] = False
        

    # =========================================================
    # PATHFINDING
    # =========================================================

    def build_deploy_tiles(self):

        o = self.owner

        o.battle_deploy_tiles = []

        main = o.runtime_world.main_actor

        self.battle_camera_mode = 0

        mx = main["gx"]
        my = main["gy"]

        for yy in range(my - 1, my + 2):

            for xx in range(mx - 2, mx + 3):

                if xx < 0 or yy < 0:
                    continue

                if yy >= len(o.runtime_world.grid):
                    continue

                if xx >= len(o.runtime_world.grid[0]):
                    continue

                tile = o.runtime_world.grid[yy][xx]

                if tile.is_block:
                    continue

                o.battle_deploy_tiles.append((xx, yy))

    def remove_actor_from_current_tile(self, pack):

        o = self.owner

        old_tile = o.runtime_world.grid[
            pack["gy"]
        ][
            pack["gx"]
        ]

        if pack in old_tile.actors:
            old_tile.actors.remove(pack)

    def build_combat_path(self, sx, sy, tx, ty):

        o = self.owner

        grid = o.runtime_world.grid

        allow_mantle = self.actor_can_mantle(
                o.battle_selected_unit
            )

        

        q = deque()
        q.append((sx, sy))

        came = {}
        visited = set()

        visited.add((sx, sy))

        dirs = [
            (0, -1),
            (0, 1),
            (-1, 0),
            (1, 0)
        ]

        while q:

            x, y = q.popleft()

            if (x, y) == (tx, ty):
                break

            for dx, dy in dirs:

                nx = x + dx
                ny = y + dy

                if nx < 0 or ny < 0:
                    continue

                if nx >= GRID_W or ny >= GRID_H:
                    continue

                if (nx, ny) in visited:
                    continue

                if not self.combat_can_move_between(
                    x,
                    y,
                    nx,
                    ny,
                    allow_mantle=allow_mantle
                ):
                    continue

                if self.combat_tile_blocked(
                    nx,
                    ny,
                    o.battle_selected_unit
                ):
                    continue

                visited.add((nx, ny))

                came[(nx, ny)] = (x, y)

                q.append((nx, ny))

        if (tx, ty) not in came:
            return []

        path = []

        cur = (tx, ty)

        while cur != (sx, sy):
            path.append(cur)
            cur = came[cur]

        path.reverse()

        return path
    
    def build_mantle_path(
        self,
        sx,
        sy,
        tx,
        ty
    ):

        o = self.owner

        q = deque()
        q.append((sx, sy))

        came = {}
        visited = set()

        visited.add((sx, sy))

        dirs = [
            (0, -1),
            (0, 1),
            (-1, 0),
            (1, 0)
        ]

        while q:

            x, y = q.popleft()

            if (x, y) == (tx, ty):
                break

            for dx, dy in dirs:

                nx = x + dx
                ny = y + dy

                if nx < 0 or ny < 0:
                    continue

                if nx >= GRID_W or ny >= GRID_H:
                    continue

                if (nx, ny) in visited:
                    continue

                # =====================================
                # ACA ESTA LA CLAVE
                # =====================================

                if not self.combat_can_move_between(
                    x,
                    y,
                    nx,
                    ny,
                    allow_mantle=True
                ):
                    continue

                if self.combat_tile_blocked(
                    nx,
                    ny,
                    o.battle_selected_unit
                ):
                    continue

                visited.add((nx, ny))

                came[(nx, ny)] = (x, y)

                q.append((nx, ny))

        if (tx, ty) not in came:
            return []

        path = []

        cur = (tx, ty)

        while cur != (sx, sy):

            path.append(cur)

            cur = came[cur]

        path.reverse()

        return path
    
    def switch_attack_move(self):

        o = self.owner

        pack = o.battle_selected_unit

        if not pack:
            return

        inst = pack["inst"]

        can_move = not inst.battle_moved

        can_attack = not self.attack_performed

        current = o.current_action_type

        # =====================================
        # PRIORIDAD DE SWITCH
        # =====================================

        next_action = None

        # -------------------------------------
        # DESDE MOVE
        # -------------------------------------

        if current == "move":

            if can_attack:
                next_action = "attack"

        # -------------------------------------
        # DESDE ATTACK
        # -------------------------------------

        elif current == "attack":

            if can_move:
                next_action = "move"

        # -------------------------------------
        # DESDE SKILL / ITEM
        # -------------------------------------

        elif current in ["skill", "item"]:

            # preferir volver a attack
            if can_attack:
                next_action = "attack"

            elif can_move:
                next_action = "move"

        # =====================================
        # NO VALID ACTION
        # =====================================

        if not next_action:
            return

        # =====================================
        # APPLY ACTION
        # =====================================

        o.current_action_type = next_action

        # -------------------------------------
        # MOVE
        # -------------------------------------

        if next_action == "move":

            o.battle_state = "select_move"

            o.battle_target_tiles = []

            self.build_battle_move_tiles(pack)

            o.button_A_command = "Mover a"

        # -------------------------------------
        # ATTACK
        # -------------------------------------

        elif next_action == "attack":

            o.battle_state = "select_target"

            o.battle_move_tiles = []

            self.build_battle_target_tiles(pack)

            o.button_A_command = "Atacar"
            
    def confirm_item_target(self):

        print("confirm_item_target")

        o = self.owner

        if o.battle_state != "select_target":
            return

        user_pack = o.battle_selected_unit

        if not user_pack:
            return

        action_data = o.selected_combat_action

        if not action_data:
            return

        script = self.get_item_value(
            action_data,
            "script",
            []
        )

        print("ITEM SCRIPT 1:", script)
        
        item_name = getattr(
                action_data,
                "name",
                ""
            )

        for pack in o.battle_units:

            if getattr(pack["inst"], "battle_dead", False):
                    continue

            if (
                pack["gx"] == o.battle_cursor_x
                and
                pack["gy"] == o.battle_cursor_y
            ):

                target = pack
                break

        if not target:

            print("NO TARGET")

            return

        # =====================================
        # TARGET TYPE VALIDATION
        # =====================================

        target_type = self.get_skill_value(
                action_data,
                "target_type",
                "enemy"
        )

        user_team = user_pack["inst"].battle_team
        target_team = target["inst"].battle_team

        # -------------------------------------
        # ENEMY
        # -------------------------------------

        if target_type == "enemy":
            print("user_team", user_team)

            if user_team == target_team:

                print("INVALID ENEMY TARGET")

                return

        # -------------------------------------
        # ALLY
        # -------------------------------------

        elif target_type == "ally":

            if user_team != target_team:

                print("INVALID ALLY TARGET")

                return

        # -------------------------------------
        # SELF
        # -------------------------------------

        elif target_type == "self":

            if target != user_pack:

                print("INVALID SELF TARGET")

                return

        self.execute_combat_action(
            user_pack,
            target_pack=target,
            action_data=action_data
        )

        inst = user_pack["inst"]

        inst.used_item_this_turn = True

        #o.button_X_command = "Guard"

    # =========================================================
    # MANTLE SKILL
    # =========================================================

    def execute_mantle_skill(
        self,
        user_pack,
        target_tile,
        action_data
    ):
        print("=== MANTLE FUNCTION VERSION NEW ===")

        print("TARGET TILE:", target_tile)
        print("USER:", user_pack)

        o = self.owner

        user = user_pack["inst"]

        tx, ty = target_tile

        print("execute_mantle_skill", target_tile)
        

        # =====================================================
        # VALIDACIONES
        # =====================================================

        if tx < 0 or ty < 0:
            print("MANTLE VALIDATION 1")
            return False

        if tx >= GRID_W or ty >= GRID_H:
            print("MANTLE VALIDATION 2")
            return False

        t = o.runtime_world.grid[ty][tx]

        # debe ser block
        if not getattr(t, "is_block", False):
            print("MANTLE VALIDATION 3")
            return False
        
        print("IS BLOCK:", getattr(t, "is_block", False))

        # ocupado?
        for pack in o.battle_units:

            if pack == user_pack:
                continue

            if (
                pack["gx"] == tx
                and
                pack["gy"] == ty
            ):

                inst = pack["inst"]

                if not getattr(inst, "battle_dead", False):
                    return False
                
        # =====================================================
        # BUSCAR TILE ADYACENTE
        # =====================================================

        ux = user_pack["gx"]
        uy = user_pack["gy"]

        best_dist = 999999
        adjacent_tile = None

        dirs = [
            (0, -1),
            (0, 1),
            (-1, 0),
            (1, 0)
        ]

        for dx, dy in dirs:

            nx = tx + dx
            ny = ty + dy

            if nx < 0 or ny < 0:
                continue

            if nx >= GRID_W or ny >= GRID_H:
                continue

            nt = o.runtime_world.grid[ny][nx]

            # no puede ser block
            if getattr(nt, "is_block", False):
                continue

            # ocupado?
            blocked = False

            for pack in o.battle_units:

                if pack == user_pack:
                    continue

                if (
                    pack["gx"] == nx
                    and
                    pack["gy"] == ny
                ):

                    inst = pack["inst"]

                    if not getattr(inst, "battle_dead", False):
                        blocked = True
                        break

            if blocked:
                continue

            # tiene que poder mantle
            if not self.combat_can_move_between(
                nx,
                ny,
                tx,
                ty,
                allow_mantle=True
            ):
                continue

            # distancia al usuario
            dist = abs(nx - ux) + abs(ny - uy)

            if dist < best_dist:

                best_dist = dist

                adjacent_tile = (nx, ny)
                print("ADJACENT TILE:", adjacent_tile)

        # =====================================================
        # MOVIMIENTO
        # =====================================================

        if adjacent_tile is None:
            print("NO ADJACENT TILE")
            return False

        path = self.build_mantle_path(
            ux,
            uy,
            adjacent_tile[0],
            adjacent_tile[1]
        )

        # =====================================================
        # GUARDAR CONTEXTO
        # =====================================================

        self.mantle_skill_active = True
        self.mantle_skill_user = user_pack
        self.mantle_skill_action = action_data
        self.mantle_skill_target_tile = (tx, ty)


        if adjacent_tile != (ux, uy) and not path:

            print("NO PATH TO MANTLE")
            print("MANTLE VALIDATION 4")

            return False
        
        if adjacent_tile == (ux, uy):

            self.setup_mantle_context(user, user_pack, tx, ty)

            user.mantle_started = True

            self.finish_mantle_skill()
            print("MANTLE VALIDATION 5")

            return "async"

        o.combat_move_queue = path

        

        user.is_battle_moving = True
        user.battle_move_timer = 0.0
        user.battle_moved = True

        self.setup_mantle_context(user, user_pack, tx, ty)

        o.battle_selected_unit = None

        o.battle_move_tiles = []

        o.battle_state = "idle"

        print("MANTLE MOVE START")
        print("MANTLE VALIDATION 6")

        return "async"
    
    def setup_mantle_context(self, user, user_pack, tx, ty):

        user.combat_using_mantle = True
        user.combat_mantle_target = (tx, ty)

        self.owner.combat_actor_moving = True
        self.owner.combat_moving_unit = user_pack


    # =========================================================
    # FIN MANTLE SKILL
    # =========================================================
    def finish_mantle_skill(self):

        o = self.owner

        user_pack = self.mantle_skill_user
        #user = user_pack["inst"]

        tx, ty = self.mantle_skill_target_tile

        ux = user_pack["gx"]
        uy = user_pack["gy"]

        dx = tx - ux
        dy = ty - uy

        started = o.runtime_actor.try_start_mantle(
            user_pack,
            tx - user_pack["gx"],
            ty - user_pack["gy"]
        )

        if not started:

            print("FAILED START MANTLE")
            self.mantle_skill_active = False
            return

        o.battle_move_tiles = []
        o.battle_target_tiles = []
        print("MANTLE STARTED")

    def complete_mantle_skill(self):

        runtime_skill = self.active_runtime_skill

        if not runtime_skill:
            return

        user_pack = self.mantle_skill_user
        user = user_pack["inst"]

        user.combat_using_mantle = False

        self.mantle_skill_active = False
        self.mantle_skill_action = None

        user.combat_mantle_target = None

        runtime_skill.flags["skill_async"] = True
        

    def confirm_selected_skill(self):

        print("selected_skill")

        o = self.owner

        pack = None

        if o.battle_state != "select_target":
            return

        user_pack = o.battle_selected_unit

        if not user_pack:
            return
        
        inst = user_pack["inst"]

        action_data = o.selected_combat_action

        if not action_data:
            return
        
        if not inst.special_meter == getattr(user_pack, "max_special_meter", 100):
            return
        
        inst.special_meter = 0

        script = self.get_skill_value(
            action_data,
            "script",
            []
        )

        print("SKILL SCRIPT:", script)
        
        skill_name = getattr(
                action_data,
                "name",
                ""
            )

        # =====================================
        # TILE TARGET SKILLS
        # =====================================

        if skill_name == "Trepar":

            target = (
                o.battle_cursor_x,
                o.battle_cursor_y
            )

        # =====================================
        # NORMAL ACTOR TARGET
        # =====================================

        else:

            for pack in o.battle_units:

                if getattr(pack["inst"], "battle_dead", False):
                    continue

                if (
                    pack["gx"] == o.battle_cursor_x
                    and
                    pack["gy"] == o.battle_cursor_y
                ):

                    target = pack
                    break

            if not target:

                print("NO TARGET")

                return

            # =====================================
            # TARGET TYPE VALIDATION
            # =====================================

            target_type = self.get_skill_value(
                action_data,
                "target_type",
                "enemy"
            )

            user_team = user_pack["inst"].battle_team
            target_team = target["inst"].battle_team

            # -------------------------------------
            # ENEMY
            # -------------------------------------

            if target_type == "enemy":
                print("user_team", user_team)

                if user_team == target_team:

                    print("INVALID ENEMY TARGET")

                    return

            # -------------------------------------
            # ALLY
            # -------------------------------------

            elif target_type == "ally":

                if user_team != target_team:

                    print("INVALID ALLY TARGET")

                    return

            # -------------------------------------
            # SELF
            # -------------------------------------

            elif target_type == "self":

                if target != user_pack:

                    print("INVALID SELF TARGET")

                    return

        if skill_name == "Trepar":

            self.execute_combat_action(
                user_pack,
                target_tile=target,
                action_data=action_data
            )

            inst.battle_moved = True
            inst.battle_acted = True

        else:

            self.execute_combat_action(
                user_pack,
                target_pack=target,
                action_data=action_data
            )

        inst.used_skill_this_turn = True

        o.command_menu = self.build_unit_command_menu(user_pack)

        #o.button_X_command = "Guard"

    # =========================================================
    # INPUT
    # =========================================================

    def handle_battle_input(self, event):

        o = self.owner

        if o.battle_input_cooldown > 0:
            return
        
        if self.active_runtime_skill:
            return

        k = event.keysym.lower()
        
        # =====================================
        # CURSOR MOVEMENT
        # =====================================

        mx = 0
        my = 0

        if o.battle_state not in ["command_menu","skill_menu","item_menu", "party_menu"]:

            if k == "w":
                my = -1

            if k == "s":
                my = 1

            if k == "a":
                mx = -1

            if k == "d":
                mx = 1

        # =====================================
        # CHANGE BATTLE MODE
        # =====================================

        else:

            if event.keysym == "Up" or k == "w":
                o.battle_input_cooldown = 0.25
                if o.battle_state == "skill_menu":
                    o.skill_menu_index -= 1

                if o.battle_state == "item_menu":
                    o.item_menu_index -= 1

                if o.battle_state == "command_menu":
                    o.menu_index -= 1

                if o.battle_state == "party_menu":
                    o.party_menu_index -= 1

            if event.keysym == "Down" or k == "s":
                o.battle_input_cooldown = 0.25
                if o.battle_state == "skill_menu":
                    o.skill_menu_index += 1

                if o.battle_state == "item_menu":
                    o.item_menu_index += 1

                if o.battle_state == "command_menu":
                    o.menu_index += 1

                if o.battle_state == "party_menu":
                    o.party_menu_index += 1

            if len(o.skill_menu) > 0:

                o.skill_menu_index %= len(o.skill_menu)

            if len(o.item_menu) > 0:

                o.item_menu_index %= len(o.item_menu)

            if len(o.party_menu) > 0:
                o.party_menu_index %= len(o.party_menu)

            o.menu_index %= len(o.command_menu)

        o.menu_index %= len(o.command_menu)

        if len(o.skill_menu) > 0:

            o.skill_menu_index %= len(o.skill_menu)

        if len(o.item_menu) > 0:

            o.item_menu_index %= len(o.item_menu)

        if len(o.party_menu) > 0:
                o.party_menu_index %= len(o.party_menu)
        

        # =====================================
        # CAMERA RELATIVE ROTATION
        # =====================================

        cam_yaw = o.runtime_cam_orbit % 360

        sector = int((cam_yaw + 45) // 90) % 4

        rx = mx
        ry = my

       # 90°
        if sector == 1:
            rx = my
            ry = -mx

        # 180°
        elif sector == 2:
            rx = -mx
            ry = -my

        # 270°
        elif sector == 3:
            rx = -my
            ry = mx

        # =====================================
        # ATTACK TILE NAVIGATION
        # =====================================

        if (
            o.battle_state == "select_target"
            and
            (rx != 0 or ry != 0)
        ):

            if not o.battle_target_tiles:
                return

            current = (
                o.battle_cursor_x,
                o.battle_cursor_y
            )

            # cursor inválido
            if current not in o.battle_target_tiles:

                first = o.battle_target_tiles[0]

                o.battle_cursor_x = first[0]
                o.battle_cursor_y = first[1]

            else:

                best = current
                best_score = 999999

                for tx, ty in o.battle_target_tiles:

                    dx = tx - current[0]
                    dy = ty - current[1]

                    if rx != 0 and (dx * rx) <= 0:
                        continue

                    if ry != 0 and (dy * ry) <= 0:
                        continue

                    dist = abs(dx) + abs(dy)

                    if dist < best_score:

                        best_score = dist
                        best = (tx, ty)

                o.battle_cursor_x = best[0]
                o.battle_cursor_y = best[1]

            o.battle_input_cooldown = 0.12
            return

        o.battle_cursor_x += rx
        o.battle_cursor_y += ry


        if mx != 0 or my != 0:
            o.battle_input_cooldown = 0.12

        if o.battle_mode and o.battle_current_unit:
            p = o.battle_current_unit["inst"]
        else:
            p = o.runtime_world.main_actor["inst"]

        if k == "r":

            if self.battle_camera_mode == 0:
                self.battle_camera_mode = 1
            else:
                self.battle_camera_mode = 0

            o.battle_input_cooldown = 0.12

            print("camera mode " + str(self.battle_camera_mode ))

        if k == "q":
            p.rot_l = True

        if k == "e":
            p.rot_r = True

        if event.keysym == "x":
            o.battle_input_cooldown = 0.25
            self.execute_x_command()

        if event.keysym == "z":
            o.battle_input_cooldown = 0.25

            # =====================================
            # ENTER ITEM MODE
            # =====================================
            print("APRETE Z")
            o.battle_cursor_x = o.battle_current_unit["gx"]
            o.battle_cursor_y = o.battle_current_unit["gy"]

            return

        if event.keysym == "c":
            o.battle_input_cooldown = 0.25
            print("APRETE C")
                
            self.execute_b_command()
                
            return

        o.battle_cursor_x = max(
            0,
            min(GRID_W - 1, o.battle_cursor_x)
        )

        o.battle_cursor_y = max(
            0,
            min(GRID_H - 1, o.battle_cursor_y)
        )


        # =====================================
        # END TURN
        # =====================================

        if event.keysym == "Return":

            if not o.battle_current_unit:
                return

            if o.battle_input_cooldown > 0:
                return

            inst = o.battle_current_unit["inst"]

            if inst.battle_team != "player":
                return

            if o.combat_actor_moving:
                return

            o.battle_input_cooldown = 0.25

            self.end_battle_turn()

        # =====================================
        # SELECT / MOVE
        # =====================================

        if event.keysym == "space":

            o.battle_input_cooldown = 0.25

            if o.max_actions <= 0:
                    o.battle_selected_unit = None

                    o.battle_move_tiles = []
                    o.battle_target_tiles = []

                    o.battle_state = "idle"

                    self.end_battle_turn()


            # =====================================
            # SELECT UNIT
            # =====================================
            if o.battle_state == "party_menu":

                if not o.party_menu:
                    return

                actor_name = o.party_menu[
                    o.party_menu_index
                ]

                o.selected_deploy_actor = actor_name

                o.battle_state = "deploy_party"

                o.show_ui = True
                o.button_A_command = "Seleccionar"

                return
            
            if o.battle_state == "deploy_party":

                o.show_ui = True

                o.button_A_command = "Colocar"

                pos = (
                    o.battle_cursor_x,
                    o.battle_cursor_y
                )

                if pos not in o.battle_deploy_tiles:
                    return
                
                if self.place_party_member(
                    o.selected_deploy_actor,
                    pos
                ):

                    o.party_menu.remove(
                        o.selected_deploy_actor
                    )

                    o.selected_deploy_actor = None

                    if o.party_menu:

                        o.party_menu_index = 0
                        o.battle_state = "party_menu"

                    else:

                        o.battle_deploy_tiles = []

                        self.build_battle_turn_order()
                        self.begin_battle_turn()

                        o.battle_state = "idle"

                        print("TACTICAL COMBAT START")

            if o.battle_selected_unit is None:

                print(
                    "CURSOR:",
                    o.battle_cursor_x,
                    o.battle_cursor_y
                )

                for pack in o.battle_units:

                    if (
                        pack["gx"] == o.battle_cursor_x and
                        pack["gy"] == o.battle_cursor_y
                    ):

                        inst = pack["inst"]

                        if inst.battle_team not in ["player", "ally"]:
                            return

                        if pack != o.battle_current_unit:
                            return

                        if inst.battle_moved:
                            return

                        o.battle_selected_unit = pack

                        o.command_menu = self.build_unit_command_menu(pack)

                        o.menu_index = 0
                        o.battle_state = "command_menu"

                        o.button_A_command = "Seleccionar"

                        #o.button_A_command = "Mover a"

                        #o.current_action_type = "move"


                        return
                    
            else:
                #o.button_X_command = "Guard"
                print("")
                    
            # --------------------------------
            # menu
            # --------------------------------

            if o.battle_state in [
                "command_menu",
                "skill_menu",
                "item_menu"
            ]:

                if o.battle_state == "skill_menu":

                    skill_name = o.skill_menu[
                        o.skill_menu_index
                    ]

                    skill_data = o.skills.get(skill_name)

                    if not skill_data:
                        return

                    o.selected_combat_action = skill_data

                    o.current_action_type = "skill"

                    self.build_battle_target_tiles(
                        o.battle_selected_unit
                    )

                    o.battle_state = "select_target"

                    return
                
                if o.battle_state == "item_menu":

                    item_name = o.item_menu_data[
                        o.item_menu_index
                    ]

                    item_data = o.items.get(item_name)

                    if not item_data:
                        return

                    o.selected_combat_action = item_data

                    o.current_action_type = "item"

                    self.build_battle_target_tiles(
                        o.battle_selected_unit
                    )

                    o.battle_state = "select_target"

                    return

                selected, enabled = o.command_menu[o.menu_index]

                if not enabled:
                    return
                    

                if selected == "Mover":

                    o.current_action_type = "move"

                    o.battle_state = "select_move"

                    o.button_X_command = "Menú"

                    self.build_battle_move_tiles(
                        o.battle_selected_unit
                    )

                elif selected == "Atacar":

                    o.current_action_type = "attack"

                    o.battle_state = "select_target"

                    o.button_X_command = "Menú"

                    self.build_battle_target_tiles(
                        o.battle_selected_unit
                    )

                elif selected == "Especial":

                    actor_def = o.actors.get(
                        o.battle_selected_unit["inst"].actor_name
                    )

                    if not actor_def:
                        return

                    skills_actor = getattr(actor_def, "skills", [])

                    skills = []

                    for skill_name in skills_actor:

                        skill = self.owner.skills.get(skill_name)

                        if not skill.passive:
                            skills.append(skill_name)

                    if not skills:
                        return

                    o.skill_menu = skills
                    o.skill_menu_index = 0

                    o.battle_state = "skill_menu"

                    print(str(o.skill_menu))

                elif selected == "Items":

                    actor_def = o.actors.get(
                        o.battle_selected_unit["inst"].actor_name
                    )

                    if not actor_def:
                        return

                    inventory = getattr(actor_def, "inventory", [])

                    counter = Counter(inventory)

                    o.item_menu = [
                        f"{name} x{qty}"
                        for name, qty in counter.items()
                    ]

                    o.item_menu_data = list(counter.keys())

                    if not inventory:
                        return

                    #o.item_menu = inventory
                    o.item_menu_index = 0

                    o.battle_state = "item_menu"

                elif selected == "Interactuar":
                    from EventManager import execute_runtime_tile_event, get_near_event_cell
                    print("battle_interact_event antes", o.battle_interact_event)

                    if not o.battle_interact_event:
                        old_gx = o.battle_selected_unit["gx"]
                        old_gy = o.battle_selected_unit["gy"]
                        
                        near_evt = get_near_event_cell(o)
                        if near_evt:
                            execute_runtime_tile_event(o, near_evt)

                        new_gx = o.battle_selected_unit["gx"]
                        new_gy = o.battle_selected_unit["gy"]

                        if not (old_gx, old_gy) == (new_gx, new_gy):
                            o.battle_interact_event = True   
                            o.battle_selected_unit["inst"].interact_tile = False

                    print("battle_interact_event despues", o.battle_interact_event)

                    o.command_menu = self.build_unit_command_menu(o.battle_selected_unit)
                

                elif selected == "Guardia":

                    o.button_X_command = "Menú"

                    #self.execute_b_command()
                    print("GUARD")
                    inst = o.battle_current_unit["inst"]

                    inst.guard_mode = True

                    self.play_runtime_idle(inst)

                    self.end_battle_turn()
                    

                return

            # =====================================
            # MOVE UNIT
            # =====================================

            else:

                # =====================================
                # BUILD MOVE TILES
                # =====================================

                if o.battle_state == "select_move":

                    # =====================================
                    # MOVE UNIT
                    # =====================================

                    tx = o.battle_cursor_x
                    ty = o.battle_cursor_y

                    if (tx, ty) not in o.battle_move_tiles:
                        return

                    sx = o.battle_selected_unit["gx"]
                    sy = o.battle_selected_unit["gy"]

                    o.battle_selected_unit["origin_gx"] = sx
                    o.battle_selected_unit["origin_gy"] = sy

                    o.combat_path = self.build_combat_path(
                        sx,
                        sy,
                        tx,
                        ty
                    )

                    if not o.combat_path:
                        return
                    
                    need_mantle = False

                    px = sx
                    py = sy

                    for nx, ny in o.combat_path:

                        cur_h = self.combat_tile_height(px, py)
                        next_h = self.combat_tile_height(nx, ny)

                        if next_h - cur_h > 0.4:
                            need_mantle = True
                            break

                        px = nx
                        py = ny

                    if need_mantle:
                        self.battle_camera_mode = 1

                    o.combat_move_queue = o.combat_path.copy()

                    o.combat_moving_unit = o.battle_selected_unit

                    o.combat_actor_moving = True

                    o.battle_selected_unit["inst"].is_battle_moving = True

                    o.battle_selected_unit["inst"].battle_move_timer = 0.0

                    o.battle_selected_unit["inst"].battle_moved = True

                    o.battle_selected_unit = None

                    o.battle_move_tiles = []

                    o.battle_state = "idle"

                    print("UNIT MOVING")

                
                if o.battle_state == "select_target":

                    if o.current_action_type == "skill":
                        
                        self.confirm_selected_skill()

                    elif o.current_action_type == "item":
                        self.confirm_item_target()


                    else:
                        tx = o.battle_cursor_x
                        ty = o.battle_cursor_y
                        target = None

                        for pack in o.battle_units:

                            if getattr(pack["inst"], "battle_dead", False):
                                continue

                            if pack["inst"].battle_team in ["player", "ally"]:
                                return

                            if pack["gx"] == tx and pack["gy"] == ty:
                                target = pack
                                break

                        if target:
                            o.battle_attacker_unit = o.battle_selected_unit
                            self.attack_performed = True
                            o.battle_attacker_unit["inst"].battle_attacked = True
                            o.current_action_type = "attack"
                            #self.perform_attack(target)
                            self.execute_combat_action(
                                o.battle_attacker_unit,
                                target
                            )
                            
                            o.command_menu = self.build_unit_command_menu(o.battle_attacker_unit)
                            #inst.battle_acted = True
                            
                        print ("max_actions " + str(o.max_actions))
                        return

                    return

    def build_unit_command_menu(self, pack):
        from EventManager import get_near_event_cell

        o = self.owner

        inst = pack["inst"]

        print ("pack[inst].interact_tile antes", pack["inst"].interact_tile)
        print("battle_interact_event en build command menu", o.battle_interact_event)
        near_evt = get_near_event_cell(o)
        if near_evt:
            pack["inst"].interact_tile = True
            if o.battle_interact_event:
                pack["inst"].interact_tile = False

        else:
            pack["inst"].interact_tile = False
                            
        print ("pack[inst].interact_tile despues", pack["inst"].interact_tile)                  
                            

        menu = []

        menu = [
            ("Mover", not inst.battle_moved),
            ("Atacar", not inst.battle_attacked),
            ("Especial", not inst.used_skill_this_turn),
            ("Items", not inst.used_item_this_turn),
            ("Interactuar", inst.interact_tile),
            ("Guardia", not inst.guard_mode)
        ]

        return menu
    
    def use_item(
        self,
        user_pack,
        target_pack,
        item_data
    ):
        # aplicar efecto
        self.apply_item_effect(
            user_pack,
            target_pack,
            item_data
        )

        # consumir si corresponde
        if item_data.consumable:
            self.consume_item_inventory(
                user_pack,
                item_data
            )

    def apply_item_effect(
        self,
        user_pack,
        target_pack,
        item_data
    ):
        effect = item_data.effect_type

        if effect == "damage":
            self.apply_item_damage(
                user_pack,
                target_pack,
                item_data
            )

        elif effect == "heal":
            self.apply_item_heal(
                user_pack,
                target_pack,
                item_data
            )

        elif effect == "revive":
            self.apply_item_revive(
                target_pack,
                item_data
            )

        elif effect == "buff_attack":
            self.apply_item_buff(
                target_pack,
                "attack",
                item_data.power
            )

        elif effect == "buff_defense":
            self.apply_item_buff(
                target_pack,
                "defense",
                item_data.power
            )

        elif effect == "buff_speed":
            self.apply_item_buff(
                target_pack,
                "speed",
                item_data.power
            )

        elif effect == "status":
            self.apply_status(target_pack,item_data)

        elif effect == "script":
            self.run_item_script(
                user_pack,
                target_pack,
                item_data
            )

    def apply_item_damage(
        self,
        user_pack,
        target_pack,
        item_data
    ):
        combat_result = {
            "hit": True,
            "critical_hit": False,
            "damage": item_data.power,
            "type": "damage",
        }

        self.apply_damage(
            user_pack,
            target_pack,
            combat_result
        )

        
    def refesh_status(self,target_pack):

        target = target_pack["inst"]

        if (target.state != "idle"):

            target.state_counter += 1

            if target.state_counter < 3:
                print(
                    target.actor_name,
                    target.state
                )
            
            else:
                target.state_counter = 0
                target.state = "idle"


    def apply_status(self,
                    target_pack,
                    data_effect
    ):
        status_effect = data_effect.status_effect
        target = target_pack["inst"]
        target.state = status_effect  

        print(target.actor_name,
            status_effect
        )

    def apply_item_heal(
        self,
        user_pack,
        target_pack,
        item_data
    ):
        target = target_pack["inst"]

        heal_amount = item_data.power

        if not hasattr(target, "hp"):

            actor_def = self.owner.actors[
                target.actor_name
            ]

            target.hp = actor_def.hp
            target.max_hp = actor_def.max_hp

        old_hp = target.hp

        target.hp = min(
            target.max_hp,
            target.hp + heal_amount
        )

        healed = target.hp - old_hp
        
        result = {
            "type": "heal",
            "amount": healed,

        }
        self.show_popup(
            target_pack,
            {
                "popup_text": "HEAL +" + str(healed),
                "popup_color": (0.2,1,0.2,1)
            }
        )

        print(
            target.actor_name,
            "healed",
            healed
        )

    def apply_item_revive(
        self,
        target_pack,
        item_data
    ):
        target = target_pack["inst"]

        if not target.battle_dead:
            return

        target.battle_dead = False
        target.pending_remove = False

        target.hp = max(
            1,
            item_data.power
        )

        #self.restore_dead_unit_to_turn_order(
         #   target_pack
        #)

        print(
            target.actor_name,
            "REVIVED"
        )

    def run_item_script(
        self,
        user_pack,
        target_pack,
        item_data
    ):
        local_vars = {
            "battle": self,
            "user": user_pack["inst"],
            "target": target_pack["inst"],
            "item": item_data
        }

        exec(
            item_data.script,
            {},
            local_vars
        )

    def apply_item_buff(
        self,
        target_pack,
        stat,
        amount
    ):
        target = target_pack["inst"]

        if not hasattr(
            target,
            "battle_buffs"
        ):
            target.battle_buffs = {}

        target.battle_buffs.setdefault(
            stat,
            0
        )

        target.battle_buffs[stat] += amount

        print(
            target.actor_name,
            stat,
            "+",
            amount
        )

        
    def consume_item_inventory(
    self,
    user_pack,
    item_data
    ):

        o = self.owner

        user = user_pack["inst"]

        actor_def = o.actors.get(
            user.actor_name
        )

        if not actor_def:
            return

        inventory = getattr(
            actor_def,
            "inventory",
            []
        )

        print("ITEM DATA", str(item_data))

        item_name = item_data.name

        if item_name in inventory:

            inventory.remove(item_name)

            print(
                "CONSUMED:",
                item_name
            )

            print(
                "LEFT:",
                inventory.count(item_name)
            )

    def has_ammo(
        self,
        actor_name,
        ammo_name,
        amount=1
    ):

        o = self.owner

        actor_def = o.actors.get(actor_name)

        if not actor_def:
            return False

        inventory = getattr(
            actor_def,
            "inventory",
            []
        )

        return inventory.count(ammo_name) >= amount

    def consume_ammo(
        self,
        actor_name,
        ammo_name,
        amount=1
    ):

        o = self.owner

        actor_def = o.actors.get(actor_name)

        if not actor_def:
            return False

        inventory = getattr(
            actor_def,
            "inventory",
            []
        )

        if inventory.count(ammo_name) < amount:
            return False

        for _ in range(amount):

            inventory.remove(ammo_name)

        print ("BALAS RESTANTES", inventory.count(ammo_name))

        return True

    def execute_attack_action(
    self,
    user_pack,
    target_pack,
    is_counter=False
    ):
        o = self.owner
        self.current_attack_is_counter = is_counter

        inst = user_pack["inst"]
        
        weapon_name = getattr(
        o.actors[inst.actor_name],
        "weapon",
        ""
        )

        script = NORMAL_ATTACK_SCRIPT

        ammo = True

        if weapon_name:

            weapon = o.weapons.get(
                weapon_name
            )

            if weapon and weapon.use_bullets:

                if not self.has_ammo(
                    inst.actor_name,
                    weapon.ammo_item,
                    weapon.ammo_per_shot
                ):
                    ammo = False
                    print("OUT OF AMMO")
                    #return

            if weapon and weapon.script and ammo:

                script = weapon.script

                if weapon and weapon.use_bullets:

                    if weapon and weapon.use_bullets:

                        self.consume_ammo(
                            inst.actor_name,
                            weapon.ammo_item,
                            weapon.ammo_per_shot
                        )

        runtime_skill = RuntimeSkill(
        combat=self,
        script=script,
        user_pack=user_pack,
        target_pack=target_pack
        )

        runtime_skill.data[
            "is_counter"
        ] = is_counter

        self.active_runtime_skill = runtime_skill

        return runtime_skill

    def execute_skill_action(
    self,
    user_pack,
    target_pack,
    target_tile,
    action_data
    ):

        script = self.get_skill_value(
            action_data,
            "script",
            []
        )

        print("SKILL SCRIPT:", script)

        self.start_runtime_skill(
            script,
            user_pack,
            target_pack=target_pack,
            target_tile=target_tile,
            action_data=action_data
        )


    def start_runtime_skill(
    self,
    script,
    user_pack,
    target_pack=None,
    target_tile=None,
    action_data=None
    ):

        manager = get_runtime_scene_manager(self.owner)
        script = manager.build_combat_script(script)

        runtime_skill = RuntimeSkill(
            self,
            script,
            user_pack,
            target_pack,
            target_tile,
            action_data
        )

        self.active_runtime_skill = runtime_skill

        return runtime_skill

                
    def execute_combat_action(
    self,
    user_pack,
    target_pack=None,
    target_tile=None,
    action_data=None
    ):

        o = self.owner

        print(
            "EXECUTE COMBAT ACTION"
        )

        # =====================================
        # NORMAL ATTACK
        # =====================================

        if o.current_action_type == "attack":

            self.execute_attack_action(
                user_pack,
                target_pack
            )

            return

        # =====================================
        # ITEM
        # =====================================

        if o.current_action_type == "item":
            
            self.use_item(user_pack, target_pack, action_data)
        

            

        # =====================================
        # SKILL
        # =====================================

        self.execute_skill_action(
            user_pack,
            target_pack,
            target_tile,
            action_data
        )

    def apply_damage(
    self,
    attacker_pack,
    target_pack,
    combat_result
):
        o = self.owner

        attacker = attacker_pack["inst"]
        target = target_pack["inst"]

        if attacker.battle_dead:
            return False

        if target.battle_dead:
            return False

        atk_def = o.actors.get(attacker.actor_name)
        tgt_def = o.actors.get(target.actor_name)

        if not combat_result["hit"]:
            print("MISS")

            # no aplicar daño
            return False

        damage = combat_result["damage"]

        if not hasattr(target, "hp"):

            actor_def = o.actors[target.actor_name]

            target.hp = actor_def.hp
            target.max_hp = actor_def.max_hp

            target.sp = actor_def.sp
            target.max_sp = actor_def.max_sp

        if combat_result["critical_hit"] and damage <=3:
            damage*=2

        self.actual_damage = damage
            
        target.hp -= damage

        print(
            attacker.actor_name,
            "deals",
            damage,
            "to",
            target.actor_name
        )

        if target.hp <= 0:

            target.hp = 0
            target.battle_dead = True
            target.pending_remove = True

            is_main = getattr(
                o.actors[target.actor_name],
                "is_main",
                False
            )

            # La unidad queda visible hasta terminar su animacion de muerte,
            # pero sale del orden de turno para que no pueda actuar.
            self.remove_dead_unit_from_turn_order(target_pack)

            print(target.actor_name, "DEAD")


        return True

    def calculate_combat_result(
    self,
    attacker_pack,
    target_pack,
    action_data=None
    ):

        o = self.owner

        self.actual_damage = 0

        attacker = attacker_pack["inst"]
        target = target_pack["inst"]

        atk_def = o.actors.get(attacker.actor_name)
        tgt_def = o.actors.get(target.actor_name)

        if not atk_def or not tgt_def:
            return None

        rules = CombatRules(config=SETTINGS.combat, rng=random)
        resolved = rules.resolve_attack(
            actor_stats_from_object(attacker.actor_name, atk_def),
            actor_stats_from_object(target.actor_name, tgt_def),
            attacker_runtime=attacker,
            target_guarding=getattr(target, "guard_mode", False),
        )

        return {
            "hit": resolved.hit,
            "critical_hit": resolved.critical_hit,
            "result": resolved.result,
            "damage": resolved.damage,
            "roll": resolved.roll,
            "attack_total": resolved.attack_total,
            "armor_class": resolved.armor_class,
            "type": "damage",
        }
    
    def use_selected_skill(self):

        o = self.owner

        pack = o.battle_selected_unit

        if not pack:
            return

        inst = pack["inst"]

        if inst.used_skill_this_turn:
            print("SKILL ALREADY USED")
            return

        actor_def = o.actors.get(inst.actor_name)

        o.current_action_type = "skill"

        if not actor_def:
            return

        skills = getattr(actor_def, "skills", [])

        if not skills:
            return

        skill_name = skills[
            inst.selected_special_index
        ]

        skill_data = o.skills.get(skill_name)

        if not skill_data:
            print("SKILL NOT FOUND:", skill_name)
            if not inst.battle_moved:

                #o.current_action_type = "move"

                o.command_menu = self.build_unit_command_menu(pack)

                o.menu_index = 0
                o.battle_state = "command_menu"

                o.battle_target_tiles = []
                o.battle_move_tiles = []

            return

        o.selected_combat_action = skill_data

        o.battle_move_tiles = []

        self.build_battle_target_tiles(
            pack
        )

        o.battle_selected_unit = pack

        o.battle_state = "select_target"

        #o.button_B_command = skill_data.name

        o.button_A_command = "Seleccionar"

        print("SKILL SELECTED:", skill_data.name)


    def game_key_up(self, event):

        tkref = self.owner

        if not tkref.runtime_world:
            return

        if not tkref.runtime_world.main_actor:
            return

        if tkref.battle_mode and tkref.battle_current_unit:
            p = tkref.battle_current_unit["inst"]
        else:
            p = tkref.runtime_world.main_actor["inst"]

        k = event.keysym.lower()

        if k == "q":
            p.rot_l = False
        if k == "e":
            p.rot_r = False

        # Si el jugador suelta WASD durante combate, el RuntimeSystem
        # no recibe el KeyRelease de exploracion. Limpiamos siempre al
        # actor principal para que no vuelva a explorar con una bandera
        # de movimiento heredada.
        main_inst = tkref.runtime_world.main_actor["inst"]

        if k == "w":
            main_inst.move_b = False
        if k == "s":
            main_inst.move_f = False
        if k == "a":
            main_inst.move_l = False
        if k == "d":
            main_inst.move_r = False
        
        if event.keysym == "space":
            tkref.space_pressed = False

    def execute_x_command(self):

        o = self.owner

        if o.battle_state == "command_menu":
                print("GUARD")

                o.battle_selected_unit["inst"].guard_mode = True

                self.end_battle_turn()


        elif o.battle_state == "select_move":

                o.command_menu = self.build_unit_command_menu(o.battle_selected_unit)

                o.menu_index = 0
                o.battle_state = "command_menu"

                o.battle_move_tiles = []

                #o.button_X_command = "Guard"

                return

        elif o.battle_state == "select_target":

                o.command_menu = self.build_unit_command_menu(o.battle_selected_unit)

                o.menu_index = 0
                o.battle_state = "command_menu"

                o.battle_target_tiles = []

                #o.button_X_command = "Guard"

                return

    def execute_b_command(self):

        o = self.owner

        pack = o.battle_current_unit

        if not pack:
            return

        inst = pack["inst"]

        # =====================================
        # CANCELAR MOVIMIENTO
        # =====================================

        if o.button_B_command == "Cancelar":
            
            if o.battle_state not in ["command_menu","skill_menu","item_menu"]:
                o.battle_cursor_x = o.battle_current_unit["gx"]
                o.battle_cursor_y = o.battle_current_unit["gy"]
                return

            # ==========================================
            # CERRAR SUBMENUS
            # ==========================================

            if o.battle_state in [
                "skill_menu",
                "item_menu",
                "select_target"
            ]:

                o.command_menu = self.build_unit_command_menu(pack)

                #o.menu_index = 0
                o.battle_state = "command_menu"

                return
            
            # ==========================================
            # CANCELAR MOVIMIENTO
            # ==========================================

            if o.battle_state == "command_menu":

                if not inst.battle_moved:
                    return

            oldtile = o.runtime_world.grid[
                pack["gy"]
            ][
                pack["gx"]
            ]


            if pack in oldtile.actors:
                oldtile.actors.remove(pack)

            pack["gx"] = pack["origin_gx"]
            pack["gy"] = pack["origin_gy"]

            newtile = o.runtime_world.grid[
                pack["gy"]
            ][
                pack["gx"]
            ]

            if newtile.is_block:
                pack["inst"].offz = newtile.block_top

            else:
                pack["inst"].offz = newtile.floor_height

            if pack not in newtile.actors:
                newtile.actors.append(pack)

            inst.battle_moved = False

            o.max_actions += 1

            o.battle_selected_unit = pack

            o.battle_state = "select_move"

            o.battle_target_tiles = []

            self.build_battle_move_tiles(pack)

            #o.button_X_command = "Guardia"

            self.focus_battle_camera_on_current(pack)

            o.battle_cursor_x = o.battle_current_unit["gx"]
            o.battle_cursor_y = o.battle_current_unit["gy"]

            print("MOVE CANCELED")

            return

    def switch_x_command(self):

        o = self.owner

        pack = o.battle_current_unit

        if not pack:
            return

        inst = pack["inst"]

        # =====================================
        # SI NO SE MOVIO
        # =====================================

        if not inst.battle_moved:

            o.button_X_command = "Guardia"

            print(
                "X COMMAND:",
                o.button_X_command
            )

            return

        # =====================================
        # TOGGLE CANCELAR / GUARDIA
        # =====================================

        if o.button_X_command == "Cancelar":

            o.button_X_command = "Guardia"

        else:

            o.button_X_command = "Cancelar"

        print(
            "X COMMAND:",
            o.button_X_command
        )

    def cycle_battle_items(self):

        o = self.owner

        pack = o.battle_current_unit

        if not pack:
            return

        inst = pack["inst"]

        actor_def = o.actors.get(inst.actor_name)

        if not actor_def:
            return

        inventory = getattr(actor_def, "inventory", [])

        counter = Counter(inventory)

        o.item_menu = [
            f"{name} x{qty}"
            for name, qty in counter.items()
        ]

        o.item_menu_data = list(counter.keys())

        o.command_menu = inventory

        if not inventory:


            return

        inst.selected_item_index += 1

        if inst.selected_item_index >= len(inventory):
            inst.selected_item_index = 0

        item_name = inventory[inst.selected_item_index]

        # si el inventario guarda strings
        if item_name in o.items:

            item = o.items[item_name]

            quantity = inventory.count(item_name)

            #o.button_Y_command = f"{item.name} x{quantity}"

            print("ITEM:", item.name)


    def cycle_battle_specials(self):

        o = self.owner

        pack = o.battle_current_unit

        if not pack:
            return

        inst = pack["inst"]

        actor_def = o.actors.get(inst.actor_name)

        if not actor_def:
            return

        skills = getattr(actor_def, "skills", [])

        if not skills:

            #o.button_B_command = "Sin Especial"
            return

        inst.selected_special_index += 1

        if inst.selected_special_index >= len(skills):
            inst.selected_special_index = 0

        skill = skills[inst.selected_special_index]

        #o.button_B_command = skill

        print("SPECIAL:", skill)

    # =========================================================
    # TURNS
    # =========================================================

    def end_battle_turn(self):

        o = self.owner

        if not o.battle_units:
            return

        if not o.battle_turn_order:
            return

        if o.battle_turn_index >= len(o.battle_turn_order):
            o.battle_turn_index = 0

        current = o.battle_turn_order[o.battle_turn_index]

        if current:

            inst = current["inst"]

            inst.battle_moved = True
            inst.battle_acted = True

            current["origin_gx"] = current["gx"]
            current["origin_gy"] = current["gy"] 

        # =========================================
        # limpiar overlays
        # =========================================

        o.battle_move_tiles = []
        o.battle_target_tiles = []
        o.combat_path = []

        o.battle_selected_unit = None

        o.combat_actor_moving = False
        o.combat_move_queue = []
        o.combat_moving_unit = None

        self.attack_performed = False

        # =========================================
        # siguiente turno
        # =========================================

        o.battle_interact_event = False

        o.battle_turn_index += 1

        o.max_actions = 2

        if o.battle_turn_index >= len(o.battle_turn_order):

            o.battle_turn_index = 0

            for pack in o.battle_units:

                inst = pack["inst"]

                inst.battle_moved = False
                inst.battle_acted = False

        print("TURN END")

        self.begin_battle_turn()

    def begin_battle_turn(self):

        o = self.owner

        if o.game_over:
            return

        print("begin_battle_turn max_actions", o.max_actions)

        o.max_actions = 2
        o.current_action_type = "attack"

        if not o.battle_units:
            return

        if not o.play_mode:
            return

        if not o.battle_turn_order:
            return

        # Los muertos no deben tomar turno aunque sigan referenciados
        # temporalmente por una animacion o una accion en curso.
        skipped_dead = 0

        while o.battle_turn_order:

            if o.battle_turn_index >= len(o.battle_turn_order):
                o.battle_turn_index = 0

            current = o.battle_turn_order[o.battle_turn_index]
            inst = current["inst"]

            if not getattr(inst, "battle_dead", False):
                break

            o.battle_turn_order.pop(o.battle_turn_index)
            skipped_dead += 1

            if skipped_dead > len(o.battle_turn_order) + 1:
                return

        if not o.battle_turn_order:
            return

        o.battle_input_cooldown = 0.25

        o.selected_combat_action = None

        # =========================================
        # wrap turn index
        # =========================================

        if o.battle_turn_index >= len(o.battle_turn_order):
            o.battle_turn_index = 0

        if o.battle_turn_index < 0:
            o.battle_turn_index = 0

        # =========================================
        # unidad actual
        # =========================================

        o.battle_current_unit = (
            o.battle_turn_order[o.battle_turn_index]
        )

        if not o.battle_current_unit:
            return

        inst = o.battle_current_unit["inst"]

        if not hasattr(inst, "selected_item_index"):
            inst.selected_item_index = 0
        
        if not hasattr(inst, "selected_special_index"):
            inst.selected_special_index = 0

        # =========================================
        # RESET GUARD
        # =========================================

        inst.guard_mode = False

        inst.used_skill_this_turn = False
        inst.used_item_this_turn = False
        inst.battle_attacked = False

        print("TURN:", inst.actor_name)

        # =========================================
        # reset visuales
        # =========================================

        o.battle_move_tiles = []
        o.combat_path = []

        o.battle_selected_unit = None

        o.combat_actor_moving = False
        o.combat_move_queue = []
        o.combat_moving_unit = None

        # =========================================
        # mover cursor
        # =========================================

        o.battle_cursor_x = o.battle_current_unit["gx"]
        o.battle_cursor_y = o.battle_current_unit["gy"]

        # =========================================
        # camera
        # =========================================

        self.focus_battle_camera_on_current()

        self.turn_camera_lock = 0.45

        if inst.state != "idle":
            self.refesh_status(o.battle_current_unit)
            self.end_battle_turn()
            return
            

        # =========================================
        # IA
        # =========================================

        if inst.battle_team == "enemy":

            o.waiting_enemy_turn_start = True
            o.show_ui = False

        else:

            print("PLAYER TURN")

            o.battle_state = "idle"
            self.battle_camera_mode = 0
            o.show_ui = True
            o.button_A_command = "Seleccionar"
            o.button_X_command = "Menú"
            o.button_Y_command = ""
            o.button_B_command = "Cancelar"
            #o.button_X_command = "Menú"

            actor_def = o.actors.get(inst.actor_name)

            inventory = getattr(actor_def, "inventory", [])

            if inventory:

                idx = min(
                    inst.selected_item_index,
                    len(inventory) - 1
                )

            #o.button_Y_command = "Items"

            skills = getattr(actor_def, "skills", [])

            #o.button_B_command = "Especial"

        print(
            "CURRENT UNIT:",
            inst.actor_name,
            "TEAM:",
            inst.battle_team
        )


    def update_enemy_turn_start(self, dt):

        o = self.owner

        if o.game_over:
            return

        if not getattr(o, "waiting_enemy_turn_start", False):
            return

        self.turn_camera_lock -= dt

        if self.turn_camera_lock > 0:
            return

        o.waiting_enemy_turn_start = False

        self.run_enemy_turn()

    def run_enemy_turn(self):

        o = self.owner

        if o.game_over:
            return

        self.battle_camera_mode = 0

        print("ENEMY TURN")

        current = o.battle_current_unit

        if (
            not current
            or
            getattr(current["inst"], "battle_dead", False)
        ):
            self.end_battle_turn()
            return

        self.build_battle_move_tiles(current)

        closest_pack = IA.find_closest_enemy(self, current)

        if not closest_pack:
            if o.max_actions > 0:
                current["inst"].guard_mode = True
                self.play_runtime_idle(current["inst"])
            self.end_battle_turn()
            return

        best_tile = IA.find_best_tile_towards_target(
            self,
            current,
            closest_pack
        )

        if not best_tile:
            if o.max_actions > 0:
                current["inst"].guard_mode = True
                self.play_runtime_idle(current["inst"])
            self.end_battle_turn()
            return

        o.battle_selected_unit = current

        o.battle_cursor_x = current["gx"]
        o.battle_cursor_y = current["gy"]

        o.enemy_target_tile = best_tile

        o.enemy_ai_state = "move_cursor"

        #o.viewport.after(
         #   700,
          #  lambda: self.end_battle_turn()
        #)

    def get_unit_at(self, gx, gy):

        o = self.owner

        for unit in o.battle_units:

            if (
                unit["gx"] == gx
                and
                unit["gy"] == gy
            ):
                return unit

        return None

    # =========================================================
    # ATTACK RANGE
    # =========================================================

    # =========================================================
    # TARGET SHAPES
    # =========================================================

    def build_target_shape_diamond(
        self,
        startx,
        starty,
        action_range,
        allow_mantle=False,
        include_self=False
    ):

        o = self.owner

        tiles = []

        visited = set()

        queue = [
            (startx, starty, 0)
        ]

        while queue:

            x, y, d = queue.pop(0)

            if d > action_range:
                continue

            if (x, y) in visited:
                continue

            visited.add((x, y))

            if (
                x == startx
                and
                y == starty
            ):
                if include_self:
                    tiles.append((x, y))
            else:
                tiles.append((x, y))

            dirs = [
                (0, -1),
                (0, 1),
                (-1, 0),
                (1, 0)
            ]
            for dx, dy in dirs:

                nx = x + dx
                ny = y + dy

                if nx < 0 or ny < 0:
                    continue

                if nx >= GRID_W or ny >= GRID_H:
                    continue

                if (nx, ny) in visited:
                    continue

                if not self.combat_can_move_between(
                    x,
                    y,
                    nx,
                    ny,
                    allow_mantle=allow_mantle
                ):
                    continue

                h1 = self.combat_tile_height(x, y)
                h2 = self.combat_tile_height(nx, ny)

                diff = h2 - h1

                # subida que requiere mantle
                if allow_mantle and diff > 0.4:

                    visited.add((nx, ny))

                    if d + 1 <= action_range:
                        tiles.append((nx, ny))

                    # NO expandir desde esta tile
                    continue

                queue.append(
                    (nx, ny, d + 1)
                )
        return tiles


    # =========================================================
    # CROSS
    # =========================================================

    def build_target_shape_cross(
        self,
        startx,
        starty,
        action_range,
        allow_mantle=False,
        include_self=False
    ):

        tiles = []

        dirs = [
            (0, -1),
            (0, 1),
            (-1, 0),
            (1, 0)
        ]

        for dx, dy in dirs:

            px = startx
            py = starty

            for i in range(action_range):

                nx = px + dx
                ny = py + dy

                if nx < 0 or ny < 0:
                    break

                if nx >= GRID_W or ny >= GRID_H:
                    break

                if not self.combat_can_move_between(
                    px,
                    py,
                    nx,
                    ny,
                    allow_mantle=allow_mantle
                ):
                    break

                if (
                    nx == startx
                    and
                    ny == starty
                ):
                    if include_self:
                        tiles.append((nx, ny))
                else:

                    tiles.append((nx, ny))

                if self.combat_tile_blocked(nx, ny):
                    break

                px = nx
                py = ny

                

        return tiles


    # =========================================================
    # LINE
    # solo hacia donde mira la unidad
    # =========================================================

    def build_target_shape_line(
        self,
        pack,
        action_range,
        allow_mantle=False,
        include_self=False
    ):

        tiles = []

        inst = pack["inst"]

        startx = pack["gx"]
        starty = pack["gy"]

        face = getattr(
            inst,
            "visual_facing",
            "frente"
        )

        dirmap = {
            "frente": (0, 1),
            "espalda": (0, -1),
            "dere": (1, 0),
            "izq": (-1, 0)
        }

        dx, dy = dirmap.get(
            face,
            (0, 1)
        )

        px = startx
        py = starty

        for i in range(action_range):

            nx = px + dx
            ny = py + dy

            if nx < 0 or ny < 0:
                break

            if nx >= GRID_W or ny >= GRID_H:
                break

            if not self.combat_can_move_between(
                px,
                py,
                nx,
                ny,
                allow_mantle=allow_mantle
            ):
                break

            if (
                nx == startx
                and
                ny == starty
                ):
                if include_self:
                    tiles.append((nx, ny))
                else:
                    tiles.append((nx, ny))

            px = nx
            py = ny

        return tiles


    # =========================================================
    # SQUARE
    # =========================================================

    def build_target_shape_square(
        self,
        startx,
        starty,
        action_range,
        include_self=False
    ):

        tiles = []

        for y in range(
            starty - action_range,
            starty + action_range + 1
        ):

            for x in range(
                startx - action_range,
                startx + action_range + 1
            ):

                if x < 0 or y < 0:
                    continue

                if x >= GRID_W or y >= GRID_H:
                    continue

                if (
                    x == startx
                    and
                    y == starty
                ):
                    continue

                tiles.append((x, y))

        return tiles


    # =========================================================
    # RING
    # =========================================================

    def build_target_shape_ring(
        self,
        startx,
        starty,
        action_range,
        include_self=False
    ):

        tiles = []

        for y in range(
            starty - action_range,
            starty + action_range + 1
        ):

            for x in range(
                startx - action_range,
                startx + action_range + 1
            ):

                if x < 0 or y < 0:
                    continue

                if x >= GRID_W or y >= GRID_H:
                    continue

                dist = abs(x - startx) + abs(y - starty)

                if dist != action_range:
                    continue

                tiles.append((x, y))

        return tiles


    # =========================================================
    # CONE
    # =========================================================

    def build_target_shape_cone(
        self,
        pack,
        action_range,
        include_self=False
    ):

        tiles = []

        inst = pack["inst"]

        startx = pack["gx"]
        starty = pack["gy"]

        face = getattr(
            inst,
            "visual_facing",
            "frente"
        )

        if face == "frente":

            for d in range(1, action_range + 1):

                y = starty + d

                for xoff in range(-d, d + 1):

                    x = startx + xoff

                    if (
                        0 <= x < GRID_W
                        and
                        0 <= y < GRID_H
                    ):
                        tiles.append((x, y))

        elif face == "espalda":

            for d in range(1, action_range + 1):

                y = starty - d

                for xoff in range(-d, d + 1):

                    x = startx + xoff

                    if (
                        0 <= x < GRID_W
                        and
                        0 <= y < GRID_H
                    ):
                        tiles.append((x, y))

        elif face == "dere":

            for d in range(1, action_range + 1):

                x = startx + d

                for yoff in range(-d, d + 1):

                    y = starty + yoff

                    if (
                        0 <= x < GRID_W
                        and
                        0 <= y < GRID_H
                    ):
                        tiles.append((x, y))

        elif face == "izq":

            for d in range(1, action_range + 1):

                x = startx - d

                for yoff in range(-d, d + 1):

                    y = starty + yoff

                    if (
                        0 <= x < GRID_W
                        and
                        0 <= y < GRID_H
                    ):
                        tiles.append((x, y))

        return tiles

    def build_battle_target_tiles(self, pack):

        o = self.owner

        o.battle_target_tiles = []

        allow_mantle = False

        if not pack:
            return

        inst = pack["inst"]

        if inst.actor_name not in o.actors:
            return

        actor_def = o.actors[inst.actor_name]

        # =========================================
        # DEFAULTS
        # =========================================

        action_range = 1
        include_self = False

        shape = "diamond"
        action_data = None

        target_type = "enemy"

        # =========================================
        # NORMAL ATTACK
        # =========================================

        if o.current_action_type == "attack":

            weapon_name = getattr(
                actor_def,
                "weapon",
                ""
            )

            weapon = o.weapons.get(
                weapon_name
            )

            if weapon:
                
                action_range = weapon.range
                shape = weapon.target_shape
                
                if weapon and weapon.use_bullets:

                    if not self.has_ammo(
                        inst.actor_name,
                        weapon.ammo_item,
                        weapon.ammo_per_shot
                    ):
                        ammo = False
                        print("OUT OF AMMO")
                        action_range = getattr(
                            actor_def,
                            "attack_range",
                            1
                        )

                        shape = "diamond"
                        

            else:

                action_range = getattr(
                    actor_def,
                    "attack_range",
                    1
                )

                shape = "diamond"

        # =========================================
        # SKILL / ITEM
        # =========================================

        else:

            action_data = o.selected_combat_action

            if not action_data:
                return

            action_range = getattr(
                action_data,
                "range",
                1
            )

            action_name = getattr(
                action_data,
                "name",
                ""
            )

            if o.current_action_type == "skill":

                target_type = self.get_skill_value(
                    action_data,
                    "target_type",
                    "enemy"
                )

                script = self.get_skill_value(
                action_data,
                "script",
                []
                )

                print("SKILL SCRIPT:", script)

            else:
                target_type = self.get_item_value(
                    action_data,
                    "target_type",
                    "enemy"
                )

                script = self.get_item_value(
                action_data,
                "script",
                []
                )

                print("ITEM SCRIPT:", script)


            if target_type in ["self", "ally"]:
                include_self = True
                

            shape = getattr(
                action_data,
                "target_shape",
                "diamond"
            )

            if action_name == "Trepar":
                allow_mantle = True

        # =========================================
        # SHAPES
        # =========================================

        startx = pack["gx"]
        starty = pack["gy"]

        if shape == "diamond":

            o.battle_target_tiles = (
                self.build_target_shape_diamond(
                    startx,
                    starty,
                    action_range,
                    allow_mantle,
                    include_self=include_self
                )
            )

        elif shape == "cross":

            o.battle_target_tiles = (
                self.build_target_shape_cross(
                    startx,
                    starty,
                    action_range,
                    allow_mantle,
                    include_self=include_self
                )
            )

        elif shape == "line":

            o.battle_target_tiles = (
                self.build_target_shape_line(
                    pack,
                    action_range,
                    allow_mantle,
                    include_self=include_self
                )
            )

        elif shape == "square":

            o.battle_target_tiles = (
                self.build_target_shape_square(
                    startx,
                    starty,
                    action_range,
                    include_self=include_self
                )
            )

        elif shape == "ring":

            o.battle_target_tiles = (
                self.build_target_shape_ring(
                    startx,
                    starty,
                    action_range,
                    include_self=include_self
                )
            )

        elif shape == "cone":

            o.battle_target_tiles = (
                self.build_target_shape_cone(
                    pack,
                    action_range,
                    include_self=include_self
                )
            )

        # =====================================
        # AUTO CURSOR POSITION
        # =====================================

        ux = pack["gx"]
        uy = pack["gy"]

        target = IA.find_attack_target(
            self,
            pack
        )

        if include_self:
            target = pack

        if not target:

            print("NO TARGET IN RANGE")
            if(inst.battle_team == "enemy"):
                self.pending_turn_end = True
                self.turn_end_timer = 0.9

                o.enemy_ai_state = "end_turn"

            else:

                for tx, ty in o.battle_target_tiles:

                    if not include_self:

                        if tx == ux and ty == uy:
                            continue

                    o.battle_cursor_x = tx
                    o.battle_cursor_y = ty
                    break
            return

        # =====================================
        # FOUND TARGET
        # =====================================

        else:

            o.battle_cursor_x = target["gx"]
            o.battle_cursor_y = target["gy"]

        
        if(inst.battle_team == "enemy"):
    
            o.enemy_ai_attack_target = target
            o.enemy_ai_state = "confirm_attack"
            o.battle_move_tiles = []

        #if not target_type == "enemy" and not inst.battle_team  == "enemy":



        o.battle_target_unit = target

        o.battle_cursor_x = target["gx"]
        o.battle_cursor_y = target["gy"]

        print(
                "TARGET FOUND:",
                target["inst"].actor_name
        )

    def get_skill_value(self,skill, key, default=None):

        if isinstance(skill, dict):
            return skill.get(key, default)

        return getattr(skill, key, default)
    
    def get_item_value(self,item, key, default=None):

        if isinstance(item, dict):
            return item.get(key, default)

        return getattr(item, key, default)
    
    # =========================================================
    # MOVE RANGE
    # =========================================================

    def build_battle_move_tiles(self, pack):

        o = self.owner

        o.battle_move_tiles = []

        inst = pack["inst"]

        if inst.actor_name not in o.actors:
            return

        actor_def = o.actors[inst.actor_name]

        move_range = getattr(actor_def, "move_range", 4)

        allow_mantle = self.actor_can_mantle(pack)

        startx = pack["gx"]
        starty = pack["gy"]

        visited = set()

        queue = [
            (startx, starty, 0)
        ]

        while queue:

            x, y, d = queue.pop(0)

            if d > move_range:
                continue

            if (x, y) in visited:
                continue

            visited.add((x, y))

            o.battle_move_tiles.append((x, y))

            dirs = [
                (0, -1),
                (0, 1),
                (-1, 0),
                (1, 0)
            ]

            for dx, dy in dirs:

                nx = x + dx
                ny = y + dy

                if not self.combat_can_move_between(
                    x,
                    y,
                    nx,
                    ny,
                    allow_mantle=allow_mantle
                ):
                    continue

                if nx < 0 or ny < 0:
                    continue

                if nx >= GRID_W or ny >= GRID_H:
                    continue

                if (nx, ny) in visited:
                    continue

                if self.combat_tile_blocked(nx, ny, pack):
                    continue
                

                queue.append((nx, ny, d + 1))

    # =========================================================
    # COLLISION
    # =========================================================

    def combat_target_blocked(
        self,
        gx,
        gy,
        ignore_pack=None
    ):

        o = self.owner

        t = o.runtime_world.grid[gy][gx]

        for pack in getattr(t, "actors", []):

            if pack == ignore_pack:
                continue

            inst = pack["inst"]

            if getattr(inst, "battle_dead", False):
                continue

            return True

        return False

    def combat_tile_blocked(
        self,
        gx,
        gy,
        ignore_pack=None
    ):

        o = self.owner

        px = gx + 0.5
        py = gy + 0.5

        # geometría
        cur_h = self.combat_tile_height(gx, gy)

        if o.runtime_actor.runtime_collides(
            px,
            py,
            cur_h,
            radius=0.28
        ):
            return True

        # actores
        t = o.runtime_world.grid[gy][gx]

        for pack in getattr(t, "actors", []):

            if pack == ignore_pack:
                continue

            inst = pack["inst"]

            if getattr(inst, "battle_dead", False):
                continue

            return True

        return False

    # =========================================================
    # CAMERA
    # =========================================================

    def update_battle_camera(self, dt):

        o = self.owner

        if not o.play_mode:
            return

        if not o.battle_mode:
            return
        
        if o.runtime_cam_orbit is None:
            o.runtime_cam_orbit = 0

        if hasattr(o, "game_view"):
            cam = o.game_view.game_camera
        else:
            cam = o.viewport.camera

        if self.turn_camera_lock > 0:
            self.turn_camera_lock -= dt

        if o.runtime_camera_locked:

            cam.yaw = o.runtime_cam_orbit

            return

        # =========================================
        # ROTACION CAMARA
        # =========================================

        rot_speed = 80 * dt

        if o.battle_current_unit:

            inst = o.battle_current_unit["inst"]

            if inst.rot_l:
                o.runtime_cam_orbit -= rot_speed

            if inst.rot_r:
                o.runtime_cam_orbit += rot_speed

        if o.battle_current_unit:

            inst = o.battle_current_unit["inst"]

            if inst.rot_l or inst.rot_r:
                o.update_battle_unit_facings()

        # =========================================
        # FOLLOW
        # =========================================

        # =========================================
        # CAMERA TARGET
        # =========================================

        target_x = cam.x
        target_z = cam.z
        target_y = 0.0
        

        # =========================================
        # ATTACK CAMERA
        # =========================================

        if self.runtime_attack_camera:

            target_y = 0.0

        # =========================================
        # FOLLOW MOVING UNIT
        # =========================================

        elif o.combat_actor_moving and o.combat_moving_unit:

            pack = o.combat_moving_unit
            inst = pack["inst"]

            target_x = (
                pack["gx"] + inst.offx + 0.5
            )

            target_z = (
                pack["gy"] + inst.offy + 0.5
            )

            target_y = self.combat_tile_height(
                pack["gx"],
                pack["gy"]
            )

        # =========================================
        # FOLLOW CURSOR WHILE SELECTING MOVE
        # =========================================

        elif o.battle_state == "select_move" or o.battle_state == "select_target":

            target_x = (
                o.battle_cursor_x + 0.5
            )

            target_z = (
                o.battle_cursor_y + 0.5
            )

        elif o.battle_state == "idle":

            # =========================================
            # DURANTE TRANSICION DE TURNO
            # =========================================

            if self.turn_camera_lock > 0:

                if o.battle_current_unit:

                    pack = o.battle_current_unit

                    target_x = pack["gx"] + 0.5
                    target_z = pack["gy"] + 0.5
                    

            # =========================================
            # FOLLOW CURSOR
            # =========================================

            else:

                target_x = o.battle_cursor_x + 0.5
                target_z = o.battle_cursor_y + 0.5

        # =========================================
        # DEFAULT: CURRENT UNIT
        # =========================================

        elif o.battle_current_unit:

            pack = o.battle_current_unit

            target_x = pack["gx"] + 0.5
            target_z = pack["gy"] + 0.5
            target_y = self.combat_tile_height(
                pack["gx"],
                pack["gy"]
            )

        speed = 5.0

        cam.x += (target_x - cam.x) * min(1.0, dt * speed)
        cam.z += (target_z - cam.z) * min(1.0, dt * speed)
        cam.y += (
            target_y - cam.y
        ) * min(1.0, dt * speed)

        ground_y = target_y


        # =========================================
        # CAMERA PRESETS
        # =========================================

        if self.battle_camera_mode == 0:

            # tactical
            preset = o.camera_presets["battle_tactical"]
            #preset = CAMERA_PRESETS["battle_tactical"]

            cam.y = preset["y"] + ground_y

            target_pitch = preset["pitch"]
            target_dist  = preset["distance"]
            cam.pitch += (target_pitch - cam.pitch) * dt * 6
            cam.distance += (target_dist - cam.distance) * dt * 6

        else:

            # close camera
            #preset = CAMERA_PRESETS["battle_close"]
            preset = o.camera_presets["battle_close"]

            cam.y = preset["y"] + ground_y

            target_pitch = preset["pitch"]
            target_dist  = preset["distance"]
            cam.pitch += (target_pitch - cam.pitch) * dt * 6
            cam.distance += (target_dist - cam.distance) * dt * 6

        if self.runtime_attack_camera:

            current = o.runtime_cam_orbit % 360
            target = self.runtime_attack_cam_target % 360

            diff = (target - current + 180) % 360 - 180

            o.runtime_cam_orbit = (
                current + diff * min(1, dt * 6)
            ) % 360

            if abs(diff) < 1:

                o.runtime_cam_orbit = (
                    self.runtime_attack_cam_target
                )

                self.runtime_attack_camera = False

                runtime_skill = self.active_runtime_skill

                if runtime_skill:

                    runtime_skill.flags[
                        "camera_finished"
                    ] = True

                    return

                if self.charge_attack_camera:

                    self.charge_attack_camera = False

                    print("CHARGE CAMERA FINISHED")

                    return

                inst = self.attack_anim_inst

                inst_target = self.damage_anim_inst

                # =========================================
                # ATTACK ANIMATION
                # =========================================

                if self.attack_result_type == "critical":

                    attack_anim = (
                        "attack_dereX2"
                        if self.attack_anim_side == "dere"
                        else "attack_izqX2"
                    )

                elif self.attack_result_type == "miss":

                    attack_anim = (
                        "miss_hit_fall_sitdown_dere"
                        if self.attack_anim_side == "dere"
                        else "miss_hit_fall_sitdown_izq"
                    )

                else:

                    attack_anim = (
                        "attack_dere"
                        if self.attack_anim_side == "dere"
                        else "attack_izq"
                    )

                # =========================================
                # DAMAGE / REACTION ANIMATION
                # =========================================

                if self.attack_result_type == "critical":

                    damage_anim = (
                        "hit_fall_sitdown_izq"
                        if self.attack_anim_side == "dere"
                        else "hit_fall_sitdown_dere"
                    )

                elif self.attack_result_type == "miss":

                    damage_anim = (
                        "dodge_izq"
                        if self.attack_anim_side == "dere"
                        else "dodge_dere"
                    )

                else:

                    if getattr(inst_target, "battle_dead", False):
                        damage_anim = (
                        "hit_fall_face_up_izq"
                        if self.attack_anim_side == "dere"
                        else "hit_fall_face_up_dere"
                        )

                    else:
                        damage_anim = (
                            "hit_izq"
                            if self.attack_anim_side == "dere"
                            else "hit_dere"
                        )

                if attack_anim in inst.animator.clips:
                    inst.animator.play(attack_anim)

                if damage_anim in inst_target.animator.clips:
                    inst_target.animator.play(damage_anim)

                self.performing_attack = True

        # ORBITAL
        if not o.runtime_camera_locked:
            cam.yaw = o.runtime_cam_orbit

    def runtime_skill_attack_camera(
    self,
    runtime_skill
    ):

        user_pack = runtime_skill.user_pack
        target_pack = runtime_skill.target_pack

        self.attack_anim_inst = (
            user_pack["inst"]
        )

        self.damage_anim_inst = (
            target_pack["inst"]
        )

        self.start_attack_camera(
            user_pack,
            target_pack
        )

    def focus_battle_camera_on_current(self, pack=None):

        o = self.owner

        if pack is None:

            pack = o.battle_current_unit

        if not pack:
            return

        if not o.battle_current_unit:
            return

        o.battle_cam_target_x = pack["gx"] + 0.5
        o.battle_cam_target_z = pack["gy"] + 0.5

        print(
            "BATTLE CAMERA TARGET:",
            o.battle_cam_target_x,
            o.battle_cam_target_z
        )

    def start_attack_camera(
        self,
        attacker_pack,
        target_pack
    ):

        o = self.owner

        attacker = attacker_pack["inst"]
        target = target_pack["inst"]

        ax = attacker_pack["gx"] + attacker.offx
        ay = attacker_pack["gy"] + attacker.offy

        tx = target_pack["gx"] + target.offx
        ty = target_pack["gy"] + target.offy

        dx = tx - ax
        dy = ty - ay

        print(
            "ATTACKER H",
            self.combat_tile_height(
                attacker_pack["gx"],
                attacker_pack["gy"]
            )
        )

        print(
            "TARGET H",
            self.combat_tile_height(
                target_pack["gx"],
                target_pack["gy"]
            )
        )

        # =====================================
        # YAWS DE PERFIL
        # =====================================

        ang = math.degrees(
            math.atan2(dx, dy)
        )

        yaw_a = (ang - 90) % 360
        yaw_b = (ang + 90) % 360

        # =====================================
        # LADO ANIMACION
        # =====================================

        side_a = "dere"
        side_b = "izq"

        # =====================================
        # ELEGIR PERFIL MAS CERCANO
        # =====================================

        current = o.runtime_cam_orbit % 360

        def angle_dist(a, b):
            return abs(
                ((a - b + 180) % 360) - 180
            )

        dist_a = angle_dist(current, yaw_a)
        dist_b = angle_dist(current, yaw_b)

        if dist_a <= dist_b:

            yaw_candidates = [
                (yaw_a, side_a),
                (yaw_b, side_b)
            ]

        else:

            yaw_candidates = [
                (yaw_b, side_b),
                (yaw_a, side_a)
            ]

        # =====================================
        # ELEGIR PRIMER ANGULO LIBRE
        # =====================================

        best_yaw = yaw_candidates[0][0]
        best_side = yaw_candidates[0][1]

        for yaw, side in yaw_candidates:

            blocked = self.attack_camera_blocked(
                yaw,
                attacker_pack,
                target_pack
            )

            if not blocked:

                best_yaw = yaw
                best_side = side
                break

        # =====================================
        # INIT CAMERA
        # =====================================

        self.attack_anim_side = best_side

        self.runtime_attack_cam_target = (
            best_yaw % 360
        )

        self.runtime_attack_camera = True
    
    def remove_dead_unit_from_turn_order(self, pack):

        o = self.owner

        if not pack:
            return

        if pack not in o.battle_turn_order:
            return

        removed_index = o.battle_turn_order.index(pack)

        o.battle_turn_order.remove(pack)

        if removed_index < o.battle_turn_index:
            o.battle_turn_index -= 1

        if o.battle_turn_order:

            if o.battle_turn_index >= len(o.battle_turn_order):
                o.battle_turn_index = 0

        else:

            o.battle_turn_index = 0

    def finalize_pending_dead_unit(self, pack):

        if not pack:
            return

        inst = pack["inst"]

        if not getattr(inst, "pending_remove", False):
            return

        if not getattr(inst, "battle_dead", False):
            return

        self.remove_battle_unit(pack)

    def remove_battle_unit(self, pack):

        o = self.owner

        if pack not in o.battle_units:
            return

        # índice antes de remover
        removed_index = -1

        if pack in o.battle_turn_order:
            removed_index = o.battle_turn_order.index(pack)

        # remover del tile
        tile = o.runtime_world.grid[
            pack["gy"]
        ][
            pack["gx"]
        ]

        if pack in tile.actors:
            tile.actors.remove(pack)

        inst = pack["inst"]

        main_dead = False

        is_main = getattr(
        o.actors[inst.actor_name],
        "is_main",
        False
        )

        print ("IS MAIN?", str(is_main))

        if is_main and getattr(inst, "battle_dead", False):
            main_dead = True

        # remover listas
        if pack in o.battle_units:
            o.battle_units.remove(pack)

        if pack in o.battle_turn_order:
            o.battle_turn_order.remove(pack)

        enemy_alive = False
        player_alive = False

        for p in o.battle_units:

            inst = p["inst"]

            print ("IS MAIN?", str(is_main))

            if getattr(inst, "battle_dead", False):
                continue

            if inst.battle_team == "enemy":
                enemy_alive = True

            if inst.battle_team in ["player", "ally"]:
                player_alive = True

        if not enemy_alive:

            print("VICTORY DETECTED")

            self.combat_result = "win"

            o.start_fade_out(
                self.finish_combat_fade
            )

            return
        
        if not player_alive or main_dead:

            print("GAME OVER")

            self.combat_result = "lose"

            o.game_over = True

            o.start_fade_out(
                self.finish_combat_fade
            )

            return

        # ajustar turn index
        if removed_index != -1:

            if removed_index < o.battle_turn_index:
                o.battle_turn_index -= 1

            if o.battle_turn_index >= len(o.battle_turn_order):
                o.battle_turn_index = 0
        
    def update_combat_end(self, dt):

        if self.combat_end_state == "fade_out":

            if self.owner.screen_fade_alpha >= 1.0:

                self.remove_party_members()

                self.end_runtime_combat()

                self.owner.start_fade_in(1.0)

                self.combat_end_state = "fade_in"

        elif self.combat_end_state == "fade_in":

            if self.owner.screen_fade_alpha <= 0:

                self.combat_end_state = None

    def remove_party_members(self):

        o = self.owner

        print("REMOVE PARTY FROM BATTLE UNITS")

        leader = o.runtime_world.main_actor

        remove_list = []

        for pack in o.battle_units:

            pack["inst"].guard_mode = False

            if pack == leader:
                continue

            if pack["inst"].battle_team == "enemy":
                continue

            remove_list.append(pack)

        for pack in remove_list:

            print(
                "REMOVING",
                pack["inst"].actor_name
            )

            tile = o.runtime_world.grid[
                pack["gy"]
            ][
                pack["gx"]
            ]

            if pack in tile.actors:
                tile.actors.remove(pack)

    def finish_combat_fade(self):

        print("FINISH COMBAT FADE")

        o = self.owner

        self.remove_party_members()

        result = getattr(
            self,
            "combat_result",
            None
        )

        scripts = getattr(
            o,
            "combat_result_scripts",
            {}
        )

        script = scripts.get(result)

        self.end_runtime_combat()

        if script:

            print(
                "EXECUTING COMBAT SCRIPT:",
                script
            )

            manager = get_runtime_scene_manager(self)
            manager.change_world_scene(o, script)

            self.combat_result = None
            o.combat_result_scripts = {}

            return

        #if o.game_over:
         #   return

        #o.start_fade_in()
        
    def end_runtime_combat(self):

        print("END RUNTIME COMBAT")

        o = self.owner

        combat_music = getattr(
            o,
            "current_combat_music",
            None
        )

        current_music = getattr(
            o,
            "current_music",
            None
        )

        music_to_stop = combat_music or current_music

        if music_to_stop and hasattr(o, "audio_manager"):
            o.audio_manager.stop(
                music_to_stop,
                fade_ms=1000
            )

        o.current_music = None
        o.current_combat_music = None

        o.battle_mode = False

        o.pending_combat_enemy = False

        o.battle_units = []
        o.battle_turn_order = []

        o.battle_selected_unit = None
        o.battle_current_unit = None

        o.battle_move_tiles = []
        o.battle_target_tiles = []

        o.combat_actor_moving = False

        o.combat_move_queue = []
        o.combat_moving_unit = None

        o.battle_state = "idle"

        self.performing_attack = False
        self.runtime_attack_camera = False

        o.button_A_command = "Interactuar"
        o.button_X_command = "Menú"
        o.button_Y_command = ""
        o.button_B_command = "Cancelar"
        o.battle_mode = False

        # =====================================
        # RESET FLAGS
        # =====================================

        self.reset_runtime_actor_motion(force_idle=True)

        print("COMBAT END")

    def reset_runtime_actor_motion(self, force_idle=False):

        o = self.owner

        if not getattr(o, "runtime_world", None):
            return

        for row in o.runtime_world.grid:
            for t in row:
                for pack in getattr(t, "actors", []):

                    inst = pack["inst"]

                    # Las teclas soltadas durante combate no pasan por el
                    # runtime de exploracion. Si alguna bandera queda viva,
                    # al volver al mundo se sigue eligiendo walk aunque el
                    # actor ya este detenido.
                    inst.move_f = False
                    inst.move_b = False
                    inst.move_l = False
                    inst.move_r = False
                    inst.rot_l = False
                    inst.rot_r = False
                    inst.world_move_queue = []
                    inst.is_world_moving = False

                    inst.is_battle_moving = False
                    inst.battle_dead = False
                    inst.pending_remove = False
                    inst.battle_moved = False
                    inst.battle_acted = False

                    if force_idle:
                        self.play_runtime_idle(inst)

    def play_runtime_idle(self, inst):

        if hasattr(self.owner, "play_runtime_actor_idle"):
            self.owner.play_runtime_actor_idle(inst)


    # =========================================================
    # UNIT MOVEMENT
    # =========================================================

    def combat_animation_finished(self):

        return (
            not self.performing_attack
            and
            not self.runtime_attack_camera
        )


    def show_popup(
    self,
    target_pack,
    result, counter = False
    ):

        if "popup_text" in result:

            self.spawn_combat_popup(
                target_pack,
                result["popup_text"],
                color=result.get(
                    "popup_color",
                    (1,1,1,1)
                ),
                lifetime=0.5,
                offset_y=10
            )

            return
        
        damage = result["damage"]

        offset_x = 100

        #side = self.attack_anim_side


        if result["critical_hit"]:

            self.spawn_combat_popup(
                target_pack,
                "CRITICAL! " + str(damage),
                color=(1,0.2,0.2,1),
                lifetime=0.5,
                offset_y=10,
                scale=2.5,
                offset_x=offset_x
            )

        elif counter:
            self.spawn_combat_popup(
            target_pack,
            target_pack["inst"].actor_name
            + " COUNTER!",
            color=(1,0.2,0.2,1),
            lifetime=0.5,
            offset_y=10,
            offset_x=offset_x
        )

        elif not result["hit"]:

            self.spawn_combat_popup(
                target_pack,
                "MISS",
                lifetime=0.5,
                color=(0.8,0.8,0.8,1),
                offset_x=offset_x + 30
            )

        else:

            self.spawn_combat_popup(
                target_pack,
                "HIT! " + str(damage),
                color=(1,0.2,0.2,1),
                lifetime=0.5,
                offset_y=10,
                offset_x=offset_x
            )                    

    def combat_tile_height(self, gx, gy):

        o = self.owner

        t = o.runtime_world.grid[gy][gx]

        if getattr(t, "is_block", False):
            return t.block_top

        return t.floor_height   
    
    def combat_can_move_between(
        self,
        x1,
        y1,
        x2,
        y2,
        allow_mantle=False
    ):

        h1 = self.combat_tile_height(x1, y1)
        h2 = self.combat_tile_height(x2, y2)

        diff = h2 - h1

        # misma altura o escalon chico
        if diff <= 0.4:
            return True

        # subida alta requiere mantle
        if allow_mantle and diff <= 2.0:
            return True

        return 
    
    def attack_camera_blocked(
        self,
        yaw,
        user_pack,
        target_pack
    ):

        o = self.owner

        ux = user_pack["gx"] + 0.5
        uy = user_pack["gy"] + 0.5

        tx = target_pack["gx"] + 0.5
        ty = target_pack["gy"] + 0.5

        midx = (ux + tx) * 0.5
        midy = (uy + ty) * 0.5

        rad = math.radians(yaw)

        camx = midx + math.sin(rad) * 4
        camy = midy + math.cos(rad) * 4

        steps = 16

        for i in range(steps):

            t = i / steps

            sx = camx + (midx - camx) * t
            sy = camy + (midy - camy) * t

            gx = int(sx)
            gy = int(sy)

            if gx < 0 or gy < 0:
                continue

            if gx >= GRID_W or gy >= GRID_H:
                continue

            tile = o.runtime_world.grid[gy][gx]

            if getattr(tile, "is_block", False):

                if tile.block_top > 1.0:
                    return True

        return False
    

    def spawn_combat_popup(
        self,
        pack,
        text,
        color=(1,1,1,1),
        lifetime=1.5,
        rise_speed=40,
        offset_y=0,
        scale=1,
        offset_x=0
    ):

        popup = {
            "pack": pack,
            "text": text,
            "color": color,
            "time": lifetime,
            "max_time": lifetime,
            "rise_speed": rise_speed,
            "offset_y": offset_y,
            "offset_x": offset_x,
            "scale": scale

        }

        self.combat_text_popups.append(popup)

    def update_combat_popups(self, dt):

        alive = []

        for p in self.combat_text_popups:

            p["time"] -= dt

            if p["time"] <= 0:
                continue

            p["offset_y"] -= p["rise_speed"] * dt

            alive.append(p)

        self.combat_text_popups = alive


    def update_battle_animations(self, dt):

        o = self.owner

        if not o.battle_mode:
            return

        for pack in o.battle_units:

            inst = pack["inst"]

            if not inst.animator:
                continue

            inst.animator.update(dt)

    def actor_can_mantle(self, pack):

        inst = pack["inst"]

        actor_def = self.owner.actors.get(
            inst.actor_name
        )

        if not actor_def:
            return False

        for skill_name in getattr(actor_def, "skills", []):

            skill = self.owner.skills.get(skill_name)

            if not skill:
                continue

            if skill.name == "Trepar":
                return True

        return False

    def update_combat_actor_move(self, dt):
        from EventManager import get_near_event_cell

        o = self.owner

        if not o.play_mode:
            return

        if not o.combat_actor_moving:
            return

        pack = o.combat_moving_unit

        if not pack:
            o.combat_actor_moving = False
            return

        inst = pack["inst"]


        if getattr(inst, "is_mantling", False):
            if pack["inst"].is_mantling:
                o.runtime_actor.update_actor_mantle(pack, dt)
            return
        
        # =====================================
        # FIN MOVIMIENTO
        # =====================================

        if not o.combat_move_queue:

            # =====================================
            # MANTLE ARRIVAL
            # =====================================

            is_mantle = getattr(
                inst,
                "combat_using_mantle",
                False
            )

            # ya terminó el mantle real
            if is_mantle:

                # todavía no arrancó mantle
                if not getattr(inst, "mantle_started", False):

                    inst.mantle_started = True

                    self.finish_mantle_skill()

                    return

                # mantle sigue ejecutándose
                if inst.is_mantling:
                    return

                # mantle terminó completamente

                o.combat_actor_moving = False
                o.combat_moving_unit = None

                inst.mantle_started = False

                self.complete_mantle_skill()

                o.combat_actor_moving = False
                o.combat_moving_unit = None

                user_pack = self.mantle_skill_user

                #o.button_X_command = "Guardia"
                self.battle_camera_mode = 0

                self.focus_battle_camera_on_current(user_pack)

                o.battle_cursor_x = o.battle_current_unit["gx"]
                o.battle_cursor_y = o.battle_current_unit["gy"]

                self.mantle_skill_user = None

                return
            
            # =====================================
            # CHARGE SKILL
            # =====================================

            runtime_skill = self.active_runtime_skill

            # =====================================
            # MOVEMENT FROM RUNTIME SKILL
            # =====================================

            if runtime_skill:

                o.combat_actor_moving = False

                runtime_skill.flags["move_finished"] = True

                print("RUNTIME SKILL MOVE FINISHED")

                return

            
            o.combat_actor_moving = False
            runtime_skill = self.active_runtime_skill

            if runtime_skill:

                runtime_skill.flags[
                    "move_finished"
                ] = True

            o.max_actions-=1

            print ("max_actions " + str(o.max_actions))
            
            if(o.max_actions > 0):
                # volver a seleccionar unidad
                o.battle_selected_unit = o.combat_moving_unit

                #o.button_A_command = "Atacar"

                o.command_menu = self.build_unit_command_menu(o.battle_selected_unit)

                o.menu_index = 0
                o.battle_state = "command_menu"

                #o.current_action_type = "attack"

                #self.switch_x_command()

                o.combat_moving_unit = None

            # FIN TURNO
            else:

                o.battle_selected_unit = None
                o.battle_state = "idle"

                self.end_battle_turn()

            if getattr(inst, "charge_running", False):
                    print("charge_running update movimiento")
                    return

            face = getattr(
                inst,
                "visual_facing",
                "espalda"
            )

            if not inst.guard_mode:

                idlemap = {
                    "frente": "idle_frente",
                    "espalda": "idle_espalda",
                    "dere": "idle_perfil_dere",
                    "izq": "idle_perfil_izq"
                }

                idle_anim = idlemap.get(
                    face,
                    "idle_espalda"
                )

            else:
                idlemap = {
                    "frente": "idle_guard_frente",
                    "espalda": "idle_guard_espalda",
                    "dere": "idle_guard_perfil_dere",
                    "izq": "idle_guard_perfil_izq"
                }

                idle_anim = idlemap.get(
                    face,
                    "idle_guard_espalda"
                )

            if (
                inst.animator and
                idle_anim in inst.animator.clips
            ):
                inst.animator.play(idle_anim)

            return

        # =====================================
        # TILE TARGET
        # =====================================

        tx, ty = o.combat_move_queue[0]

        next_h = self.combat_tile_height(tx, ty)

        cur_h = self.combat_tile_height(
            pack["gx"],
            pack["gy"]
        )

        diff = next_h - cur_h

        if (
            diff > 0.4
            and
            self.actor_can_mantle(pack)
        ):

            started = o.runtime_actor.try_start_mantle(
                pack,
                tx - pack["gx"],
                ty - pack["gy"]
            )

            if started:
                o.combat_move_queue.pop(0)
                return

        speed = 3.5

        dx = tx - (pack["gx"] + inst.offx)
        dy = ty - (pack["gy"] + inst.offy)

        dist = math.sqrt(dx * dx + dy * dy)

        # =====================================
        # WALK ANIMATION
        # =====================================

        if abs(dx) > 0.001 or abs(dy) > 0.001:

            if hasattr(o, "game_view"):
                cam = o.game_view.game_camera
            else:
                cam = o.viewport.camera

            cam_ang = math.radians(cam.yaw)

            forward_x = math.sin(cam_ang)
            forward_y = math.cos(cam_ang)

            right_x = math.sin(cam_ang + math.pi / 2)
            right_y = math.cos(cam_ang + math.pi / 2)

            fdot = dx * forward_x + dy * forward_y
            rdot = dx * right_x + dy * right_y

            is_charge = getattr(
                inst,
                "charge_running",
                False
            )
            # =====================================
            # WALK NORMAL
            # =====================================         

            if is_charge:

                side = getattr(
                    self,
                    "attack_anim_side",
                    "dere"
                )

                if side == "dere":

                    chosen = "run_perfil_dere"
                    face = "dere"
                    self.attack_anim_side = "dere"

                else:

                    chosen = "run_perfil_izq"
                    face = "izq"
                    self.attack_anim_side = "izq"

            else:

                if abs(fdot) >= abs(rdot):

                    if fdot >= 0:
                        chosen = "walk_frente"
                        face = "frente"
                    else:
                        chosen = "walk_espalda"
                        face = "espalda"

                else:

                    if rdot >= 0:
                        chosen = "walk_perfil_dere"
                        face = "dere"
                    else:
                        chosen = "walk_perfil_izq"
                        face = "izq"

            inst.visual_facing = face

            if inst.animator:

                if inst.animator.current != chosen:

                    if chosen in inst.animator.clips:
                        inst.animator.play(chosen)

                inst.animator.update(dt)

        # =====================================
        # LLEGADA A TILE
        # =====================================

        if dist < 0.05:

            inst.battle_moved = True

            if not getattr(inst, "charge_running", False):

                if "idle" in inst.animator.clips:
                    inst.animator.play("idle")

            oldtile = o.runtime_world.grid[
                pack["gy"]
            ][
                pack["gx"]
            ]

            if pack in oldtile.actors:
                oldtile.actors.remove(pack)

            pack["gx"] = tx
            pack["gy"] = ty
            new_h = self.combat_tile_height(tx, ty)

            inst.offz = new_h
            inst.ground_z = new_h

            inst.offx = 0
            inst.offy = 0

            newtile = o.runtime_world.grid[ty][tx]

            if pack not in newtile.actors:
                newtile.actors.append(pack)

            o.combat_move_queue.pop(0)

            return

        # =====================================
        # MOVIMIENTO
        # =====================================

        inst.offx += (dx / dist) * speed * dt
        inst.offy += (dy / dist) * speed * dt
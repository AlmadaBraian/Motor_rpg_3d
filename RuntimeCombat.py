import math
from collections import deque

import IA
import Skills
from config import GRID_H, GRID_W
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
        self.performing_damage = False
        self.attack_performed = False
        self.attack_anim_side = "izq"
        self.counter_attack = False
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
        self.last_attack_result = None
        self.last_attack_attacker = None
        self.last_attack_target = None
        self.counter_attack_in_progress = False
        self.counter_attack_used = False
        self.current_attack_is_counter = False
        self.actual_damage = 0
        self.combat_text_popups = []

    # =========================================================
    # START COMBAT
    # =========================================================

    def start_runtime_combat(self, enemy_id=""):

        o = self.owner

        if o.battle_mode:
            return
        
        if o.runtime_cam_orbit is None:
            o.runtime_cam_orbit = 0
        
        self.previous_camera_orbit = o.runtime_cam_orbit

        o.battle_mode = True

        o.battle_units = []

        o.combat_move_tiles = []
        o.combat_path = []

        o.combat_actor_moving = False
        o.combat_move_queue = []

        o.battle_input_cooldown = 0

        o.battle_cam_target_x = 0
        o.battle_cam_target_z = 0
        o.battle_cam_active = True
        self.battle_camera_mode = 0

        o.button_A_command = "Seleccionar"
        o.button_X_command = "Guardia"
        o.button_Y_command = "Items"
        o.button_B_command = "Especial"

        # =====================================
        # PARTY
        # =====================================

        for row in o.runtime_world.grid:
            for t in row:
                for pack in getattr(t, "actors", []):

                    inst = pack["inst"]

                    if inst.actor_name not in o.actors:
                        continue

                    actor_def = o.actors[inst.actor_name]

                    team = getattr(actor_def, "team", "npc")

                    # MAIN ACTOR SIEMPRE PLAYER
                    if pack == o.runtime_world.main_actor:
                        team = "player"

                    elif team == "main":
                        team = "player"

                    elif team == "party":
                        team = "player"

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

        # =====================================
        # BUILD TURN ORDER
        # =====================================

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

            inst.battle_initiative = base_init + roll + speed

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

        # =====================================
        # START TURN
        # =====================================

        o.battle_turn_index = 0

        self.begin_battle_turn()

        print("TACTICAL COMBAT START")
        

    # =========================================================
    # PATHFINDING
    # =========================================================

    def build_combat_path(self, sx, sy, tx, ty):

        o = self.owner

        grid = o.runtime_world.grid

        

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
                    ny
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

        o = self.owner

        if not o.battle_selected_unit:
            return

        target = None

        if o.battle_state == "select_target":
                        
            if not o.battle_target_tiles:

                self.build_battle_target_tiles(
                            o.battle_selected_unit
                )

        for pack in o.battle_units:

            if (
                pack["gx"] == o.battle_cursor_x
                and
                pack["gy"] == o.battle_cursor_y
            ):
                target = pack
                break

        if not target:
            print("NO TARGET")

            o.battle_target_tiles = []

            self.build_battle_move_tiles(
                o.battle_selected_unit
            )
            return

        inst = o.battle_selected_unit["inst"]

        print("selected_combat_action " + str(o.selected_combat_action))

        self.execute_combat_action(
            o.battle_selected_unit,
            target,
            o.selected_combat_action
        )

        inst.used_item_this_turn = True
        

    def confirm_selected_skill(self):

        print("selected_skill")

        o = self.owner

        if o.battle_state != "select_target":
            return

        user_pack = o.battle_selected_unit

        if not user_pack:
            return

        action_data = o.selected_combat_action

        if not action_data:
            return

        script = getattr(
            action_data,
            "script",
            ""
        ).strip()

        # =====================================
        # TILE TARGET SKILLS
        # =====================================

        if script == "mantle_skill":

            target = (
                o.battle_cursor_x,
                o.battle_cursor_y
            )

        # =====================================
        # NORMAL ACTOR TARGET
        # =====================================

        else:

            target = None

            for pack in o.battle_units:

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

            target_type = getattr(
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
            target,
            action_data
        )

        inst = user_pack["inst"]

        inst.used_skill_this_turn = True

    # =========================================================
    # INPUT
    # =========================================================

    def handle_battle_input(self, event):

        o = self.owner

        if o.battle_input_cooldown > 0:
            return
        
        if self.performing_attack:
            return

        if self.runtime_attack_camera:
            return

        k = event.keysym.lower()

        # =====================================
        # CURSOR MOVEMENT
        # =====================================

        mx = 0
        my = 0

        if k == "w":
            my = -1

        if k == "s":
            my = 1

        if k == "a":
            mx = -1

        if k == "d":
            mx = 1

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

            self.execute_x_command()
            o.battle_input_cooldown = 0.12
            return

        if event.keysym == "z":

            # =====================================
            # ENTER ITEM MODE
            # =====================================

            if o.battle_state in [
                "select_move",
                "select_target"
            ]:

                o.battle_move_tiles = []

                self.use_selected_item()

                return

        if event.keysym == "c":
            o.battle_input_cooldown = 0.25

            if o.battle_state in [
                "select_move",
                "select_target"
            ]:
                o.battle_move_tiles = []
                o.battle_target_tiles = []
                self.cycle_battle_specials()

                self.use_selected_skill()
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
        # CHANGE BATTLE MODE
        # =====================================

        if event.keysym == "Down":

            o.battle_input_cooldown = 0.25
            self.switch_attack_move()

        elif event.keysym == "Left":

            o.battle_input_cooldown = 0.25
            self.switch_x_command()

        elif event.keysym == "Up":

            o.battle_input_cooldown = 0.25

            self.cycle_battle_items()

            if o.battle_state == "select_item":

                self.use_selected_item()

        elif event.keysym == "Right":

            o.battle_input_cooldown = 0.25
            self.cycle_battle_specials()
            self.use_selected_skill()

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

            if o.max_actions <= 0:
                    o.battle_selected_unit = None

                    o.battle_move_tiles = []
                    o.battle_target_tiles = []

                    o.battle_state = "idle"

                    self.end_battle_turn()

            # =====================================
            # SELECT UNIT
            # =====================================

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

                        # SOLO CAMBIA ESTADO
                        o.battle_state = "select_move"

                        o.button_A_command = "Mover a"

                        o.current_action_type = "move"

                        if not o.battle_move_tiles:

                            self.build_battle_move_tiles(
                                o.battle_selected_unit
                            )

                        print("UNIT SELECTED")

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

                if o.battle_state == "select_item":

                    self.confirm_item_target()
                    return
                
                if o.battle_state == "select_target":

                    if o.current_action_type == "skill":
                        
                        self.confirm_selected_skill()

                    else:
                        tx = o.battle_cursor_x
                        ty = o.battle_cursor_y
                        target = None

                        for pack in o.battle_units:

                            if pack["gx"] == tx and pack["gy"] == ty:
                                target = pack
                                break

                        if target:
                            o.battle_attacker_unit = o.battle_selected_unit
                            self.attack_performed = True
                            #self.perform_attack(target)
                            self.execute_combat_action( o.battle_attacker_unit,target)
                            #inst.battle_acted = True
                            
                        print ("max_actions " + str(o.max_actions))
                        return

                    return
                
    def enter_attack_mode(self):

        o = self.owner

        if not o.battle_selected_unit:
            return

        o.current_action_type = "attack"

        o.battle_state = "select_target"

        o.battle_move_tiles = []

        self.build_battle_target_tiles(
            o.battle_selected_unit
        )

        o.button_A_command = "Atacar"

                
    def execute_combat_action(
        self,
        user_pack,
        target_pack,
        action_data=None
    ):

        o = self.owner
        print("execute_combat_action")

        user = user_pack["inst"]
        target = None

        # =====================================
        # TARGET UNIT
        # =====================================

        if isinstance(target_pack, dict):

            target = target_pack["inst"]
            o.battle_target_unit = target_pack


        # =====================================
        # TARGET TILE
        # =====================================

        elif isinstance(target_pack, tuple):

            tx, ty = target_pack

        if o.current_action_type == "attack":

            print("attack por execute_conbat_action")

            if not target_pack:
                return

            o.battle_attacker_unit = user_pack

            self.attack_performed = True

            self.perform_attack(
                user_pack,
                target_pack,
                is_counter=self.counter_attack
            )

            return

        anim = getattr(
            action_data,
            "animation",
            ""
        )

        script = getattr(
            action_data,
            "script",
            ""
        ).strip()

        if target:

            print(
                user.actor_name,
                "uses",
                getattr(action_data, "name", "Unknown"),
                "on",
                target.actor_name
            )

        else:

            print(
                user.actor_name,
                "uses",
                getattr(action_data, "name", "Unknown"),
                "on tile",
                target_pack
            )

        if o.current_action_type == "item":

            actor_def = o.actors.get(user.actor_name)

            if actor_def:

                inventory = getattr(
                    actor_def,
                    "inventory",
                    []
                )

                item_name = action_data.name

                # remover una sola unidad
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
                    o.button_Y_command = f"{item_name} x{inventory.count(item_name)}"

        print("excecute_effect por excecute_combat_action")

        if not action_data:

            print(
                "ERROR: effect_data is None",
                user_pack["inst"].actor_name
            )

            return

        result = self.execute_effect(
            user_pack,
            target_pack,
            action_data
        )

        if result == "async":
            return

        o.max_actions -= 1

        o.battle_target_tiles = []
        o.selected_combat_action = None
        o.current_action_type = "attack"

        if o.max_actions <= 0:

            self.end_battle_turn()

        else:
            inst = o.battle_selected_unit["inst"]

            if inst.battle_moved:
                return

            o.battle_state = "select_move"

            o.button_A_command = "Mover a"

            if o.battle_selected_unit:

                self.build_battle_move_tiles(
                    o.battle_selected_unit
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

            if combat_result["critical_miss"]:

                self.attack_result_type = "critical_miss"
                print("CRITICAL MISS!")
                
            else:
                print("MISS")

            # no aplicar daño
            return False

        damage = combat_result["damage"]

        if not hasattr(target, "hp"):

            target.hp = 10

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

        # =========================================
        # BODY TYPE
        # =========================================

        body_type_tgt = getattr(tgt_def, "body_type", "normal")
        body_type_atk = getattr(atk_def, "body_type", "normal")

        body_type_tgt_bonus = o.body_type_list[body_type_tgt]
        body_type_atk_bonus = o.body_type_list[body_type_atk]

        # =========================================
        # STATS
        # =========================================

        speed_bonus = 1

        if getattr(atk_def, "speed", 0) > 4:
            speed_bonus = 1.25

        attack_bonus = getattr(atk_def, "attack_bonus", 0) * speed_bonus

        armor_class = getattr(tgt_def, "armor_class", 10)
        armor_class *= body_type_tgt_bonus

        if getattr(target, "guard_mode", False):
            armor_class += 4

        # =========================================
        # ROLL
        # =========================================

        roll = random.randint(1, 20)

        total_attack = roll + attack_bonus

        critical_hit = False
        critical_miss = False

        if roll == 20:
            hit = True
            critical_hit = True

        elif roll == 1:
            hit = False
            critical_miss = True

        else:
            hit = total_attack >= armor_class

        # =========================================
        # DAMAGE
        # =========================================

        damage = 0

        if hit:

            dmg_min = getattr(atk_def, "damage_min", 1)
            dmg_max = getattr(atk_def, "damage_max", 6)

            if critical_hit:
                dmg_max *= 2
                #dmg_max -= 2

            print("dmg_max", dmg_max)

            base_damage = random.randint(dmg_min, dmg_max)
            base_damage *= body_type_atk_bonus

            print("base_damage", base_damage)

            defense = getattr(tgt_def, "defense", 0)
            #defense *= body_type_tgt_bonus

            damage = max(
                1,
                round(base_damage + attack_bonus - defense)
            )

            if getattr(target, "guard_mode", False):

                damage *= 0.5
                damage = max(1, round(damage))

        return {
            "hit": hit,
            "critical_hit": critical_hit,
            "critical_miss": critical_miss,
            "damage": damage,
            "roll": roll,
            "attack_total": total_attack,
            "armor_class": armor_class
        }
                
    def use_selected_item(self):

        o = self.owner

        pack = o.battle_selected_unit

        if not pack:
            return

        inst = pack["inst"]

        if inst.used_item_this_turn:
            print("ITEM ALREADY USED")
            return

        actor_def = o.actors.get(inst.actor_name)

        if not actor_def:
            return

        inventory = getattr(actor_def, "inventory", [])

        if not inventory:

            o.button_Y_command = "Sin Items"

            if not inst.battle_moved:

                o.current_action_type = "move"

                o.battle_state = "select_move"

                o.battle_target_tiles = []

                self.build_battle_move_tiles(
                    o.battle_selected_unit
                )

                o.button_A_command = "Mover a"

            return

        # =====================================
        # SI NUNCA ELIGIO ITEM
        # =====================================

        if inst.selected_item_index >= len(inventory):

            inst.selected_item_index = 0

        item_name = inventory[
            inst.selected_item_index
        ]

        quantity = inventory.count(item_name)

        print(
            "ITEM:",
            item_name,
            "X ",
            quantity
        )

        if item_name not in o.items:
            return
        
        

        item = o.items[item_name]

        o.selected_combat_action = item

        o.current_action_type = "item"

        o.battle_state = "select_item"

        o.battle_move_tiles = []

        self.build_battle_target_tiles(pack)

        print(
            "TARGET TILES:",
            len(o.battle_target_tiles)
        )

        o.button_Y_command = f"{item.name} x{quantity}"

        o.button_A_command = "Seleccionar"

        print("SELECT ITEM:", item.name)
    
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

                o.current_action_type = "move"

                o.battle_state = "select_move"

                o.battle_target_tiles = []

                self.build_battle_move_tiles(
                    o.battle_selected_unit
                )

                o.button_A_command = "Mover a"
            return

        o.selected_combat_action = skill_data

        o.battle_move_tiles = []

        self.build_battle_target_tiles(
            pack
        )

        o.battle_selected_unit = pack

        o.battle_state = "select_target"

        o.button_B_command = skill_data.name

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
        
        if event.keysym == "space":
            tkref.space_pressed = False

    def execute_x_command(self):

        o = self.owner

        pack = o.battle_current_unit

        if not pack:
            return

        inst = pack["inst"]

        # =====================================
        # CANCELAR MOVIMIENTO
        # =====================================

        if o.button_X_command == "Cancelar":

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

            if pack not in newtile.actors:
                newtile.actors.append(pack)

            inst.battle_moved = False

            o.max_actions += 1

            o.battle_selected_unit = pack

            o.battle_state = "select_move"

            o.battle_target_tiles = []

            self.build_battle_move_tiles(pack)

            o.button_X_command = "Guardia"

            self.focus_battle_camera_on_current(pack)

            o.battle_cursor_x = o.battle_current_unit["gx"]
            o.battle_cursor_y = o.battle_current_unit["gy"]

            print("MOVE CANCELED")

            return

        # =====================================
        # GUARD
        # =====================================

        else:

            print("GUARD")

            inst.guard_mode = True

            self.end_battle_turn()

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

        if not inventory:

            o.button_Y_command = "Sin Items"
            return

        inst.selected_item_index += 1

        if inst.selected_item_index >= len(inventory):
            inst.selected_item_index = 0

        item_name = inventory[inst.selected_item_index]

        # si el inventario guarda strings
        if item_name in o.items:

            item = o.items[item_name]

            quantity = inventory.count(item_name)

            o.button_Y_command = f"{item.name} x{quantity}"

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

            o.button_B_command = "Sin Especial"
            return

        inst.selected_special_index += 1

        if inst.selected_special_index >= len(skills):
            inst.selected_special_index = 0

        skill = skills[inst.selected_special_index]

        o.button_B_command = skill

        print("SPECIAL:", skill)

    # =========================================================
    # TURNS
    # =========================================================

    def end_battle_turn(self):

        o = self.owner

        if not o.battle_units:
            return

        current = o.battle_turn_order[o.battle_turn_index]

        if current:

            inst = current["inst"]

            inst.battle_moved = True
            inst.battle_acted = True

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

        o.battle_turn_index += 1

        o.max_actions = 2

        if o.battle_turn_index >= len(o.battle_turn_order):

            o.battle_turn_index = 0

            for pack in o.battle_units:

                inst = pack["inst"]

                inst.battle_moved = False
                inst.battle_acted = False

        self.begin_battle_turn()

        print("TURN END")

    def begin_battle_turn(self):

        o = self.owner

        print("begin_battle_turn max_actions", o.max_actions)

        o.max_actions = 2
        o.current_action_type = "attack"

        if not o.battle_units:
            return

        if not o.play_mode:
            return

        o.battle_input_cooldown = 0.25

        o.selected_combat_action = None

        self.counter_attack = False

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

        # =========================================
        # IA
        # =========================================

        if inst.battle_team == "enemy":

            o.waiting_enemy_turn_start = True

        else:

            print("PLAYER TURN")

            o.battle_state = "idle"
            self.battle_camera_mode = 1
            o.show_ui = True
            o.button_A_command = "Seleccionar"
            o.button_X_command = "Guardia"

            actor_def = o.actors.get(inst.actor_name)

            inventory = getattr(actor_def, "inventory", [])

            if inventory:

                idx = min(
                    inst.selected_item_index,
                    len(inventory) - 1
                )

            o.button_Y_command = "Items"

            skills = getattr(actor_def, "skills", [])

            o.button_B_command = "Especial"

        print(
            "CURRENT UNIT:",
            inst.actor_name,
            "TEAM:",
            inst.battle_team
        )

    def execute_effect(self, user_pack, target_pack, effect_data):

        attacker = user_pack["inst"]

        o = self.owner
        print("execute_effect")

        effect_type = effect_data.effect_type

        print(str(effect_type))

        # =====================================
        # TARGET ACTOR
        # =====================================

        target = None
        actor_def_target = None

        if isinstance(target_pack, dict):

            target = target_pack["inst"]

            actor_def_target = o.actors.get(
                target.actor_name
            )

        actor_def_user = o.actors.get(
            attacker.actor_name
        )

        if o.current_action_type == "skill":
            actor_def = o.actors.get(attacker.actor_name)

            if actor_def:

                skills = getattr(
                    actor_def,
                    "skills",
                    []
                )

                skill_name = effect_data.name

                if skill_name in skills:

                    cost = actor_def.sp - effect_data.sp_cost

                    print("cost " + str(cost))

                    if cost >=0:

                        actor_def.sp = cost

                        print(
                            "CONSUMED:",
                            str(effect_data.sp_cost)
                        )

                        print(
                            "LEFT:",
                            str(actor_def.sp)
                        )
                        o.button_B_command = skill_name
                    
                    else:
                        print("Falta sp para realizar la accion")
                        if attacker.battle_moved:
                            return

                        o.battle_state = "select_move"

                        o.button_A_command = "Mover a"

                        if o.battle_selected_unit:

                            self.build_battle_move_tiles(
                                o.battle_selected_unit
                            )
                        return

        script = getattr(
            effect_data,
            "script",
            ""
        ).strip()

        if effect_type == "damage":

            result = self.calculate_combat_result(
                user_pack,
                target_pack,
                effect_data
            )

            #result["damage"] *= 2
            if script == "charge_attack":

                Skills.execute_charge_attack(
                    self,
                    user_pack,
                    target_pack,
                    effect_data
                )

                return "async"

            self.apply_damage(
                user_pack,
                target_pack,
                result
            )

        elif effect_type == "heal":

            actor_def_target.hp += effect_data.power

            if actor_def_target.hp > actor_def_target.max_hp:
                actor_def_target.hp = actor_def_target.max_hp

            print(str(target.actor_name) +  " recupero " + str(effect_data.power) + " de hp." )
            print("Salud actual " + str(actor_def_target.hp))

        elif effect_type == "move":
            if script == "mantle_skill":


                Skills.execute_mantle_skill(
                    self,
                    user_pack,
                    target_pack,
                    effect_data
                )

                return "async"



        elif effect_type == "buff_attack":

            actor_def_target.atk += effect_data.power

        elif effect_type == "revive":

            if actor_def_target.hp <= 0:
                actor_def_target.hp = effect_data.power

    def update_enemy_turn_start(self, dt):

        o = self.owner

        if not getattr(o, "waiting_enemy_turn_start", False):
            return

        self.turn_camera_lock -= dt

        if self.turn_camera_lock > 0:
            return

        o.waiting_enemy_turn_start = False

        self.run_enemy_turn()

    def run_enemy_turn(self):

        o = self.owner

        self.battle_camera_mode = 1

        print("ENEMY TURN")

        current = o.battle_current_unit

        self.build_battle_move_tiles(current)

        closest_pack = IA.find_closest_enemy(self, current)

        best_tile = IA.find_best_tile_towards_target(
            self,
            current,
            closest_pack
        )

        if not best_tile:
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
        allow_mantle=False
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

            if not (
                x == startx
                and
                y == starty
            ):
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
        allow_mantle=False
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

                tiles.append((nx, ny))

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
        allow_mantle=False
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
        action_range
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
        action_range
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
        action_range
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

        # =========================================
        # NORMAL ATTACK
        # =========================================

        if o.current_action_type == "attack":

            action_range = getattr(
                actor_def,
                "attack_range",
                1
            )

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

            target_type = getattr(
                action_data,
                "target_type",
                "enemy"
            )

            script = getattr(
                action_data,
                "script",
                ""
            ).strip()

            shape = getattr(
                action_data,
                "target_shape",
                "diamond"
            )

            if script == "mantle_skill":
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
                    allow_mantle
                )
            )

        elif shape == "cross":

            o.battle_target_tiles = (
                self.build_target_shape_cross(
                    startx,
                    starty,
                    action_range,
                    allow_mantle
                )
            )

        elif shape == "line":

            o.battle_target_tiles = (
                self.build_target_shape_line(
                    pack,
                    action_range,
                    allow_mantle
                )
            )

        elif shape == "square":

            o.battle_target_tiles = (
                self.build_target_shape_square(
                    startx,
                    starty,
                    action_range
                )
            )

        elif shape == "ring":

            o.battle_target_tiles = (
                self.build_target_shape_ring(
                    startx,
                    starty,
                    action_range
                )
            )

        elif shape == "cone":

            o.battle_target_tiles = (
                self.build_target_shape_cone(
                    pack,
                    action_range
                )
            )
    
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
                    ny
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

        if o.runtime_collides(
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
        target_y = cam.y

        # =========================================
        # ATTACK CAMERA
        # =========================================

        if self.runtime_attack_camera:

            pass

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


        # =========================================
        # CAMERA PRESETS
        # =========================================

        if self.battle_camera_mode == 0:

            # tactical
            cam.y = 0
            target_pitch = 55
            target_dist = 18
            cam.pitch += (target_pitch - cam.pitch) * dt * 6
            cam.distance += (target_dist - cam.distance) * dt * 6

        else:

            # close camera
            cam.y = 1
            target_pitch = 20
            target_dist = 6
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
                self.performing_damage = True

        # ORBITAL
        cam.yaw = o.runtime_cam_orbit

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

    def perform_attack(self,attacker_pack,target_pack, is_counter=False):

        o = self.owner
        self.current_attack_is_counter = is_counter

        if not is_counter:
            self.pending_counter_attack = None
            self.counter_attack_used = False

        if not attacker_pack or not target_pack:
            return False

        attacker = attacker_pack["inst"]
        target = target_pack["inst"]

        self.attack_anim_inst = attacker
        self.damage_anim_inst = target

        self.attack_result_type = "normal"

        self.start_attack_camera(
            attacker_pack,
            target_pack
        )

        result = self.calculate_combat_result(
            attacker_pack,
            target_pack
        )

        if not result:

            self.counter_attack = False
            return False
        
        if result["critical_hit"]:
            self.attack_result_type = "critical"

        elif not result["hit"]:
            self.attack_result_type = "miss"

        else:
            self.attack_result_type = "normal"
        
        self.last_attack_result = result
        self.last_attack_attacker = attacker_pack
        self.last_attack_target = target_pack

        print("result", result)

        self.apply_damage(
            attacker_pack,
            target_pack,
            result
        )

        o.battle_attack_tiles = []
        o.battle_move_tiles = []

        return True
    
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

        # remover listas
        if pack in o.battle_units:
            o.battle_units.remove(pack)

        if pack in o.battle_turn_order:
            o.battle_turn_order.remove(pack)

        # ajustar turn index
        if removed_index != -1:

            if removed_index < o.battle_turn_index:
                o.battle_turn_index -= 1

            if o.battle_turn_index >= len(o.battle_turn_order):
                o.battle_turn_index = 0

        enemy_alive = False
        player_alive = False

        for p in o.battle_units:

            inst = p["inst"]

            if getattr(inst, "battle_dead", False):
                continue

            if inst.battle_team == "enemy":
                enemy_alive = True

            if inst.battle_team in ["player", "ally"]:
                player_alive = True

        if not enemy_alive:

            print("PLAYER WIN")

            self.end_runtime_combat()

            return
        
        if not player_alive:

            print("GAME OVER")

            self.end_runtime_combat()

            return
        
    def end_runtime_combat(self):

        o = self.owner

        o.battle_mode = False

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
        self.performing_damage = False
        self.runtime_attack_camera = False

        o.button_A_command = "Interactuar"
        o.button_X_command = "Guardia"
        o.button_Y_command = "Items"
        o.button_B_command = "Especial"

        # =====================================
        # RESET FLAGS
        # =====================================

        for row in o.runtime_world.grid:
            for t in row:
                for pack in getattr(t, "actors", []):

                    inst = pack["inst"]

                    inst.is_battle_moving = False
                    inst.battle_dead = False
                    inst.pending_remove = False
                    inst.battle_moved = False
                    inst.battle_acted = False

        print("COMBAT END")


    # =========================================================
    # UNIT MOVEMENT
    # =========================================================

    def combat_animation_finished(self):

        return (
            not self.performing_attack
            and
            not self.performing_damage
            and
            not self.runtime_attack_camera
        )

    def update_combat_actor_damage(self, dt):

        o = self.owner

        if not o.play_mode:
            return

        if not self.performing_damage:
            return

        inst = self.damage_anim_inst

        if not inst:
            self.performing_damage = False
            return

        if not inst.animator:
            self.performing_damage = False
            return

        # actualizar animacion
        inst.animator.update(dt)

        # terminó
        if inst.animator.finished:

            self.performing_damage = False

            if getattr(inst, "pending_remove", False):

                pack_to_remove = None

                for pack in o.battle_units:

                    if pack["inst"] == inst:
                        pack_to_remove = pack
                        break

                if pack_to_remove:

                    tile = o.runtime_world.grid[
                        pack_to_remove["gy"]
                    ][
                        pack_to_remove["gx"]
                    ]

                    self.remove_battle_unit(pack_to_remove)

                inst.pending_remove = False

            if self.attack_result_type == "critical":
                idle_anim = (
                        "hit_fall_face_up_izq"
                        if self.attack_anim_side == "dere"
                        else "hit_fall_face_up_dere"
                    )
                
            elif inst.battle_dead:
                idle_anim = (
                        "hit_fall_face_up_izq"
                        if self.attack_anim_side == "dere"
                        else "hit_fall_face_up_dere"
                    )
                
            elif inst.guard_mode:
                idle_anim = (
                        "idle_guard_izq"
                        if self.attack_anim_side == "dere"
                        else "idle_guard_dere"
                    )
                
            else:

                # volver a idle
                idle_anim = (
                    "idle_izq"
                    if self.attack_anim_side == "dere"
                    else "idle_dere"
                )

            if idle_anim in inst.animator.clips:
                inst.animator.play(idle_anim)

            result = self.last_attack_result

            # =========================================
            # PREPARAR COUNTER
            # =========================================

            if (
                not result["hit"]
                and
                not self.current_attack_is_counter
                and
                not self.counter_attack_used
            ):

                self.counter_attack_used = True

                self.attack_result_type = "counter_attack"

                atk_pack = self.last_attack_attacker
                tgt_pack = self.last_attack_target

                atk_def = o.actors.get(
                    atk_pack["inst"].actor_name
                )

                tgt_def = o.actors.get(
                    tgt_pack["inst"].actor_name
                )
                #COUNTER ATTACK

                atk_speed = getattr(atk_def, "speed", 5)
                tgt_speed = getattr(tgt_def, "speed", 5)

                atk_init = getattr(
                    atk_pack["inst"],
                    "battle_initiative",
                    0
                )

                tgt_init = getattr(
                    tgt_pack["inst"],
                    "battle_initiative",
                    0
                )

                can_counter = False

                # target mas rapido
                if tgt_speed > atk_speed:
                    can_counter = True

                # empate de velocidad
                elif tgt_speed == atk_speed:

                    # desempate por iniciativa
                    if tgt_init > atk_init:
                        can_counter = True

                if can_counter:

                    print(
                        tgt_pack["inst"].actor_name,
                        "COUNTER ATTACK!"
                    )

                    self.pending_counter_attack = (
                        tgt_pack,
                        atk_pack
                    )

            # =========================================
            # FINALIZAR O EJECUTAR COUNTER
            # =========================================

            self.try_finish_attack_sequence()
                
           

    def finalize_combat_action(self):

        o = self.owner

        o.max_actions -= 1

        o.battle_target_tiles = []
        o.selected_combat_action = None
        o.current_action_type = "attack"

        if o.max_actions <= 0:

            o.battle_selected_unit = None
            o.battle_state = "idle"

            self.end_battle_turn()

        else:

            o.battle_state = "select_move"

            o.button_A_command = "Mover a"

            o.current_action_type = "select move"

            if o.battle_selected_unit:
                self.build_battle_move_tiles(
                    o.battle_selected_unit
                )


    def update_combat_actor_attack(self, dt):

        o = self.owner

        if not o.play_mode:
            return

        if not self.performing_attack:
            return

        inst = self.attack_anim_inst

        if not inst:
            self.performing_attack = False
            return

        if not inst.animator:
            self.performing_attack = False
            return

        # actualizar animacion
        inst.animator.update(dt)

        is_charge = getattr(
                inst,
                "charge_running",
                False
            )
        
        if is_charge:
            print("charge_running update_combat_actor_attack")
            return
        
        if self.attack_result_type == "counter_attack":

                self.spawn_combat_popup(
                            o.battle_selected_unit,
                            "COUNTER ATTACK!",
                            color=(1,0.2,0.2,1),
                            lifetime=0.5,
                            offset_y = 10,
                            offset_x = -10
                        )
                self.attack_result_type = ""
                
        elif self.attack_result_type == "normal":

                self.spawn_combat_popup(
                                o.battle_selected_unit,
                                "HIT! " + str(self.actual_damage),
                                color=(1,0.2,0.2,1),
                                lifetime=0.5,
                                offset_y = 10,
                                offset_x = -10,
                            )
                
        elif self.attack_result_type == "critical":

                self.spawn_combat_popup(
                                o.battle_selected_unit,
                                "CRITICAL! " + str(self.actual_damage),
                                color=(1,0.2,0.2,1),
                                lifetime=0.5,
                                offset_y = 10,
                                offset_x = -10,
                                scale=2.5
                            )

                
        elif self.attack_result_type == "miss":
                
                self.spawn_combat_popup(
                    o.battle_selected_unit,
                    "MISS",
                    lifetime=0.5,
                    color=(0.8,0.8,0.8,1),
                    offset_x = -10
                )
        
        # terminó
        if inst.animator.finished:

            self.performing_attack = False

            if self.attack_result_type == "miss":
                
                idle_anim = (
                        "sitdown_dere"
                        if self.attack_anim_side == "dere"
                        else "sitdown_izq"
                    )
                
            else:     
                # volver a idle
                idle_anim = (
                    "idle_dere"
                    if self.attack_anim_side == "dere"
                    else "idle_izq"
                )

            if idle_anim in inst.animator.clips:
                inst.animator.play(idle_anim)

            self.try_finish_attack_sequence()

    def try_finish_attack_sequence(self):

        if not self.combat_animation_finished():
            return
        
        o = self.owner

        # =====================================
        # COUNTER ATTACK
        # =====================================

        if self.pending_counter_attack:

            atk, tgt = self.pending_counter_attack

            self.pending_counter_attack = None

            self.perform_attack(
                atk,
                tgt,
                is_counter=True
            )

            return

        # =====================================
        # FIN NORMAL
        # =====================================

        self.finalize_combat_action()
                            

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
        if allow_mantle and diff <= 2.5:
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
        scale=2,
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

    def draw_combat_popups(self):

        o = self.owner

        for p in self.combat_text_popups:

            pack = p["pack"]

            inst = pack["inst"]

            scale = p["scale"]

            wx = pack["gx"] + inst.offx
            wy = inst.ground_z + 2.0
            wz = pack["gy"] + inst.offy

            screen = o.viewport.world_to_screen(wx, wy, wz)

            if not screen:
                continue

            sx, sy = screen

            alpha = p["time"] / p["max_time"]

            color = (
                p["color"][0],
                p["color"][1],
                p["color"][2],
                alpha
            )

            o.viewport.draw_ui_text(
                p["text"],
                sx + p["offset_x"],
                sy + p["offset_y"],
                color=color,
                centered=True,
                scale=scale
            )

    def update_combat_actor_move(self, dt):

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
                o.update_actor_mantle(pack, dt)
            return
        
        # =====================================
        # FIN MOVIMIENTO
        # =====================================

        if not o.combat_move_queue:

            # =====================================
            # CHARGE SKILL
            # =====================================

            if getattr(inst, "charge_running", False):

                o.combat_actor_moving = False
                o.combat_moving_unit = None

                print("CHARGE MOVE FINISHED")

                return

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

                    Skills.finish_mantle_skill(self)

                    return

                # mantle sigue ejecutándose
                if inst.is_mantling:
                    return

                # mantle terminó completamente

                o.combat_actor_moving = False
                o.combat_moving_unit = None

                inst.mantle_started = False

                Skills.complete_mantle_skill(self)

                o.combat_actor_moving = False
                o.combat_moving_unit = None

                user_pack = self.mantle_skill_user

                o.battle_target_tiles = []

                if user_pack:
                    self.build_battle_target_tiles(user_pack)

                o.battle_state = "select_target"

                o.button_X_command = "Guardia"

                self.focus_battle_camera_on_current(user_pack)

                o.battle_cursor_x = o.battle_current_unit["gx"]
                o.battle_cursor_y = o.battle_current_unit["gy"]

                self.mantle_skill_user = None

                return

            
            o.combat_actor_moving = False

            o.max_actions-=1

            print ("max_actions " + str(o.max_actions))
            
            if(o.max_actions > 0):
                # volver a seleccionar unidad
                o.battle_selected_unit = o.combat_moving_unit

                o.button_A_command = "Atacar"

                o.battle_state = "select_target"

                o.current_action_type = "attack"

                #self.switch_x_command()

                o.combat_moving_unit = None
                
                if not o.battle_target_tiles:

                    self.build_battle_target_tiles(
                        o.battle_selected_unit
                    )

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

        if diff > 0.4:

            started = o.try_start_mantle(
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

                else:

                    chosen = "run_perfil_izq"
                    face = "izq"

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
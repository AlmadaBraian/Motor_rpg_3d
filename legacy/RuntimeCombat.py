import math
from collections import deque

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

    # =========================================================
    # START COMBAT
    # =========================================================

    def start_runtime_combat(self, enemy_id=""):

        o = self.owner

        if o.battle_mode:
            return

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
    
    def switch_attack_move (self):
        o = self.owner

        if not self.attack_performed:

            if o.battle_state == "select_move":

                    o.battle_state = "select_attack"

                    o.button_A_command = "Atacar"

                    o.battle_move_tiles = []

                    # si todavia no existen
                    if not o.battle_attack_tiles:

                        self.build_battle_attack_tiles(
                            o.battle_selected_unit
                        )

                        print("SHOW MOVE TILES")

                        return

                    print("STATE: SELECT ATTACK")

                    return

            elif o.battle_state == "select_attack":

                o.battle_state = "select_move"

                o.button_A_command = "Mover a"

                o.battle_attack_tiles = []


                # si todavia no existen
                if not o.battle_move_tiles:

                    self.build_battle_move_tiles(
                        o.battle_selected_unit
                    )

                    print("SHOW MOVE TILES")

                    return

                print("STATE: SELECT MOVE")

                return

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
            o.battle_state == "select_attack"
            and (rx != 0 or ry != 0)
        ):

            if not o.battle_attack_tiles:
                return

            current = (
                o.battle_cursor_x,
                o.battle_cursor_y
            )

            # cursor inválido
            if current not in o.battle_attack_tiles:

                first = o.battle_attack_tiles[0]

                o.battle_cursor_x = first[0]
                o.battle_cursor_y = first[1]

            else:

                best = current
                best_score = 999999

                for tx, ty in o.battle_attack_tiles:

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

        if event.keysym in ["Left", "Right"]:

            o.battle_input_cooldown = 0.25

            self.switch_attack_move()

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
                    o.battle_attack_tiles = []

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

                if o.battle_state == "select_attack":
                        
                    if not o.battle_attack_tiles:

                        self.build_battle_attack_tiles(
                            o.battle_selected_unit
                        )

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
                        self.perform_attack(target)
                        
                    print ("max_actions " + str(o.max_actions))
                    return



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
        o.battle_attack_tiles = []
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

        if not o.battle_units:
            return

        if not o.play_mode:
            return

        o.battle_input_cooldown = 0.25

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

        # =========================================
        # IA
        # =========================================

        if inst.battle_team == "enemy":

            self.run_enemy_turn()

        else:

            print("PLAYER TURN")

            o.battle_state = "idle"
            self.battle_camera_mode = 1
            o.show_ui = True
            o.button_A_command = "Seleccionar"
            o.button_X_command = "Guardia"

        print(
            "CURRENT UNIT:",
            inst.actor_name,
            "TEAM:",
            inst.battle_team
        )

    def run_enemy_turn(self):

        o = self.owner

        if not o.play_mode:
            return

        print("ENEMY TURN")

        o.viewport.after(
            700,
            lambda: self.end_battle_turn()
        )

    # =========================================================
    # ATTACK RANGE
    # =========================================================

    def build_battle_attack_tiles(self, pack):

        o = self.owner

        o.battle_attack_tiles = []

        inst = pack["inst"]

        if inst.actor_name not in o.actors:
            return

        actor_def = o.actors[inst.actor_name]

        attack_range = getattr(
            actor_def,
            "attack_range",
            1
        )

        startx = pack["gx"]
        starty = pack["gy"]

        visited = set()

        queue = [
            (startx, starty, 0)
        ]

        while queue:

            x, y, d = queue.pop(0)

            if d > attack_range:
                continue

            if (x, y) in visited:
                continue

            visited.add((x, y))

            # no incluir tile central
            if not (x == startx and y == starty):

                o.battle_attack_tiles.append(
                    (x, y)
                )

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

                queue.append(
                    (nx, ny, d + 1)
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
        if o.runtime_collides(px, py, 0, radius=0.28):
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

        if hasattr(o, "game_view"):
            cam = o.game_view.game_camera
        else:
            cam = o.viewport.camera

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

        # =========================================
        # FOLLOW CURSOR WHILE SELECTING MOVE
        # =========================================

        elif o.battle_state == "select_move":

            target_x = (
                o.battle_cursor_x + 0.5
            )

            target_z = (
                o.battle_cursor_y + 0.5
            )

        # =========================================
        # DEFAULT: CURRENT UNIT
        # =========================================

        elif o.battle_current_unit:

            pack = o.battle_current_unit

            target_x = pack["gx"] + 0.5
            target_z = pack["gy"] + 0.5

        speed = 5.0

        cam.x += (target_x - cam.x) * min(1.0, dt * speed)
        cam.z += (target_z - cam.z) * min(1.0, dt * speed)


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

        # ORBITAL
        cam.yaw = o.runtime_cam_orbit

        if self.runtime_attack_camera:

            diff = (
                self.runtime_attack_cam_target
                - o.runtime_cam_orbit
                + 540
            ) % 360 - 180

            o.runtime_cam_orbit += diff * min(1, dt * 6)

            if abs(diff) < 1:

                o.runtime_cam_orbit = (
                    self.runtime_attack_cam_target
                )

                self.runtime_attack_camera = False

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

    def focus_battle_camera_on_current(self):

        o = self.owner

        if not o.battle_current_unit:
            return

        pack = o.battle_current_unit

        o.battle_cam_target_x = pack["gx"] + 0.5
        o.battle_cam_target_z = pack["gy"] + 0.5

        print(
            "BATTLE CAMERA TARGET:",
            o.battle_cam_target_x,
            o.battle_cam_target_z
        )

    def start_attack_camera(self, attacker_pack, target_pack):

        attacker = attacker_pack["inst"]
        target = target_pack["inst"]

        ax = attacker_pack["gx"] + attacker.offx
        ay = attacker_pack["gy"] + attacker.offy

        tx = target_pack["gx"] + target.offx
        ty = target_pack["gy"] + target.offy

        dx = tx - ax
        dy = ty - ay

        ang = math.degrees(
            math.atan2(dx, dy)
        )

        if dx >= 0:
            cam_yaw = ang - 90
            self.attack_anim_side = "dere"
        else:
            cam_yaw = ang + 90
            self.attack_anim_side = "izq"

        self.runtime_attack_cam_target = (
            cam_yaw % 360
        )

        self.runtime_attack_camera = True

    def perform_attack(self, target_pack):

        o = self.owner

        hit = False

        attacker_pack = o.battle_attacker_unit

        if not attacker_pack:
            return

        if not target_pack:
            return

        attacker = attacker_pack["inst"]
        target = target_pack["inst"]

        self.attack_anim_inst = attacker
        self.damage_anim_inst = target

        self.attack_result_type = "normal"

        self.start_attack_camera(attacker_pack, target_pack)

        # =========================================
        # VALIDACIONES
        # =========================================

        if getattr(target, "battle_dead", False):
            return

        if attacker_pack == target_pack:
            return

        if attacker.battle_team == target.battle_team:
            return

        # =========================================
        # ACTOR DATA
        # =========================================

        atk_def = o.actors.get(attacker.actor_name)
        tgt_def = o.actors.get(target.actor_name)

        if not atk_def or not tgt_def:
            return

        # =========================================
        # STATS
        # =========================================
        #Aca hay que agregar losbonus que van a dar las armas y los escudos
        body_type_tgt = getattr(tgt_def, "body_type", "normal")
        body_type_atk = getattr(atk_def, "body_type", "normal")

        body_type_tgt_bonus = o.body_type_list[body_type_tgt]

        body_type_atk_bonus = o.body_type_list[body_type_atk]

        speed_bonus = 0

        if getattr(atk_def, "speed", 0) > 4 : speed_bonus = 1.25
        elif getattr(atk_def, "speed", 0) < 4 : speed_bonus = 1

        attack_bonus = getattr(atk_def, "attack_bonus", 0) * speed_bonus  #* body_type_atk_bonus
        armor_class = getattr(tgt_def, "armor_class", 10) * body_type_tgt_bonus 

        # =========================================
        # ATTACK ROLL
        # =========================================

        roll = random.randint(1, 20)

        total_attack = roll + attack_bonus

        print(
            attacker.actor_name,
            "ROLL:",
            roll,
            "+",
            attack_bonus,
            "=",
            total_attack
        )

        print(
            target.actor_name,
            "CA:",
            armor_class
        )

        critical_hit = False
        critical_miss = False

        # =========================================
        # HIT CHECK
        # =========================================

        if roll == 20:
            hit = True
            critical_hit = True

        elif roll == 1:
            hit = False
            critical_miss = True

        else:
            hit = total_attack >= armor_class

        if critical_hit:
            self.attack_result_type = "critical"

        elif critical_miss:
            self.attack_result_type = "miss"

        elif not hit:
            self.attack_result_type = "miss"

        else:
            self.attack_result_type = "normal"

        if not hit:

            print("MISS")
            if not self.counter_attack:
                print (target.actor_name, "COUNTER ATTACK!")
                o.battle_attacker_unit = target_pack
                self.counter_attack = True

                if getattr(atk_def, "speed", 5) <= getattr(tgt_def, "speed", 5):
                    self.perform_attack(attacker_pack)

                else:
                    print("COUNTER ATTACK MISS")
                    self.counter_attack = False
                    return

            else:
                self.counter_attack = False

            if critical_miss:
                print("CRITICAL MISS!")

            # no aplicar daño
            return

        print("HIT")
        self.counter_attack = False

        # =========================================
        # DAMAGE
        # =========================================

        dmg_min = getattr(atk_def, "damage_min", 1)  #  + damage_weapon
        dmg_max = getattr(atk_def, "damage_max", 6) #  + damage_weapon

        # crítico natural
        if roll == 20:
            dmg_max *= 2
            dmg_max -=2
            if self.counter_attack:
                dmg_max -= 2
            print("CRITICAL HIT!")

        # fallo crítico
        if roll == 1:
            print("CRITICAL MISS!")
            return

        base_damage = random.randint(dmg_min, dmg_max) * body_type_atk_bonus 

        defense = getattr(tgt_def, "defense", 0) * body_type_atk_bonus # + armor_defense

        damage = max(1, base_damage + attack_bonus - defense)

        # =========================================
        # HP
        # =========================================

        if not hasattr(target, "hp"):

            maxhp = getattr(tgt_def, "hp", 30)

            target.hp = maxhp

        target.hp -= damage

        print(
            attacker.actor_name,
            "attacks",
            target.actor_name,
            "for",
            damage,
            "damage"
        )

        print(
            target.actor_name,
            "HP:",
            target.hp
        )

        # =========================================
        # MUERTE
        # =========================================

        if target.hp <= 0:

            target.hp = 0
            target.battle_dead = True

            print(target.actor_name, "DEAD")

            tile = o.runtime_world.grid[
                target_pack["gy"]
            ][
                target_pack["gx"]
            ]

            if target_pack in tile.actors:
                tile.actors.remove(target_pack)

            if target_pack in o.battle_units:
                o.battle_units.remove(target_pack)

            if target_pack in o.battle_turn_order:
                o.battle_turn_order.remove(target_pack)

        # =========================================
        # LIMPIAR UI
        # =========================================

        o.battle_attack_tiles = []
        o.battle_move_tiles = []

    # =========================================================
    # UNIT MOVEMENT
    # =========================================================

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

            if self.attack_result_type == "critical":
                idle_anim = (
                        "sitdown_izq"
                        if self.attack_anim_side == "dere"
                        else "sitdown_dere"
                    )
                
            elif inst.battle_dead:
                idle_anim = (
                        "hit_fall_face_up_izq"
                        if self.attack_anim_side == "dere"
                        else "hit_fall_face_up_dere"
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

            # consumir accion
            o.max_actions -= 1

            print("max_actions", o.max_actions)

            # limpiar
            o.battle_attack_tiles = []

            # FIN TURNO
            if o.max_actions <= 0:

                o.battle_selected_unit = None
                o.battle_state = "idle"

                self.end_battle_turn()

            else:

                o.battle_state = "select_move"

                o.button_A_command = "Mover a"

                if not o.battle_move_tiles:

                    self.build_battle_move_tiles(
                        o.battle_selected_unit
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

        # =====================================
        # FIN MOVIMIENTO
        # =====================================

        if not o.combat_move_queue:

            o.combat_actor_moving = False

            o.max_actions-=1

            print ("max_actions " + str(o.max_actions))
            
            if(o.max_actions > 0):
                # volver a seleccionar unidad
                o.battle_selected_unit = o.combat_moving_unit

                o.button_A_command = "Atacar"

                o.battle_state = "select_attack"

                o.combat_moving_unit = None
                
                if not o.battle_attack_tiles:

                    self.build_battle_attack_tiles(
                        o.battle_selected_unit
                    )

            # FIN TURNO
            else:

                o.battle_selected_unit = None
                o.battle_state = "idle"

                self.end_battle_turn()

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

            chosen = "walk_espalda"
            face = "espalda"

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
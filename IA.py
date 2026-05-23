from config import NORMAL_ATTACK_SCRIPT


def find_closest_enemy(self, user_pack):

    o = self.owner

    ux = user_pack["gx"]
    uy = user_pack["gy"]

    user_inst = user_pack["inst"]

    closest_pack = None
    closest_dist = 999999

    for row in o.runtime_world.grid:

        for tile in row:

            for pack in getattr(tile, "actors", []):

                if pack == user_pack:
                    continue

                inst = pack["inst"]

                # muerto
                if inst.battle_dead:
                    continue

                # mismo equipo
                if inst.battle_team == user_inst.battle_team:
                    continue

                dx = pack["gx"] - ux
                dy = pack["gy"] - uy

                dist = abs(dx) + abs(dy)

                if dist < closest_dist:

                    closest_dist = dist
                    closest_pack = pack

    return closest_pack

def find_best_tile_towards_target(
    self,
    user_pack,
    target_pack
):

    o = self.owner

    tx = target_pack["gx"]
    ty = target_pack["gy"]

    best_tile = None
    best_dist = 999999

    adjacent_tiles = [
        (tx, ty - 1),
        (tx, ty + 1),
        (tx - 1, ty),
        (tx + 1, ty)
    ]

    # =====================================
    # BUSCAR TILE ADYACENTE
    # =====================================

    for mx, my in o.battle_move_tiles:

        for ax, ay in adjacent_tiles:

            if mx == ax and my == ay:

                dist = abs(mx - tx) + abs(my - ty)

                if dist < best_dist:

                    best_dist = dist
                    best_tile = (mx, my)

    # =====================================
    # SI ENCONTRO TILE DE ATAQUE
    # =====================================

    if best_tile:
        return best_tile

    # =====================================
    # SI NO LLEGA:
    # TILE MAS CERCANA
    # =====================================

    best_dist = 999999

    for mx, my in o.battle_move_tiles:

        dist = abs(mx - tx) + abs(my - ty)

        if dist < best_dist:

            best_dist = dist
            best_tile = (mx, my)

    return best_tile

def update_enemy_ai(self, dt):

    o = self.owner

    current = o.battle_current_unit

    if not current:
        return

    inst = current["inst"]

    if inst.battle_team != "enemy":
        o.enemy_ai_state = None
        return

    state = getattr(
        o,
        "enemy_ai_state",
        None
    )

    if not state:
        return

    # =====================================
    # MOVE CURSOR
    # =====================================

    if state == "move_cursor":

        tx, ty = o.enemy_target_tile

        cx = o.battle_cursor_x
        cy = o.battle_cursor_y

        # =====================================
        # MOVER CURSOR
        # =====================================

        if cx < tx:
            o.battle_cursor_x += 1

        elif cx > tx:
            o.battle_cursor_x -= 1

        elif cy < ty:
            o.battle_cursor_y += 1

        elif cy > ty:
            o.battle_cursor_y -= 1

        # =====================================
        # LLEGO
        # =====================================

        else:

            print("AI CURSOR ARRIVED")

            enemy_confirm_move(self)

            o.enemy_ai_state = "wait_move_finish"

            return

    # =====================================
    # WAIT MOVE
    # =====================================

    if state == "wait_move_finish":

        if o.combat_actor_moving:
            return

        print("AI MOVE FINISHED")

        o.enemy_ai_state = "select_attack"

        o.battle_move_tiles = []

        return

    # =====================================
    # SELECT ATTACK
    # =====================================

    if state == "select_attack":

        target = enemy_find_attack_target(self)

        if not target:

            print("NO TARGET IN RANGE")
            self.pending_turn_end = True
            self.turn_end_timer = 0.9

            o.enemy_ai_state = "end_turn"
            return

        o.enemy_ai_attack_target = target

        o.battle_cursor_x = target["gx"]
        o.battle_cursor_y = target["gy"]

        print(
            "TARGET FOUND:",
            target["inst"].actor_name
        )

        o.enemy_ai_state = "confirm_attack"
        o.battle_move_tiles = []

        return

    # =====================================
    # CONFIRM ATTACK
    # =====================================

    if state == "confirm_attack":

        target = o.enemy_ai_attack_target

        o.battle_attacker_unit = (
            o.battle_current_unit
        )

        self.attack_performed = True

        o.current_action_type = "attack"

        self.start_runtime_skill(
                NORMAL_ATTACK_SCRIPT,
                o.battle_attacker_unit,
                target
            )

        o.enemy_ai_state = "wait_attack_finish"

        return
    
    if state == "wait_attack_finish":

        # skill todavía ejecutándose
        if self.active_runtime_skill:
            return

        # cámara todavía activa
        if self.runtime_attack_camera:
            return

        # animaciones todavía activas
        if self.performing_attack:
            return
        
        self.pending_turn_end = True
        self.turn_end_timer = 0.9

        o.enemy_ai_state = "end_turn"

    # =====================================
    # END TURN
    # =====================================

    if state == "end_turn":

        if self.performing_attack:
            return

        if self.runtime_attack_camera:
            return
        
        if self.pending_turn_end:

            self.turn_end_timer -= dt

            if self.turn_end_timer <= 0:

                self.pending_turn_end = False

                print("AI TURN END")

                o.enemy_ai_state = None

                self.end_battle_turn()

        

def enemy_find_attack_target(self):

    o = self.owner

    attacker = o.battle_current_unit

    if not attacker:
        return None

    team = attacker["inst"].battle_team

    ax = attacker["gx"]
    ay = attacker["gy"]

    best = None
    best_dist = 999

    for pack in o.battle_units:

        if pack == attacker:
            continue

        inst = pack["inst"]

        if inst.battle_dead:
            continue

        if inst.battle_team == team:
            continue

        dx = abs(pack["gx"] - ax)
        dy = abs(pack["gy"] - ay)

        dist = dx + dy

        # melee range
        if dist > 1:
            continue

        if dist < best_dist:

            best_dist = dist
            best = pack

    return best

def enemy_confirm_move(self):

    o = self.owner

    tx = o.battle_cursor_x
    ty = o.battle_cursor_y

    if (tx, ty) not in o.battle_move_tiles:
        return

    sx = o.battle_current_unit["gx"]
    sy = o.battle_current_unit["gy"]

    o.combat_path = self.build_combat_path(
        sx,
        sy,
        tx,
        ty
    )

    if not o.combat_path:
        return

    o.combat_move_queue = o.combat_path.copy()

    o.combat_moving_unit = o.battle_current_unit

    o.combat_actor_moving = True

    inst = o.battle_current_unit["inst"]

    inst.is_battle_moving = True
    inst.battle_move_timer = 0.0

    o.battle_state = "idle"

    print("AI UNIT MOVING")
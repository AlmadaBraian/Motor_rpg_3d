import math

from config import GRID_H, GRID_W



def execute_charge_attack(
    self,
    user_pack,
    target_pack,
    action_data
):

    o = self.owner

    user = user_pack["inst"]
    target = target_pack["inst"]

    print("START CHARGE ATTACK")

    if o.runtime_cam_orbit is None:
        o.runtime_cam_orbit = 0

    o.runtime_cam_orbit = self.previous_camera_orbit

    # =====================================
    # GUARDAR CONTEXTO
    # =====================================

    self.charge_attack_active = True

    self.charge_attack_user = user_pack
    self.charge_attack_target = target_pack
    self.charge_attack_action = action_data

    self.charge_attack_phase = "camera"

    self.attack_anim_inst = user
    self.damage_anim_inst = target
    self.charge_attack_camera = True
    

    ux = user_pack["gx"]
    uy = user_pack["gy"]

    tx = target_pack["gx"]
    ty = target_pack["gy"]

    dx = tx - ux
    dy = ty - uy

    step_x = 0
    step_y = 0

    if abs(dx) > abs(dy):

        step_x = 1 if dx > 0 else -1

    else:

        step_y = 1 if dy > 0 else -1

    target_tile_x = tx - step_x
    target_tile_y = ty - step_y

    self.charge_attack_dest = (
        target_tile_x,
        target_tile_y
    )

    # =====================================
    # PUSH TILE
    # =====================================

    push_x = tx + step_x
    push_y = ty + step_y

    if (
        0 <= push_x < GRID_W
        and
        0 <= push_y < GRID_H
    ):

        self.charge_attack_push_tile = (
            push_x,
            push_y
        )

    else:

        self.charge_attack_push_tile = None

    # =====================================
    # CAMERA
    # =====================================

    self.start_attack_camera(
        user_pack,
        target_pack
    )

def charge_camera_blocked(
    self,
    user_pack,
    target_pack,
    yaw
):

    o = self.owner

    ux = user_pack["gx"] + 0.5
    uy = user_pack["gy"] + 0.5

    tx = target_pack["gx"] + 0.5
    ty = target_pack["gy"] + 0.5

    midx = (ux + tx) * 0.5
    midy = (uy + ty) * 0.5

    ang = math.radians(yaw)

    camx = midx + math.sin(ang) * 2.0
    camy = midy + math.cos(ang) * 2.0

    steps = 12

    for i in range(steps):

        t = i / steps

        sx = camx + (midx - camx) * t
        sy = camy + (midy - camy) * t

        gx = int(sx)
        gy = int(sy)

        if (
            gx < 0
            or gy < 0
            or gx >= GRID_W
            or gy >= GRID_H
        ):
            continue

        tile = o.runtime_world.grid[gy][gx]

        if getattr(tile, "is_block", False):

            return True

    return False

def start_charge_attack_camera(
    self,
    user_pack,
    target_pack
):

    o = self.owner

    ux = user_pack["gx"]
    uy = user_pack["gy"]

    tx = target_pack["gx"]
    ty = target_pack["gy"]

    dx = tx - ux
    dy = ty - uy

    # =====================================
    # YAWS PRIORITARIOS
    # =====================================

    # =====================================
    # YAWS DE PERFIL VALIDOS
    # =====================================

    ang = math.degrees(
    math.atan2(dx, dy)
    )

    yaw_a = (ang - 90) % 360
    yaw_b = (ang + 90) % 360

    side_a = "dere"
    side_b = "izq"

    # =====================================
    # ELEGIR PERFIL MAS CERCANO
    # =====================================

    current = o.runtime_cam_orbit % 360

    def angle_dist(a, b):
        return abs((a - b + 180) % 360 - 180)

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
    # FALLBACKS
    # =====================================

    for extra in [90, 270, 0, 180]:

        if extra not in yaw_candidates:
            yaw_candidates.append(extra)

    # =====================================
    # ELEGIR PRIMER ANGULO LIBRE
    # =====================================

    best_yaw = yaw_candidates[0][0]
    best_side = yaw_candidates[0][1]

    for yaw, side in yaw_candidates:

        blocked = charge_camera_blocked(
            self,
            user_pack,
            target_pack,
            yaw
        )

        if not blocked:

            best_yaw = yaw
            best_side = side
            break

    # =====================================
    # INIT CAMERA
    # =====================================

    if o.runtime_cam_orbit is None:
        o.runtime_cam_orbit = 0

    self.runtime_attack_cam_target = best_yaw

    self.runtime_attack_camera = True

    self.charge_attack_camera = True

    self.battle_camera_mode = 1

    self.attack_anim_side = best_side

    print(
        "CHARGE CAMERA START",
        best_yaw
    )

def update_charge_attack(self, dt):

    if not self.charge_attack_active:
        return

    o = self.owner

    phase = self.charge_attack_phase

    # =====================================
    # ESPERANDO CAMARA
    # =====================================

    if phase == "camera":

        # seguir esperando mientras rota
        if self.runtime_attack_camera:
            return

        print("CAMERA READY")

        user_pack = self.charge_attack_user

        user = user_pack["inst"]

        user.charge_running = True

        tx, ty = self.charge_attack_dest

        o.combat_move_queue = [
            (tx, ty)
        ]

        o.combat_actor_moving = True

        o.combat_moving_unit = user_pack

        user.is_battle_moving = True

        self.charge_attack_phase = "move"

        o.combat_moving_unit = o.battle_selected_unit

        o.combat_actor_moving = True

        o.combat_moving_unit = user_pack

        user.is_battle_moving = True
        user.battle_move_timer = 0.0
        user.battle_moved = True

        o.battle_selected_unit = None

        o.battle_move_tiles = []

        o.battle_state = "idle"

        print("UNIT MOVING")

        return

    # =====================================
    # ESPERANDO LLEGADA
    # =====================================

    if phase == "move":

        if o.combat_actor_moving:
            return

        print("CHARGE ARRIVED")

        finish_charge_attack(self)

        return
    # =====================================
    # EMPUJE
    # =====================================

    if phase == "push":
        print("if phase == push")

        update_charge_push(self, dt)

    # =====================================
    # WAIT ANIM FINISH
    # =====================================

    if phase == "finish_wait":

        user_pack = self.charge_attack_user
        target_pack = self.charge_attack_target

        user = user_pack["inst"]
        target = target_pack["inst"]

        user_done = True
        target_done = True

        if user.animator:
            user_done = user.animator.finished

        if target.animator:
            target_done = target.animator.finished

        if not user_done:
            return

        if not target_done:
            return

        end_charge_attack(self)

        return
    
def start_charge_attack_animation(self):

    user_pack = self.charge_attack_user
    target_pack = self.charge_attack_target

    user = user_pack["inst"]
    target = target_pack["inst"]

    dx = target_pack["gx"] - user_pack["gx"]

    side = self.attack_anim_side

    attack_anim = (
        "attack_dereX2"
        if side == "dere"
        else "attack_izqX2"
    )

    hit_anim = (
        "hit_fall_face_up_izq"
        if side == "dere"
        else "hit_fall_face_up_dere"
    )

    if attack_anim in user.animator.clips:
        user.animator.play(attack_anim)

    if hit_anim in target.animator.clips:
        target.animator.play(hit_anim)

    self.charge_phase_timer = 0.0

def apply_charge_attack_damage(self):

    o = self.owner

    user_pack = self.charge_attack_user
    target_pack = self.charge_attack_target

    target = target_pack["inst"]

    result = self.calculate_combat_result(
        user_pack,
        target_pack,
        self.charge_attack_action
    )

    actor_def_target = o.actors.get(
        target.actor_name
    )

    actor_def_target.hp -= result["damage"]

    print(
        "CHARGE DAMAGE",
        result["damage"]
    )

    if actor_def_target.hp <= 0:

        actor_def_target.hp = 0

        target.battle_dead = True
        target.pending_remove = True

def start_charge_knockback(self):

    o = self.owner

    user_pack = self.charge_attack_user
    target_pack = self.charge_attack_target

    ux = user_pack["gx"]
    uy = user_pack["gy"]

    tx = target_pack["gx"]
    ty = target_pack["gy"]

    dx = tx - ux
    dy = ty - uy

    step_x = 0
    step_y = 0

    if abs(dx) > abs(dy):

        step_x = 1 if dx > 0 else -1

    else:

        step_y = 1 if dy > 0 else -1

    px = tx + step_x
    py = ty + step_y

    if px < 0 or py < 0:
        return

    if px >= GRID_W or py >= GRID_H:
        return

    target = target_pack["inst"]

    target.knockback_active = True

    target.knockback_from = (
        tx,
        ty
    )

    target.knockback_to = (
        px,
        py
    )

    target.knockback_t = 0.0

def update_knockback(self, pack, dt):

    inst = pack["inst"]

    if not getattr(inst, "knockback_active", False):
        return

    inst.knockback_t += dt * 4.0

    t = min(
        inst.knockback_t,
        1.0
    )

    fx, fy = inst.knockback_from
    tx, ty = inst.knockback_to

    ix = fx + (tx - fx) * t
    iy = fy + (ty - fy) * t

    inst.offx = ix - pack["gx"]
    inst.offy = iy - pack["gy"]

    if t >= 1.0:

        pack["gx"] = tx
        pack["gy"] = ty

        inst.offx = 0
        inst.offy = 0

        inst.knockback_active = False

def update_charge_push(self, dt):
    print("update_charge_push")

    o = self.owner

    target_pack = self.charge_attack_target

    inst = target_pack["inst"]

    self.charge_push_timer += dt * 4.0

    t = min(1.0, self.charge_push_timer)

    sx, sy = self.charge_push_start
    ex, ey = self.charge_push_end

    px = sx + (ex - sx) * t
    py = sy + (ey - sy) * t

    inst.offx = px - target_pack["gx"]
    inst.offy = py - target_pack["gy"]

    if t >= 1.0:

        oldtile = o.runtime_world.grid[
            target_pack["gy"]
        ][
            target_pack["gx"]
        ]

        if target_pack in oldtile.actors:
            oldtile.actors.remove(target_pack)

        target_pack["gx"] = ex
        target_pack["gy"] = ey

        newtile = o.runtime_world.grid[ey][ex]

        if target_pack not in newtile.actors:
            newtile.actors.append(target_pack)

        inst.offx = 0
        inst.offy = 0

        self.charge_attack_phase = "finish_wait"

        #end_charge_attack(self)

def end_charge_attack(self):
    print("end_charge_attack")

    o = self.owner

    self.charge_attack_active = False

    self.charge_attack_phase = None

    self.charge_attack_camera = False


    self.mantle_skill_active = False

    self.mantle_skill_action = None


     # consumir accion
    o.max_actions -= 1

    #user.battle_moved = False

    print(
        "max_actions finish charge skill",
        o.max_actions
    )

    o.battle_target_tiles = []
    o.selected_combat_action = None

    o.battle_state = "select_target"

    o.battle_move_tiles = []

    o.current_action_type = "attack"

    self.build_battle_target_tiles(self.charge_attack_user)

    o.button_A_command = "Atacar"
    

    # =====================================
    # FIN TURNO
    # =====================================

    if o.max_actions <= 0:
        idle_anim = (
                    "idle_izq"
                    if self.attack_anim_side == "dere"
                    else "idle_dere"
                )

        if idle_anim in self.charge_attack_user["inst"].animator.clips:
                self.charge_attack_user["inst"].animator.play(idle_anim)

        o.battle_selected_unit = None
        o.battle_state = "idle"

        self.end_battle_turn()

    else:

        o.battle_selected_unit = self.charge_attack_user

        o.button_A_command = "Atacar"

        o.battle_state = "select_target"

        o.current_action_type = "attack"

        idle_anim = (
                    "idle_izq"
                    if self.attack_anim_side == "dere"
                    else "idle_dere"
                )

        if idle_anim in self.charge_attack_user["inst"].animator.clips:
                self.charge_attack_user["inst"].animator.play(idle_anim)

        #self.switch_x_command()

        self.charge_attack_user = None

def start_charge_push(self):
    print("start_charge_push")

    o = self.owner

    push_tile = self.charge_attack_push_tile

    if not push_tile:

        end_charge_attack(self)
        return

    target_pack = self.charge_attack_target

    self.charge_push_start = (
        target_pack["gx"],
        target_pack["gy"]
    )

    self.charge_push_end = push_tile

    self.charge_push_timer = 0.0

    self.charge_attack_phase = "push"

def finish_charge_attack(self):

    o = self.owner

    user_pack = self.charge_attack_user

    user = user_pack["inst"]

    user.charge_running = False

    o.combat_actor_moving = False
    o.combat_moving_unit = None

    # =====================================
    # ANIMACIONES
    # =====================================

    start_charge_attack_animation(self)

    apply_charge_attack_damage(self)

    # =====================================
    # PUSH
    # =====================================

    start_charge_push(self)
# =========================================================
# MANTLE SKILL
# =========================================================

def execute_mantle_skill(
    self,
    user_pack,
    target_tile,
    action_data
):

    o = self.owner

    user = user_pack["inst"]

    tx, ty = target_tile
    

    # =====================================================
    # VALIDACIONES
    # =====================================================

    if tx < 0 or ty < 0:
        return False

    if tx >= GRID_W or ty >= GRID_H:
        return False

    t = o.runtime_world.grid[ty][tx]

    # debe ser block
    if not getattr(t, "is_block", False):
        return False

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

    # =====================================================
    # MOVIMIENTO
    # =====================================================

    path = self.build_mantle_path(
        ux,
        uy,
        adjacent_tile[0],
        adjacent_tile[1]
    )

    if adjacent_tile != (ux, uy) and not path:

        print("NO PATH TO MANTLE")

        return False
    
    if adjacent_tile == (ux, uy):

        self.finish_mantle_skill(self)

        return "async"

    o.combat_move_queue = path

    user.combat_using_mantle = True

    user.combat_mantle_target = (
        tx,
        ty
    )

    user.is_battle_moving = True
    user.battle_move_timer = 0.0
    user.battle_moved = True

    o.combat_actor_moving = True
    o.combat_moving_unit = user_pack

    o.battle_selected_unit = None

    o.battle_move_tiles = []

    o.battle_state = "idle"

    # =====================================================
    # GUARDAR CONTEXTO
    # =====================================================

    self.mantle_skill_active = True

    self.mantle_skill_user = user_pack

    self.mantle_skill_action = action_data

    self.mantle_skill_target_tile = (
        tx,
        ty
    )

    print("MANTLE MOVE START")

    return "async"


# =========================================================
# FIN MANTLE SKILL
# =========================================================
def finish_mantle_skill(self):

    o = self.owner

    user_pack = self.mantle_skill_user
    user = user_pack["inst"]

    tx, ty = self.mantle_skill_target_tile

    ux = user_pack["gx"]
    uy = user_pack["gy"]

    dx = tx - ux
    dy = ty - uy

    started = o.try_start_mantle(
        user_pack,
        dx,
        dy
    )

    if not started:

        print("FAILED START MANTLE")
        self.mantle_skill_active = False
        return

    o.battle_move_tiles = []
    o.battle_target_tiles = []
    print("MANTLE STARTED")

def complete_mantle_skill (self):

    o = self.owner

    user_pack = self.mantle_skill_user
    user = user_pack["inst"]

    # =====================================================
    # LIMPIEZA FLAGS
    # =====================================================

    user.combat_using_mantle = False

    self.mantle_skill_active = False

    self.mantle_skill_action = None

    user.combat_mantle_target = None

    user.battle_moved = True

     # consumir accion
    o.max_actions -= 1

    #user.battle_moved = False

    print(
        "max_actions finish mantle skill",
        o.max_actions
    )

    o.battle_target_tiles = []
    o.selected_combat_action = None
    

    # =====================================
    # FIN TURNO
    # =====================================

    if o.max_actions <= 0:

        o.battle_selected_unit = None
        o.battle_state = "idle"

        self.end_battle_turn()

    else:

        o.battle_selected_unit = o.combat_moving_unit

        o.button_A_command = "Atacar"

        o.battle_state = "select_target"

        o.current_action_type = "attack"

        #self.switch_x_command()

        o.combat_moving_unit = None

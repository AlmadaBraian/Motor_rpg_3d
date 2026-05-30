# =========================================================
# RUNTIME SKILL
# =========================================================

from config import GRID_H, GRID_W, NORMAL_ATTACK_SCRIPT


class RuntimeSkill:

    def __init__(
    self,
    combat,
    script,
    user_pack,
    target_pack=None,
    target_tile=None,
    action_data=None
    ):

        self.combat = combat
        self.owner = combat.owner

        self.skill = action_data

        self.user_pack = user_pack
        self.target_pack = target_pack

        self.target_tile = target_tile

        self.action_data = action_data

        self.script = script or []

        self.index = 0

        self.running = True

        self.waiting = False
        self.wait_timer = 0.0

        self.waiting_animation = False
        self.wait_animation_target = None

        self.finished = False

        self.flags = {}

        self.wait_flag = None

        self.wait_type = None

        # =====================================
        # CUSTOM DATA
        # =====================================

        self.data = {}

    # =====================================================
    # UPDATE
    # =====================================================

    def update(self, dt):

        if not self.running:
            return

        update_skill_script(self, dt)


def update_skill_script(runtime_skill, dt):

    combat = runtime_skill.combat

    # =====================================
    # FINISHED
    # =====================================

    if runtime_skill.finished:
        return

    # =====================================
    # WAIT TIMER
    # =====================================

    if runtime_skill.waiting:

        if runtime_skill.wait_timer > 0:

            runtime_skill.wait_timer -= dt

            if runtime_skill.wait_timer <= 0:

                runtime_skill.waiting = False
                runtime_skill.index += 1

            return

        flag = runtime_skill.wait_flag

        if runtime_skill.flags.get(flag):

            runtime_skill.waiting = False

            runtime_skill.wait_flag = None

        else:

            return

    # =====================================
    # WAIT ANIMATION
    # =====================================

    if runtime_skill.waiting_animation:

        target = runtime_skill.wait_animation_target

        if not target:

            runtime_skill.waiting_animation = False
            runtime_skill.index += 1
            return

        animator = getattr(target, "animator", None)

        if not animator:

            if (
                runtime_skill.target_pack
                and
                target == runtime_skill.target_pack["inst"]
            ):
                combat.finalize_pending_dead_unit(
                    runtime_skill.target_pack
                )

            runtime_skill.waiting_animation = False
            runtime_skill.index += 1
            return

        #animator.update(dt)

        if animator.finished:

            if (
                runtime_skill.target_pack
                and
                target == runtime_skill.target_pack["inst"]
            ):
                combat.finalize_pending_dead_unit(
                    runtime_skill.target_pack
                )

            runtime_skill.waiting_animation = False
            runtime_skill.index += 1

        return

    # =====================================
    # END SCRIPT
    # =====================================

    if runtime_skill.index >= len(runtime_skill.script):

        end_runtime_skill(runtime_skill)
        return

    # =====================================
    # EXECUTE COMMAND
    # =====================================

    cmd = runtime_skill.script[
        runtime_skill.index
    ]

    run_skill_command(
        runtime_skill,
        cmd
    )

def run_skill_command(
    runtime_skill,
    cmd
):

    combat = runtime_skill.combat
    o = combat.owner

    action = cmd.get("action", "")

    user_pack = runtime_skill.user_pack
    target_pack = runtime_skill.target_pack

    user = None
    target = None

    if user_pack:
        user = user_pack["inst"]

    if (
        target_pack
        and
        isinstance(target_pack, dict)
    ):
        target = target_pack["inst"]

    target_tile = runtime_skill.target_tile


    if action == "wait_runtime_flag":

        flag = cmd.get("flag")

        if runtime_skill.flags.get(flag):

            runtime_skill.index += 1

        return

    # =====================================================
    # WAIT
    # =====================================================

    if action == "wait":

        runtime_skill.waiting = True

        runtime_skill.wait_timer = (
            cmd.get("time", 0) / 1000.0
        )

        return

    # =====================================================
    # PLAY ANIMATION
    # =====================================================

    if action == "play_animation":

        side = combat.attack_anim_side

        runtime_skill.data["attack_side"] = side

        target_name = cmd.get(
            "target",
            "user"
        )

        inst = None

        if target_name == "user":
            inst = user

        elif target_name == "target":
            inst = target

        # =====================================
        # CLIP SEGUN LADO
        # =====================================

        clip = ""

        action_data = runtime_skill.action_data

        if action_data:

            if side == "dere":

                clip = getattr(
                    action_data,
                    "animation_clip_dere",
                    ""
                )

            else:

                clip = getattr(
                    action_data,
                    "animation_clip_izq",
                    ""
                )

        # fallback opcional
        if not clip:
            clip = cmd.get("clip", "")

        # =====================================
        # PLAY
        # =====================================

        if inst and inst.animator:

            if clip in inst.animator.clips:

                inst.animator.play(clip)

        runtime_skill.index += 1
        return
    
    if action == "play_hit_animation":

        side = runtime_skill.data.get(
            "attack_side",
            "dere"
        )

        result = runtime_skill.data.get(
            "combat_result"
        )

        if result is None:

            result = combat.calculate_combat_result(
                user_pack,
                target_pack,
                runtime_skill.action_data
            )

            runtime_skill.data["combat_result"] = result

            if result:

                combat.apply_damage(
                    user_pack,
                    target_pack,
                    result
                )

                runtime_skill.data["damage_applied"] = True

        result_type = "normal"

        if result:

            if result["critical_hit"]:
                result_type = "critical"

            elif not result["hit"]:
                result_type = "miss"

        # =====================================
        # CLIP
        # =====================================

        print("result", result_type)

        if result_type == "critical":

            clip = (
                "hit_fall_sitdown_izq"
                if side == "dere"
                else "hit_fall_sitdown_dere"
            )

        elif result_type == "miss":

            clip = (
                "dodge_izq"
                if side == "dere"
                else "dodge_dere"
            )

        else:

            if getattr(target, "battle_dead", False):

                clip = (
                    "hit_fall_face_up_izq"
                    if side == "dere"
                    else "hit_fall_face_up_dere"
                )

            else:

                clip = (
                    "hit_izq"
                    if side == "dere"
                    else "hit_dere"
                )

        if target and target.animator:

            if clip in target.animator.clips:

                target.animator.play(clip)

        runtime_skill.index += 1
        return
    
    if action == "play_attack_animation":

        side = combat.attack_anim_side

        runtime_skill.data["attack_side"] = side

        result = runtime_skill.data.get(
            "combat_result"
        )

        result_type = "normal"

        if result:

            if result["critical_hit"]:
                result_type = "critical"

            elif not result["hit"]:
                result_type = "miss"

        # =====================================
        # CLIP
        # =====================================

        if result_type == "critical":

            clip = (
                "attack_dereX2"
                if side == "dere"
                else "attack_izqX2"
            )

        elif result_type == "miss":

            clip = (
                "miss_hit_fall_sitdown_dere"
                if side == "dere"
                else "miss_hit_fall_sitdown_izq"
            )

        else:

            clip = (
                "attack_dere"
                if side == "dere"
                else "attack_izq"
            )

        if user and user.animator:

            if clip in user.animator.clips:

                user.animator.play(clip)

        runtime_skill.index += 1
        return
    
    if action == "play_idle_animation":

        side = combat.attack_anim_side

        runtime_skill.data["attack_side"] = side


        # =====================================
        # CLIP
        # =====================================
        
        idle_anim = (
                    "idle_dere"
                    if side == "dere"
                    else "idle_izq"
                )

        if user and user.animator:

            if idle_anim in user.animator.clips:

                user.animator.play(idle_anim)

        runtime_skill.index += 1
        return
    
    if action == "attack_camera":

        combat.attack_anim_inst = user
        combat.damage_anim_inst = target

        if not target:
            end_runtime_skill(
            runtime_skill
            )
            return

        print("ATTACK CAMERA")

        combat.runtime_skill_attack_camera(
            runtime_skill
        )

        runtime_skill.index += 1

        return

    # =====================================================
    # WAIT ANIMATION
    # =====================================================

    if action == "wait_animation":

        target_name = cmd.get(
            "target",
            "user"
        )

        inst = None

        if target_name == "user":
            inst = user

        elif target_name == "target":
            inst = target

        runtime_skill.waiting_animation = True

        runtime_skill.wait_animation_target = inst

        return

    # =====================================================
    # DAMAGE
    # =====================================================

    if action == "damage":

        result = runtime_skill.data.get(
            "combat_result"
        )

        if result is None:

            result = combat.calculate_combat_result(
                user_pack,
                target_pack,
                runtime_skill.action_data
            )

            runtime_skill.data["combat_result"] = result

        if not runtime_skill.data.get("damage_applied"):

            combat.apply_damage(
                user_pack,
                target_pack,
                result
            )

            runtime_skill.data["damage_applied"] = True

        combat.show_popup(
        target_pack,
        result
        )

        runtime_skill.index += 1
        return

    # =====================================================
    # PUSH TARGET
    # =====================================================

    if action == "push_target":

        distance = cmd.get(
            "distance",
            1
        )

        runtime_skill.flags[
            "push_finished"
        ] = False

        push_skill_target(
            runtime_skill,
            distance
        )

        runtime_skill.index += 1

        return

    # =====================================================
    # CALL FUNC
    # =====================================================

    if action == "call_func":

        fn_name = cmd.get("func", "")

        fn = getattr(
            combat,
            fn_name,
            None
        )

        print(fn)

        print(str(fn_name))
        print("TARGET TILE:", runtime_skill.target_tile)

        if fn:

            result = fn(
                runtime_skill.user_pack,
                runtime_skill.target_tile,
                runtime_skill.action_data
            )

            # =====================================
            # ASYNC
            # =====================================

            if result == "async":

                runtime_skill.waiting = True
                runtime_skill.wait_flag = "skill_async"

                runtime_skill.index += 1

                return

        runtime_skill.index += 1
        return
    
    if action == "check_counter":

        result = runtime_skill.data.get(
            "combat_result"
        )

        if not result:

            runtime_skill.index += 1
            return

        # =====================================
        # SOLO SI FALLÓ
        # =====================================

        if result["hit"]:

            runtime_skill.index += 1
            return

        # =====================================
        # NO COUNTEREAR COUNTERS
        # =====================================

        if runtime_skill.data.get(
            "is_counter",
            False
        ):

            runtime_skill.index += 1
            return

        atk_pack = user_pack
        tgt_pack = target_pack

        atk_def = o.actors.get(
            atk_pack["inst"].actor_name
        )

        tgt_def = o.actors.get(
            tgt_pack["inst"].actor_name
        )

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

        if tgt_speed > atk_speed:

            can_counter = True

        elif tgt_speed == atk_speed:

            if tgt_init > atk_init:

                can_counter = True

        # =====================================
        # NO COUNTER
        # =====================================

        if not can_counter:

            runtime_skill.index += 1
            return

        # =====================================
        # POPUP
        # =====================================
        combat.show_popup(
        tgt_pack,
        result, counter=True
        )

        

        # =====================================
        # START COUNTER SKILL
        # =====================================

        counter_skill = combat.start_runtime_skill(
            NORMAL_ATTACK_SCRIPT,
            tgt_pack,
            atk_pack
        )

        counter_skill.data["is_counter"] = True

        # esperar que termine
        runtime_skill.waiting = True

        runtime_skill.wait_flag = (
            "counter_finished"
        )

        counter_skill.data[
            "parent_runtime_skill"
        ] = runtime_skill

        runtime_skill.index += 1

        return
    
    if action == "move_actor":

        combat = runtime_skill.combat
        o = combat.owner

        actor_id = cmd.get(
            "actor",
            "user"
        )

        direction = cmd.get(
            "direction",
            "left"
        )

        tiles = cmd.get(
            "tiles",
            1
        )

        # =====================================
        # SELECT PACK
        # =====================================

        if actor_id == "user":
            pack = runtime_skill.user_pack
        else:
            pack = runtime_skill.target_pack

        inst = pack["inst"]

        start_x = pack["gx"]
        start_y = pack["gy"]

        # =====================================
        # DIRECTION
        # =====================================

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

        # =====================================
        # BUILD PATH
        # =====================================

        queue = []

        for i in range(tiles):

            gx = start_x + dx * (i + 1)
            gy = start_y + dy * (i + 1)

            queue.append((gx, gy))

        # =====================================
        # START MOVEMENT
        # =====================================

        inst.charge_running = True

        runtime_skill.flags[
            "move_finished"
        ] = False

        o.combat_move_queue = queue

        o.combat_actor_moving = True

        o.combat_moving_unit = pack

        inst.is_battle_moving = True

        inst.battle_move_timer = 0.0

        inst.battle_moved = True

        # =====================================
        # WAIT
        # =====================================

        runtime_skill.waiting = True

        runtime_skill.wait_flag = (
            "move_finished"
        )

        runtime_skill.index += 1

        return
    
    if action == "move_to_target":

        combat = runtime_skill.combat
        o = combat.owner

        user_pack = runtime_skill.user_pack
        target_pack = runtime_skill.target_pack

        user = user_pack["inst"]

        ux = user_pack["gx"]
        uy = user_pack["gy"]

        tx = target_pack["gx"]
        ty = target_pack["gy"]

        dx = tx - ux
        dy = ty - uy

        step_x = 0
        step_y = 0

        if abs(dx) > abs(dy):

            step_x = (
                1 if dx > 0 else -1
            )

        else:

            step_y = (
                1 if dy > 0 else -1
            )

        move_x = tx - step_x
        move_y = ty - step_y

        # =====================================
        # IMPORTANT FLAGS
        # =====================================

        user.charge_running = True

        runtime_skill.flags[
            "move_finished"
        ] = False

        # =====================================
        # START MOVEMENT
        # =====================================

        o.combat_move_queue = [
            (move_x, move_y)
        ]

        o.combat_actor_moving = True

        o.combat_moving_unit = user_pack

        user.is_battle_moving = True

        user.battle_move_timer = 0.0

        user.battle_moved = True

        # =====================================
        # WAIT ASYNC
        # =====================================

        runtime_skill.waiting = True

        runtime_skill.wait_flag = (
            "move_finished"
        )

        runtime_skill.index += 1

        return

    # =====================================================
    # END SKILL
    # =====================================================

    if action == "end_skill":

        end_runtime_skill(
            runtime_skill
        )

        return

    # =====================================================
    # UNKNOWN
    # =====================================================

    print(
        "UNKNOWN SKILL ACTION:",
        action
    )

    runtime_skill.index += 1

def update_knockback(self, pack, dt):

    o = self.owner

    inst = pack["inst"]

    if not getattr(inst, "knockback_active", False):
        return

    inst.knockback_t += dt * 4.0

    t = min(inst.knockback_t, 1.0)

    fx, fy = inst.knockback_from
    tx, ty = inst.knockback_to

    ix = fx + (tx - fx) * t
    iy = fy + (ty - fy) * t

    inst.offx = ix - pack["gx"]
    inst.offy = iy - pack["gy"]

    if t >= 1.0:

        oldtile = o.runtime_world.grid[
            pack["gy"]
        ][
            pack["gx"]
        ]

        if pack in oldtile.actors:
            oldtile.actors.remove(pack)

        pack["gx"] = tx
        pack["gy"] = ty

        newtile = o.runtime_world.grid[ty][tx]

        if pack not in newtile.actors:
            newtile.actors.append(pack)

        inst.offx = 0
        inst.offy = 0

        inst.knockback_active = False

        runtime_skill = getattr(
            inst,
            "knockback_runtime_skill",
            None
        )

        if runtime_skill:

            runtime_skill.flags[
                "push_finished"
            ] = True

            inst.knockback_runtime_skill = None

def push_skill_target(
    runtime_skill,
    distance=1
):

    combat = runtime_skill.combat
    o = combat.owner

    user_pack = runtime_skill.user_pack
    target_pack = runtime_skill.target_pack

    if not user_pack or not target_pack:
        return

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

    px = tx + step_x * distance
    py = ty + step_y * distance

    if px < 0 or py < 0:
        return

    if px >= GRID_W or py >= GRID_H:
        return

    inst = target_pack["inst"]

    inst.knockback_active = True

    inst.knockback_from = (
        tx,
        ty
    )

    inst.knockback_to = (
        px,
        py
    )

    inst.knockback_t = 0.0

    inst.knockback_runtime_skill = (
        runtime_skill
    )

    print(
        "TARGET PUSH START",
        px,
        py
    )

def end_runtime_skill(runtime_skill):

    combat = runtime_skill.combat
    o = combat.owner

    runtime_skill.running = False
    runtime_skill.finished = True

    combat.finalize_pending_dead_unit(
        runtime_skill.target_pack
    )

    # =====================================
    # CONSUME ACTION
    # =====================================

    o.max_actions -= 1

    o.battle_target_tiles = []

    o.selected_combat_action = None

    runtime_skill.user_pack["inst"].charge_running = False

    action_data = runtime_skill.action_data

    effect_type = getattr(
        action_data,
        "effect_type",
        ""
    )

    # =====================================
    # FIN TURN
    # =====================================

    if o.max_actions <= 0:

        o.battle_selected_unit = None

        o.battle_state = "idle"

        combat.end_battle_turn()

    else:

        o.battle_selected_unit = (
            runtime_skill.user_pack
        )

        # =====================================
        # MOVE SKILLS
        # =====================================

        if effect_type == "move":

            o.battle_state = "select_target"

            o.current_action_type = "attack"

            o.button_A_command = "Atacar"

            combat.build_battle_target_tiles(
                o.battle_selected_unit
            )

        # =====================================
        # NORMAL SKILLS
        # =====================================

        else:

            o.battle_state = "select_move"

            o.button_A_command = "Mover a"

            o.current_action_type = "select move"

            combat.build_battle_move_tiles(
                o.battle_selected_unit
            )

    parent = runtime_skill.data.get(
    "parent_runtime_skill"
    )

    if parent:

        parent.flags[
            "counter_finished"
        ] = True

    combat.active_runtime_skill = None

    print("RUNTIME SKILL END")


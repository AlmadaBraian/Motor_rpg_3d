import math

from pyopengltk import OpenGLFrame
from OpenGL.GL import *
from OpenGL.GLU import *

class ActorInstance:
    def __init__(self, actor_name):
        self.actor_name = actor_name

        self.offx = 0.0
        self.offy = 0.0
        self.offz = 0.0

        self.rot = 180

        self.animator = None

        # runtime controls
        self.move_f = False
        self.move_b = False
        self.move_l = False
        self.move_r = False

        self.rot_l = False
        self.rot_r = False

        self.fall_start_x = 0.0
        self.fall_start_y = 0.0

        self.last_move_dx = 0.0
        self.last_move_dy = 0.0

        self.state = "idle"

        self.animator = None

        self.facing = "espalda"
        self.visual_facing = "espalda"
        self.face_angle = 180
        self.inspect_timer = 0.0
        self.last_cam_yaw = None

        self.guard_mode = False

        self.crit_meter = 0.0

        self.selected_item_index = 0
        self.selected_special_index = 0

        self.is_npc = False
        self.npc_name = actor_name

        self.interact_radius = 1.2
        self.interact_text = "..."
        self.interact_once = False
        self.interacted = False

        self.trigger_combat = False
        self.trigger_event = ""

        self.vspeed = 0.0
        self.ground_z = 0.0
        self.on_ground = True

        self.is_jumping = False

        self._claw_started  = False

        self.jump_vspeed = 4.8          # impulso inicial hacia arriba
        self.jump_gravity = 9.0         # gravedad
        self.jump_target_z = self.ground_z

        self.jump_land_done = False

        self.mantle_dest_gx = 0
        self.mantle_dest_gy = 0

        self.battle_team = "player"
        self.battle_moved = False
        self.battle_acted = False
        self.battle_dead = False
        self.pending_remove = False
        self.is_battle_moving = False
        self.battle_move_timer = 0.0

        self.used_skill_this_turn = False
        self.used_item_this_turn = False
        self.battle_attacked = False

        self.charge_running = False
        self.is_mantling = False
        self.combat_using_mantle = False
        self.combat_mantle_target = None

        self.scripted_animation = False

        self.world_move_queue=[]
        self.is_world_moving=False
        self.withdraw_after_move=False

   
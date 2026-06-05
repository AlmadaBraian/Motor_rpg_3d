END_COMBAT_SCRIPT = [
    {"action":"withdraw_party"},

    {"action": "wait",
        "time": 2500
    }
]

NORMAL_ATTACK_SCRIPT = [

    {
        "action": "attack_camera"
    },
    {
        "action": "wait",
        "time": 600
    },

    {
        "action": "play_attack_animation"

    },

    {
        "action": "wait_animation",
        "target": "user"
    },

    {
        "action": "play_hit_animation"
    },
    {
        "action": "play_idle_animation"
    },
    {
        "action": "wait_animation",
        "target": "target"
    },

    {
        "action": "damage"
    },

    {
    "action": "check_counter"
    },

    {
        "action": "wait",
        "time": 300
    },

    {
        "action": "end_skill"
    }
]

GUN_ATTACK_SCRIPT = [

    {
        "action": "attack_camera"
    },
    {
        "action": "wait",
        "time": 600
    },
    {
      "action": "camera_look_actor",
      "actor": "user",
      "duration": 0.5
    },

    {
        "action": "wait",
        "time": 600
    },
    
    {
        "action": "play_animation",
        "animation_clip_dere": "prepare_pistol_dere",
        "animation_clip_izq": "prepare_pistol_izq",

    },

    {
        "action": "wait_animation",
        "target": "user"
    },
    {
        "action": "play_shoot_animation"

    },

    {
        "action": "wait_animation",
        "target": "user"
    },

    {
      "action": "camera_look_actor",
      "actor": "target",
      "duration": 0.5
    },

    {
        "action": "play_hit_animation"
    },
    {
        "action": "play_idle_animation"
    },
    {
        "action": "wait_animation",
        "target": "target"
    },

    {
        "action": "attack_camera"
    },

    {
        "action": "damage"
    },

    {
        "action": "wait",
        "time": 300
    },

    {
        "action": "end_skill"
    }
]
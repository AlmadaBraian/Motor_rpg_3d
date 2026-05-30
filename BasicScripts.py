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
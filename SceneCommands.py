SCENE_COMMANDS = {

    # =====================================
    # CONTROL
    # =====================================

    "wait": {
        "time": 1000
    },

    "wait_input": {},

    "wait_animation": {},

    "restore_map_music": {},

    "end_event": {},

    # =====================================
    # FADE
    # =====================================

    "fade_in": {
        "duration": 1.0
    },

    "fade_out": {
        "duration": 1.0
    },

    # =====================================
    # DIALOGOS
    # =====================================

    "show_dialog": {
        "speaker": "Narrador",
        "text": [
            "..."
        ]
    },

    # =====================================
    # VISUAL NOVEL
    # =====================================

    "vn_add_sprite": {
        "sprite": "",
        "image": "",
        "x": 0,
        "y": 0
    },

    "vn_show_sprite": {
        "sprite": "",
        "image": "",
        "x": 0,
        "y": 0
    },

    "vn_set_sprite": {
        "sprite": "",
        "image": "",
        "x": 0,
        "y": 0
    },

    "vn_hide_sprite": {
        "sprite": ""
    },

    "vn_remove_sprite": {
        "sprite": ""
    },

    "vn_clear": {},

    "vn_clear_sprites": {},

    "vn_start_animation": {
        "sprite": "",
        "animation": "",
        "x": 0,
        "y": 0,
        "speed": 300,
        "duration": 1.0,
        "wait": False
    },

    "vn_animation": {
        "sprite": "",
        "animation": "",
        "x": 0,
        "y": 0,
        "speed": 300,
        "duration": 1.0,
        "wait": False
    },

    "start_animation": {
        "sprite": "",
        "animation": "",
        "x": 0,
        "y": 0,
        "speed": 300,
        "duration": 1.0,
        "wait": False
    },

    "vn_wait_animation": {},

    "vn_wait_input": {},

    # =====================================
    # MENUS
    # =====================================

    "open_menu": {
        "title": "",
        "options": [],
        "x": 100,
        "y": 100,
        "w": 1
    },

    # =====================================
    # AUDIO
    # =====================================

    "audio_play": {
        "track": "bgm",
        "music": "",
        "volume": 1.0
    },

    "audio_pause": {
        "track": "bgm"
    },

    "audio_resume": {
        "track": "bgm"
    },

    "audio_stop": {
        "track": "bgm"
    },

    "audio_set_volume": {
        "track": "bgm",
        "volume": 1.0
    },

    "audio_change_volume": {
        "track": "bgm",
        "delta": 0.0
    },

    "audio_fade_volume": {
        "track": "bgm",
        "volume": 0.0,
        "duration": 1.0,
        "stop": False
    },

    "set_floor_audio": {
        "texture": "",
        "sound": "",
        "volume": 0.8,
        "cooldown": 0.25
    },

    # =====================================
    # CAMARA
    # =====================================

    "camera_follow_player": {},

    "camera_look_actor": {
        "actor": "",
        "height": 1.0,
        "yaw": 180,
        "pitch": 25,
        "distance": 5,
        "duration": 2.0
    },

    "camera_move": {
        "x": 0,
        "y": 0,
        "z": 0,
        "yaw": 180,
        "pitch": 25,
        "distance": 5,
        "duration": 2.0
    },

    # =====================================
    # PARTY
    # =====================================

    "deploy_party": {},

    "withdraw_party": {},

    "all_play_idle": {},

    # =====================================
    # ACTORES
    # =====================================

    "move_actor": {
        "actor": "",
        "direction": "down",
        "tiles": 1
    },

    "play_animation": {
        "actor_name": "",
        "animation_clip": ""
    },

    # =====================================
    # PLAYER
    # =====================================

    "lock_player": {},

    "unlock_player": {},

    # =====================================
    # COMBATE
    # =====================================

    "start_combat": {
        "execute_script_win": "win_combat.json",
        "execute_script_lose": "game_over.json"
    },

    # =====================================
    # UI
    # =====================================

    "show_ui": {},

    # =====================================
    # ESCENAS
    # =====================================

    "change_scene": {
        "scene_new": ""
    },

    "next_scene": {
        "scene_new": ""
    }
}


VN_SPRITE_ANIMATIONS = {
    "walk_right": {},
    "walk_left": {},
    "enter_left": {},
    "enter_right": {},
    "exit_left": {},
    "exit_right": {},
    "traveling_x": {},
    "traveling_y": {},
    "up": {},
    "down": {},
    "stay": {},
    "fade_in": {},
    "fade_out": {}
}

VN_TEXT_ANIMATIONS = {
    "float_up": {},
    "shake": {},
    "pulse": {},
    "typewriter": {},
    "fade_in": {},
    "fade_out": {},
    "popup": {},
    "ghost": {},
    "glow": {},
    "damage": {},
    "none": {}
}
# =========================================================
# RUNTIME MUSIC STATE
# =========================================================


def _get_audio_category(cmd):
    category = cmd.get("category", "sfx")

    if "music" in cmd:
        category = "music"
    elif "voice" in cmd:
        category = "voice"

    return category


def _get_audio_path(cmd):
    return cmd.get("sound", cmd.get("music", cmd.get("voice", "")))


def _is_combat_music(cmd, track_id, path, source):
    if cmd.get("combat_music", False):
        return True

    if cmd.get("map_music", None) is True:
        return False

    if source == "combat":
        return True

    key = f"{track_id} {path}".lower()
    return "combat" in key or "battle" in key


def _remember_map_music(owner, track_id, path, cmd, category):
    owner.current_map_music = {
        "track_id": track_id,
        "path": path,
        "volume": cmd.get("volume", 1.0),
        "loop": cmd.get("loop", category == "music"),
        "category": category,
        "fade_ms": cmd.get("fade_ms", 0)
    }


def play_runtime_audio(owner, cmd, source="world"):
    track_id = cmd.get("track", cmd.get("track_id", "sfx"))
    path = _get_audio_path(cmd)
    category = _get_audio_category(cmd)

    if category == "music":
        is_combat_music = _is_combat_music(cmd, track_id, path, source)

        if getattr(owner, "current_music", None):
            if hasattr(owner, "audio_manager"):
                owner.audio_manager.stop(
                    owner.current_music,
                    fade_ms=cmd.get("fade_ms", 0)
                )

        owner.current_music = track_id

        if is_combat_music:
            owner.current_combat_music = track_id
        else:
            owner.current_combat_music = None
            _remember_map_music(owner, track_id, path, cmd, category)

    print("PLAY:", track_id)

    if hasattr(owner, "audio_manager"):
        owner.audio_manager.play(
            track_id=track_id,
            path=path,
            volume=cmd.get("volume", 1.0),
            loop=cmd.get("loop", category == "music"),
            category=category,
            replace=cmd.get("replace", True),
            fade_ms=cmd.get("fade_ms", 0)
        )


def stop_runtime_audio(owner, cmd):
    track_id = cmd.get("track", cmd.get("track_id"))

    if hasattr(owner, "audio_manager"):
        owner.audio_manager.stop(
            track_id,
            fade_ms=cmd.get("fade_ms", 0)
        )

    if track_id and track_id == getattr(owner, "current_music", None):
        owner.current_music = None

    if track_id and track_id == getattr(owner, "current_combat_music", None):
        owner.current_combat_music = None

    map_music = getattr(owner, "current_map_music", None)

    if (
        track_id
        and map_music
        and track_id == map_music.get("track_id")
        and not cmd.get("keep_map_music", False)
    ):
        owner.current_map_music = None


def restore_map_music(owner, fade_ms=1000):
    map_music = getattr(owner, "current_map_music", None)

    if not map_music:
        return False

    track_id = map_music.get("track_id")
    path = map_music.get("path")

    if not track_id or not path:
        return False

    if getattr(owner, "current_music", None) == track_id:
        return True

    if hasattr(owner, "audio_manager"):
        owner.audio_manager.play(
            track_id=track_id,
            path=path,
            volume=map_music.get("volume", 1.0),
            loop=map_music.get("loop", True),
            category=map_music.get("category", "music"),
            replace=True,
            fade_ms=fade_ms
        )

    owner.current_music = track_id
    owner.current_combat_music = None

    print("RESTORE MAP MUSIC:", track_id)

    return True

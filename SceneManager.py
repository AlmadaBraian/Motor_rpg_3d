import copy
import json
import os

from VisualNovelScene import has_visual_novel_layer, is_visual_novel_scene


class RuntimeSceneManager:

    def __init__(self, owner=None):
        self.owner = owner
        self.current_scene_path = ""
        self.current_scene_name = ""
        self.current_scene_data = {}

    # =====================================================
    # PATHS
    # =====================================================

    def resolve_scene_path(self, scene_file):
        if not scene_file:
            return ""

        candidates = [scene_file]

        if not os.path.isabs(scene_file):
            base_dir = os.path.dirname(__file__)

            candidates.append(os.path.join(os.getcwd(), scene_file))
            candidates.append(os.path.join(base_dir, scene_file))
            candidates.append(os.path.join("scenes", os.path.basename(scene_file)))
            candidates.append(os.path.join(base_dir, "scenes", os.path.basename(scene_file)))

        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return candidate

        return scene_file

    # =====================================================
    # LOAD / NORMALIZE
    # =====================================================

    def load_scene_data(self, scene_file):
        scene_path = self.resolve_scene_path(scene_file)

        if not scene_path or not os.path.exists(scene_path):
            print("SCENE FILE NOT FOUND:", scene_file)
            return None, scene_path

        with open(scene_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            print("INVALID SCENE DATA:", scene_path)
            return None, scene_path

        self.current_scene_path = scene_path
        self.current_scene_name = data.get("scene", os.path.splitext(os.path.basename(scene_path))[0])
        self.current_scene_data = data

        return data, scene_path


    def get_scene_start_map(self, scene_data):
        if not isinstance(scene_data, dict):
            return ""

        return (
            scene_data.get("start_map")
            or scene_data.get("map")
            or scene_data.get("map_id")
            or scene_data.get("map_name")
            or ""
        )


    def is_visual_novel_scene(self, scene_data):
        return is_visual_novel_scene(scene_data)

    def get_scene_player_start(self, scene_data):
        if not isinstance(scene_data, dict):
            return None

        start = scene_data.get("player_start")

        if isinstance(start, dict):
            return start

        return None

    def get_scene_script(self, scene_file):
        data, scene_path = self.load_scene_data(scene_file)

        if data is None:
            return [], scene_path, {}

        return self.copy_script(data.get("script", [])), scene_path, data

    def copy_script(self, script):
        if not script:
            return []

        if isinstance(script, list):
            return copy.deepcopy(script)

        return []

    def normalize_script_source(self, source):
        if not source:
            return []

        if isinstance(source, list):
            return self.copy_script(source)

        if isinstance(source, dict):
            return self.copy_script(source.get("script", []))

        if isinstance(source, str):
            text = source.strip()

            if not text:
                return []

            scene_path = self.resolve_scene_path(text)

            if os.path.exists(scene_path):
                script, _path, _data = self.get_scene_script(scene_path)
                return script

            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                print("INVALID SCRIPT SOURCE:", text[:80])
                return []

            if isinstance(parsed, list):
                return self.copy_script(parsed)

            if isinstance(parsed, dict):
                return self.copy_script(parsed.get("script", []))

        return []

    # =====================================================
    # WORLD EVENT LIFECYCLE
    # =====================================================


    def apply_runtime_scene_mode(self, owner, scene_data):
        if scene_data is None:
            return

        if not hasattr(owner, "visual_novel_scene"):
            from VisualNovelScene import VisualNovelSceneState
            owner.visual_novel_scene = VisualNovelSceneState()

        if self.is_visual_novel_scene(scene_data):
            owner.runtime_scene_mode = "visual_novel"
            owner.visual_novel_scene.load_from_scene_data(scene_data)
            owner.runtime_world = None
            owner.show_ui = False
            return

        owner.runtime_scene_mode = "world"
        if has_visual_novel_layer(scene_data):
            owner.visual_novel_scene.load_from_scene_data(scene_data)
        else:
            owner.visual_novel_scene.reset()

        target_map = self.get_scene_start_map(scene_data)
        if target_map and hasattr(owner, "runtime"):
            owner.current_runtime_map_id = target_map
            owner.runtime_world = owner.runtime.build_runtime_world_copy(target_map)
            player_start = self.get_scene_player_start(scene_data)
            if player_start:
                owner.runtime.apply_runtime_player_start(player_start)

    def start_world_event(self, owner, scene_file):
        script, scene_path, data = self.get_scene_script(scene_file)

        if not script and not data:
            return False

        self.apply_runtime_scene_mode(owner, data)

        owner.current_event_data = data
        owner.current_event_scene_path = scene_path
        owner.current_event_scene_name = data.get("scene", "")
        owner.current_event_script = script
        owner.current_event_index = 0

        owner.world_event_running = True
        owner.world_event_locked = True

        owner.event_wait_timer = 0
        owner.event_wait_input = False
        owner.event_wait_move = None
        owner.event_wait_vn_animation = False
        owner.event_advance_block = False

        print("WORLD EVENT START:", scene_path)

        return True

    def start_world_script(self, owner, script, source_name="inline"):
        owner.current_event_data = {}
        owner.current_event_scene_path = ""
        owner.current_event_scene_name = source_name
        owner.current_event_script = self.normalize_script_source(script)
        owner.current_event_index = 0

        owner.world_event_running = True
        owner.world_event_locked = True

        owner.event_wait_timer = 0
        owner.event_wait_input = False
        owner.event_wait_move = None
        owner.event_wait_vn_animation = False
        owner.event_advance_block = False

        print("WORLD SCRIPT START:", source_name)

        return True

    def change_world_scene(self, owner, scene_file):
        return self.start_world_event(owner, scene_file)

    # =====================================================
    # COMBAT / SKILLS
    # =====================================================

    def build_combat_script(self, script_source):
        return self.normalize_script_source(script_source)


def get_runtime_scene_manager(owner):
    manager = getattr(owner, "scene_manager", None)

    if manager is None:
        manager = RuntimeSceneManager(owner)
        owner.scene_manager = manager

    return manager


def resolve_runtime_scene_path(scene_file):
    return RuntimeSceneManager().resolve_scene_path(scene_file)

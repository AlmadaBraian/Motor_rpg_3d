from config import CAMERA_PRESETS
from copy import deepcopy


class Camera:
    def __init__(self):
        self.reset()

    def reset(self):
        for preset_name in CAMERA_PRESETS:

            apply_camera_preset(self, CAMERA_PRESETS, preset_name)

def apply_camera_preset(cam, presets, preset_name):
    p = presets[preset_name]

    for k, v in p.items():
        setattr(cam, k, v)

def build_world_camera_snapshot(tool):
    return {
        "yaw": tool.runtime_cam_orbit,
        "pitch": tool.runtime_cam_target_pitch,
        "distance": tool.runtime_cam_target_distance,
        "height": tool.runtime_cam_target_height
    }
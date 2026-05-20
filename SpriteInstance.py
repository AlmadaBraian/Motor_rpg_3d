import math
from pyopengltk import OpenGLFrame
from OpenGL.GL import *
from OpenGL.GLU import *

class SpriteInstance:
    def __init__(self, asset_name):
        self.asset = asset_name

        self.offx = 0.0
        self.offy = 0.0
        self.offz = 0.0

        self.state = "idle"

        self.animator = None

        self.facing = "espalda"
        self.visual_facing = "espalda"
        self.inspect_timer = 0.0
        self.last_cam_yaw = None

    
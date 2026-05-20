class CameraKeyframe:
    def __init__(self, x, y, z, yaw, pitch, distance, duration=2.0):
        self.x = x
        self.y = y
        self.z = z

        self.yaw = yaw
        self.pitch = pitch
        self.distance = distance

        self.duration = duration
class Camera:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = 12
        self.y = 0
        self.z = 12

        self.yaw = 45
        self.pitch = 55

        self.distance = 35
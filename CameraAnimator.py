class CameraAnimator:
    def __init__(self, camera):
        self.camera = camera
        self.keys = []
        self.playing = False

        self.current_index = 0
        self.timer = 0

    def clear(self):
        self.keys = []
        self.playing = False
        self.current_index = 0
        self.timer = 0

    def add_key(self, key):
        self.keys.append(key)

    def play(self):
        if len(self.keys) < 2:
            return
        self.playing = True
        self.current_index = 0
        self.timer = 0

    def stop(self):
        self.playing = False

    def lerp(self, a, b, t):
        return a + (b - a) * t

    def update(self, dt):
        if not self.playing:
            return

        if self.current_index >= len(self.keys)-1:
            self.playing = False
            return

        k1 = self.keys[self.current_index]
        k2 = self.keys[self.current_index + 1]

        self.timer += dt

        dur = max(0.001, k2.duration)
        t = min(1.0, self.timer / dur)

        self.camera.x = self.lerp(k1.x, k2.x, t)
        self.camera.y = self.lerp(k1.y, k2.y, t)
        self.camera.z = self.lerp(k1.z, k2.z, t)

        self.camera.yaw = self.lerp(k1.yaw, k2.yaw, t)
        self.camera.pitch = self.lerp(k1.pitch, k2.pitch, t)
        self.camera.distance = self.lerp(k1.distance, k2.distance, t)

        if t >= 1.0:
            self.current_index += 1
            self.timer = 0
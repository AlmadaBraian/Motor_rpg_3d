class AnimatedTexture:
    
    def __init__(self):
        self.frames = 0              # lista de paths
        self.speed = 0               # segundos por frame
        self.loop = 0

    def get_current_frame(self, runtime_time):
        if not self.frames:
            return None

        idx = int(runtime_time / self.speed)

        if self.loop:
            idx = idx % len(self.frames)
        else:
            idx = min(idx, len(self.frames)-1)

        return self.frames[idx]
    
    
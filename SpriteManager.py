class SpriteSheet:
    def __init__(self, texture, fw, fh):
        self.texture = texture
        self.fw = fw
        self.fh = fh

        self.frames = []

    def add_row(self, count):
        for i in range(count):
            self.frames.append((i * self.fw, 0))

class AnimationClip:
    def __init__(self, name, frames, fps=6, loop=True):
        self.name = name
        self.frames = frames
        self.fps = fps
        self.loop = loop
        

class Animator:
    def __init__(self, clips):
        self.clips = {c.name: c for c in clips}
        self.current = None
        self.frame = 0
        self.timer = 0
        self.finished = False
        self.paused = False

    def play(self, name):

        self.finished = False

        if self.current == name:
            return
        if self.current != name:
            self.current = name
            self.frame = 0
            self.timer = 0
        print("ANIM PLAY:", name)

    def update(self, dt):

        if not self.current or getattr(self, "paused", False):
            print("paused")
            return

        if not self.current:
            return
        
        self.finished = False

        clip = self.clips[self.current]
        
        if not clip.frames: return

        if self.current not in self.clips:
            return


        raw = clip.frames[self.frame]

        if isinstance(raw, dict):
            dur = max(1, raw.get("dur", 1))
        else:
            dur = 1

        frame_time = (1.0 / max(1, clip.fps)) * dur

        self.timer += dt

        if self.timer > frame_time * 2:
            self.timer = frame_time

        while self.timer >= frame_time:
            self.timer -= frame_time
            self.frame += 1

            if self.frame >= len(clip.frames):

                if clip.loop:
                    self.frame = 0

                else:
                    self.frame = len(clip.frames) - 1
                    self.finished = True

            raw = clip.frames[self.frame]

            if isinstance(raw, dict):
                dur = max(1, raw.get("dur", 1))
            else:
                dur = 1

            frame_time = (1.0 / max(1, clip.fps)) * dur
        

        
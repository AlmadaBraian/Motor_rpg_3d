class RuntimeText:

    def __init__(self):

        self.text = ""

        self.x = 0
        self.y = 0

        self.base_x = 0
        self.base_y = 0

        self.scale = 1.0

        self.color = (1,1,1,1)

        self.visible = True

        self.elapsed = 0
        self.duration = 0

        self.animations = []

        self.finished = False
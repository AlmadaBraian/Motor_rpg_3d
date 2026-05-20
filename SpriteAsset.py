class SpriteAsset:
    def __init__(self, name, tex, image_path):
        self.name = name
        self.texture = tex
        self.image_path = image_path

        self.width = 0.8
        self.height = 1.6

        self.billboard = True
        self.mode = "sprite"

        self.sheet_cols = 8
        self.sheet_rows = 7
        self.frame_w = 73
        self.frame_h = 65

        self.base_clips = []
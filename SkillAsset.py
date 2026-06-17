class SkillAsset:

    def __init__(self, name="New Skill"):

        self.name = name
        self.description = ""

        self.sp_cost = 0
        self.range = 1

        self.target_type = "enemy"

        self.effect_type = "damage"

        self.power = 10

        self.status_effect = ""

        self.script = []

        self.animation_sprite = ""
        self.animation_effect = ""
        self.animation_clip_dere = ""
        self.animation_clip_izq = ""

        self.target_shape = "diamond"

        self.passive = False
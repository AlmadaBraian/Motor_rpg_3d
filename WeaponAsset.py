class WeaponAsset:

    def __init__(self, name="New Weapon"):

        self.name = name
        self.description = ""

        self.range = 1

        self.weapon_type = "mele" 
        
        self.use_bullets = False

        self.ammo_item = ""

        self.ammo_per_shot = 1

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
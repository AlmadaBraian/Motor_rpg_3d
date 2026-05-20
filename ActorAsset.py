class ActorAsset:
    def __init__(self, name, sprite_asset_name=""):
        self.name = name

        # main / npc / enemy / party
        self.kind = "npc"

        self.is_main = False
        self.interactive = True

        # script vinculado
        self.event_file = ""

       
        # =========================
        # RPG STATS
        # =========================
        self.level = 1

        self.hp = 10
        self.max_hp = 10

        self.sp = 25
        self.max_sp = 25

        self.atk = 10
        self.defense = 5
        self.magic = 5
        self.resistance = 5
        self.speed = 5

        self.move_range = 4
        self.attack_range = 1

        self.initiative = 10
        #Agregar al creador de actores
        self.attack_bonus = 2
        self.armor_class = 10
        self.damage_min = 1
        self.damage_max = 6
        self.body_type = "normal"
        #body_type
        # Delgado: 8 
        # Normal: 10 
        # Robusto: 12

        #############################

        # =========================
        # BATTLE
        # =========================
        self.team = "neutral"
        self.ai_mode = "idle"

        # =========================
        # INVENTORY
        # =========================
        self.inventory = []

        # =========================
        # EQUIPMENT
        # =========================
        self.weapon = ""
        self.armor = ""
        self.accessory = ""

        # =========================
        # SKILLS
        # =========================
        self.skills = []

        # =========================
        # GROWTH
        # =========================
        self.exp_reward = 0
        self.gold_reward = 0

        # soporte multiple sprite sheets
        self.sprite_sheets = []

        if sprite_asset_name:
            self.sprite_sheets.append(sprite_asset_name)
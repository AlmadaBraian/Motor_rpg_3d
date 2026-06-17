import json
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from ItemAsset import ItemAsset
from SkillAsset import SkillAsset
from WeaponAsset import WeaponAsset


class AssetEditor(tk.Toplevel):

    ASSET_CONFIG = {

        "Skill": {
            "dict": "skills",
            "class": SkillAsset,
            "fields": [
                "sp_cost",
                "power",
                "range",
                "effect_type",
                "target_type",
                "target_shape",
                "status_effect",
                "animation_sprite",
                "animation_effect",
                "animation_clip_dere",
                "animation_clip_izq",
                "passive"
            ]
        },

        "Item": {
            "dict": "items",
            "class": ItemAsset,
            "fields": [
                "consumable",
                "price",
                "power",
                "range",
                "effect_type",
                "target_type",
                "target_shape"
            ]
        },

        "Weapon": {
            "dict": "weapons",
            "class": WeaponAsset,
            "fields": [
                "power",
                "range",
                "effect_type",
                "target_type",
                "weapon_type",
                "use_bullets",
                "ammo_item",
                "ammo_per_shot",
                "target_shape",
                "status_effect",
                "animation_sprite",
                "animation_effect",
                "animation_clip_dere",
                "animation_clip_izq"
            ]
        }
    }

    def __init__(self, owner):

        super().__init__()

        self.owner = owner

        self.current_asset = None

        self.title("Asset Database")
        self.geometry("1000x750")

        self.build_ui()

        self.refresh_asset_list()

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        left = tk.Frame(self)
        left.pack(side="left", fill="y")

        tk.Label(
            left,
            text="Asset Type"
        ).pack(fill="x")

        self.asset_type_combo = ttk.Combobox(
            left,
            state="readonly"
        )

        self.asset_type_combo["values"] = [
            "Skill",
            "Item",
            "Weapon"
        ]

        self.asset_type_combo.set("Skill")

        self.asset_type_combo.pack(fill="x")

        self.asset_type_combo.bind(
            "<<ComboboxSelected>>",
            self.on_asset_type_changed
        )

        self.asset_listbox = tk.Listbox(
            left,
            width=30
        )

        self.asset_listbox.pack(
            fill="y",
            expand=True
        )

        self.asset_listbox.bind(
            "<<ListboxSelect>>",
            self.load_asset
        )

        btns = tk.Frame(left)
        btns.pack(fill="x")

        tk.Button(
            btns,
            text="NEW",
            command=self.new_asset
        ).pack(fill="x")

        tk.Button(
            btns,
            text="SAVE",
            command=self.save_asset
        ).pack(fill="x")

        # ======================================

        right = tk.Frame(self)
        right.pack(
            side="left",
            fill="both",
            expand=True
        )

        tk.Label(
            right,
            text="Name"
        ).pack()

        self.name_entry = tk.Entry(right)

        self.name_entry.pack(
            fill="x",
            padx=10
        )

        tk.Label(
            right,
            text="Description"
        ).pack()

        self.desc_text = tk.Text(
            right,
            height=4
        )

        self.desc_text.pack(
            fill="x",
            padx=10
        )

        # ======================================

        self.stats = tk.LabelFrame(
            right,
            text="Stats"
        )

        self.stats.pack(
            fill="x",
            padx=10,
            pady=5
        )

        self.rows = {}

        # ======================================
        # ammo_per_shot
        # ======================================

        row = tk.Frame(self.stats)

        tk.Label(
            row,
            text="ammo per shot",
            width=20,
            anchor="w"
        ).pack(side="left")

        self.ammo_per_shot_entry = tk.Entry(row)

        self.ammo_per_shot_entry.pack(
            side="left"
        )

        self.rows["ammo_per_shot"] = row

        # ======================================
        # ammo_item
        # ======================================

        row = tk.Frame(self.stats)

        tk.Label(
            row,
            text="ammo item",
            width=20,
            anchor="w"
        ).pack(side="left")

        self.ammo_item_combo = ttk.Combobox(
            row,
            state="readonly"
        )

        self.ammo_item_combo["values"] = [
            "9mm Ammo",
            "12 Gauge Shell",
            "7.62 Ammo"
            
        ]

        self.ammo_item_combo.pack(side="left")

        self.rows["ammo_item"] = row

        # ======================================
        # SP COST
        # ======================================

        row = tk.Frame(self.stats)

        tk.Label(
            row,
            text="SP Cost",
            width=20,
            anchor="w"
        ).pack(side="left")

        self.sp_cost_entry = tk.Entry(row)

        self.sp_cost_entry.pack(
            side="left"
        )

        self.rows["sp_cost"] = row

        # ======================================
        # POWER
        # ======================================

        row = tk.Frame(self.stats)

        tk.Label(
            row,
            text="Power",
            width=20,
            anchor="w"
        ).pack(side="left")

        self.power_entry = tk.Entry(row)

        self.power_entry.pack(side="left")

        self.rows["power"] = row

        # ======================================
        # PRICE
        # ======================================

        row = tk.Frame(self.stats)

        tk.Label(
            row,
            text="Price",
            width=20,
            anchor="w"
        ).pack(side="left")

        self.price_entry = tk.Entry(row)

        self.price_entry.pack(side="left")

        self.rows["price"] = row

        # ======================================
        # RANGE
        # ======================================

        row = tk.Frame(self.stats)

        tk.Label(
            row,
            text="Range",
            width=20,
            anchor="w"
        ).pack(side="left")

        self.range_entry = tk.Entry(row)

        self.range_entry.pack(side="left")

        self.rows["range"] = row

        # ======================================
        # CONSUMABLE
        # ======================================

        row = tk.Frame(self.stats)

        self.consumable_var = tk.BooleanVar()

        tk.Checkbutton(
            row,
            text="Consumable",
            variable=self.consumable_var
        ).pack(side="left")

        self.rows["consumable"] = row

        # ======================================
        # PASSIVE
        # ======================================

        row = tk.Frame(self.stats)

        self.passive_var = tk.BooleanVar()

        tk.Checkbutton(
            row,
            text="Passive",
            variable=self.passive_var
        ).pack(side="left")

        self.rows["passive"] = row

        # ======================================
        # EFFECT
        # ======================================

        row = tk.Frame(self.stats)

        tk.Label(
            row,
            text="Effect",
            width=20,
            anchor="w"
        ).pack(side="left")

        self.effect_combo = ttk.Combobox(
            row,
            state="readonly"
        )

        self.effect_combo["values"] = [
            "damage",
            "heal",
            "buff_attack",
            "buff_defense",
            "buff_speed",
            "revive",
            "status",
            "script"
        ]

        self.effect_combo.pack(side="left")

        self.rows["effect_type"] = row

        # ======================================

        row = tk.Frame(self.stats)

        tk.Label(
            row,
            text="Target",
            width=20,
            anchor="w"
        ).pack(side="left")

        self.target_combo = ttk.Combobox(
            row,
            state="readonly"
        )

        self.target_combo["values"] = [
            "enemy",
            "ally",
            "self",
            "all_enemies",
            "all_allies",
            "tile"
        ]

        self.target_combo.pack(side="left")

        self.rows["target_type"] = row

        # ======================================

        row = tk.Frame(self.stats)

        tk.Label(
            row,
            text="Weapon Type",
            width=20,
            anchor="w"
        ).pack(side="left")

        self.weapon_type_combo = ttk.Combobox(
            row,
            state="readonly"
        )

        self.weapon_type_combo["values"] = [
            "mele",
            "pistol"
        ]

        self.weapon_type_combo.pack(side="left")

        self.rows["weapon_type"] = row

        # ======================================

        row = tk.Frame(self.stats)

        self.use_bullets_var = tk.BooleanVar()

        tk.Checkbutton(
            row,
            text="Use Bullets",
            variable=self.use_bullets_var
        ).pack(side="left")

        self.rows["use_bullets"] = row

        # ======================================

        row = tk.Frame(self.stats)

        tk.Label(
            row,
            text="Target Shape",
            width=20,
            anchor="w"
        ).pack(side="left")

        self.target_shape_combo = ttk.Combobox(
            row,
            state="readonly"
        )

        self.target_shape_combo["values"] = [
            "diamond",
            "cross",
            "line",
            "square",
            "ring",
            "cone"
        ]

        self.target_shape_combo.pack(side="left")

        self.rows["target_shape"] = row

        # ======================================

        row = tk.Frame(self.stats)

        tk.Label(
            row,
            text="Status",
            width=20,
            anchor="w"
        ).pack(side="left")

        self.status_entry = tk.Entry(row)

        self.status_entry.pack(side="left")

        self.rows["status_effect"] = row

        # ======================================

        row = tk.Frame(self.stats)

        tk.Label(
            row,
            text="Anim Sprite",
            width=20,
            anchor="w"
        ).pack(side="left")

        self.anim_sprite_combo = ttk.Combobox(
            row,
            state="readonly"
        )

        self.anim_sprite_combo["values"] = list(
            self.owner.sprites.keys()
        )

        self.anim_sprite_combo.pack(side="left")

        self.anim_sprite_combo.bind(
            "<<ComboboxSelected>>",
            self.refresh_animation_clips
        )

        self.rows["animation_sprite"] = row

        # ======================================

        row = tk.Frame(self.stats)

        tk.Label(
            row,
            text="Anim Effect",
            width=20,
            anchor="w"
        ).pack(side="left")

        self.anim_effect_entry = tk.Entry(row)

        self.anim_effect_entry.pack(side="left")

        self.rows["animation_effect"] = row

        # ======================================

        row = tk.Frame(self.stats)

        tk.Label(
            row,
            text="Clip Right",
            width=20,
            anchor="w"
        ).pack(side="left")

        self.clip_dere_combo = ttk.Combobox(
            row,
            state="readonly"
        )

        self.clip_dere_combo.pack(side="left")

        self.rows["animation_clip_dere"] = row

        # ======================================

        row = tk.Frame(self.stats)

        tk.Label(
            row,
            text="Clip Left",
            width=20,
            anchor="w"
        ).pack(side="left")

        self.clip_izq_combo = ttk.Combobox(
            row,
            state="readonly"
        )

        self.clip_izq_combo.pack(side="left")

        self.rows["animation_clip_izq"] = row

        # ======================================

        tk.Label(
            right,
            text="Script"
        ).pack()

        self.script_text = tk.Text(
            right,
            height=12
        )

        self.script_text.pack(
            fill="both",
            expand=True,
            padx=10
        )

        self.update_visible_fields()

    # =====================================================

    def get_asset_dict(self):

        cfg = self.ASSET_CONFIG[
            self.asset_type_combo.get()
        ]

        return getattr(
            self.owner,
            cfg["dict"]
        )

    # =====================================================

    def refresh_asset_list(self):

        self.asset_listbox.delete(
            0,
            tk.END
        )

        for name in self.get_asset_dict():
            self.asset_listbox.insert(
                tk.END,
                name
            )

    # =====================================================

    def on_asset_type_changed(self, evt=None):

        self.current_asset = None

        self.refresh_asset_list()

        self.update_visible_fields()

    # =====================================================

    def update_visible_fields(self):

        asset_type = self.asset_type_combo.get()

        fields = self.ASSET_CONFIG[
            asset_type
        ]["fields"]

        for row in self.rows.values():
            row.pack_forget()

        for field in fields:
            self.rows[field].pack(
                fill="x",
                padx=5,
                pady=2
            )

    # =====================================================

    def refresh_animation_clips(self, evt=None):

        sprite_name = self.anim_sprite_combo.get()

        if sprite_name not in self.owner.sprites:
            return

        sprite = self.owner.sprites[
            sprite_name
        ]

        clips = []

        if hasattr(sprite, "base_clips"):

            for clip in sprite.base_clips:
                clips.append(clip.name)

        self.clip_dere_combo["values"] = clips
        self.clip_izq_combo["values"] = clips

    # =====================================================

    def new_asset(self):

        cls = self.ASSET_CONFIG[
            self.asset_type_combo.get()
        ]["class"]

        asset = cls()

        self.get_asset_dict()[
            asset.name
        ] = asset

        self.refresh_asset_list()

    # =====================================================

    def load_asset(self, evt=None):

        sel = self.asset_listbox.curselection()

        if not sel:
            return

        name = self.asset_listbox.get(
            sel[0]
        )

        asset = self.get_asset_dict()[name]

        self.current_asset = asset

        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, asset.name)

        self.desc_text.delete("1.0", tk.END)
        self.desc_text.insert(
            "1.0",
            asset.description
        )

        self.script_text.delete("1.0", tk.END)
        self.script_text.insert(
            "1.0",
            str(asset.script)
        )

        self.power_entry.delete(0, tk.END)
        self.power_entry.insert(
            0,
            getattr(asset, "power", "")
        )

        self.price_entry.delete(0, tk.END)
        self.price_entry.insert(
            0,
            getattr(asset, "price", "")
        )

        self.range_entry.delete(0, tk.END)
        self.range_entry.insert(
            0,
            getattr(asset, "range", "")
        )

        self.sp_cost_entry.delete(0, tk.END)
        self.sp_cost_entry.insert(
            0,
            getattr(asset, "sp_cost", "")
        )

        self.ammo_per_shot_entry.delete(0, tk.END)
        self.ammo_per_shot_entry.insert(
            0,
            getattr(asset, "ammo_per_shot", "")
        )

        self.effect_combo.set(
            getattr(asset, "effect_type", "")
        )

        self.ammo_item_combo.set(
            getattr(asset, "ammo_item", "")
        )

        self.target_combo.set(
            getattr(asset, "target_type", "")
        )

        self.weapon_type_combo.set(
            getattr(asset, "weapon_type", "")
        )

        self.use_bullets_var.set(
            getattr(asset, "use_bullets", False)
        )

        self.target_shape_combo.set(
            getattr(asset, "target_shape", "diamond")
        )

        self.status_entry.delete(0, tk.END)
        self.status_entry.insert(
            0,
            getattr(asset, "status_effect", "")
        )

        self.consumable_var.set(
            getattr(asset, "consumable", True)
        )

        self.passive_var.set(
            getattr(asset, "passive", False)
        )

        self.anim_sprite_combo.set(
            getattr(asset, "animation_sprite", "")
        )

        self.anim_effect_entry.delete(0, tk.END)
        self.anim_effect_entry.insert(
            0,
            getattr(asset, "animation_effect", "")
        )

        self.refresh_animation_clips()

        self.clip_dere_combo.set(
            getattr(asset, "animation_clip_dere", "")
        )

        self.clip_izq_combo.set(
            getattr(asset, "animation_clip_izq", "")
        )

    # =====================================================

    def save_asset(self):

        if self.current_asset:

            asset = self.current_asset

        else:

            cls = self.ASSET_CONFIG[
                self.asset_type_combo.get()
            ]["class"]

            asset = cls()

        old_name = asset.name

        asset.name = self.name_entry.get()

        asset.description = self.desc_text.get(
            "1.0",
            tk.END
        ).strip()

        script_text = self.script_text.get(
            "1.0",
            tk.END
        ).strip()

        try:
            json.loads(script_text)
        except Exception as e:
            messagebox.showerror(
                "Script Error",
                str(e)
            )
            return

        asset.script = script_text

        if hasattr(asset, "power"):
            asset.power = int(self.power_entry.get() or 0)

        if hasattr(asset, "price"):
            asset.price = int(self.price_entry.get() or 0)

        if hasattr(asset, "range"):
            asset.range = int(self.range_entry.get() or 0)

        if hasattr(asset, "sp_cost"):
            asset.sp_cost = int(self.sp_cost_entry.get() or 0)

        if hasattr(asset, "ammo_per_shot"):
            asset.ammo_per_shot = int(self.ammo_per_shot_entry.get() or 0)

        if hasattr(asset, "effect_type"):
            asset.effect_type = self.effect_combo.get()

        if hasattr(asset, "ammo_item"):
            asset.ammo_item = self.ammo_item_combo.get()

        if hasattr(asset, "target_type"):
            asset.target_type = self.target_combo.get()

        if hasattr(asset, "weapon_type"):
            asset.weapon_type = self.weapon_type_combo.get()

        if hasattr(asset, "target_shape"):
            asset.target_shape = self.target_shape_combo.get()

        if hasattr(asset, "status_effect"):
            asset.status_effect = self.status_entry.get()

        if hasattr(asset, "consumable"):
            asset.consumable = self.consumable_var.get()

        if hasattr(asset, "passive"):
            asset.passive = self.passive_var.get()

        if hasattr(asset, "use_bullets"):
            asset.use_bullets = self.use_bullets_var.get()

        if hasattr(asset, "animation_sprite"):
            asset.animation_sprite = self.anim_sprite_combo.get()

        if hasattr(asset, "animation_effect"):
            asset.animation_effect = self.anim_effect_entry.get()

        if hasattr(asset, "animation_clip_dere"):
            asset.animation_clip_dere = self.clip_dere_combo.get()

        if hasattr(asset, "animation_clip_izq"):
            asset.animation_clip_izq = self.clip_izq_combo.get()

        assets = self.get_asset_dict()

        if old_name in assets:
            del assets[old_name]

        assets[asset.name] = asset

        self.refresh_asset_list()
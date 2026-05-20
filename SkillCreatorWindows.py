import os
import tkinter as tk
from tkinter import ttk, simpledialog, filedialog
from tkinter import messagebox

from SkillAsset import SkillAsset

def open_skill_editor(self):

    win = tk.Toplevel()
    win.title("Skill Database")
    win.geometry("900x700")

    # =====================================
    # LEFT PANEL
    # =====================================

    left = tk.Frame(win)
    left.pack(side="left", fill="y")

    skill_listbox = tk.Listbox(left, width=30)
    skill_listbox.pack(fill="y", expand=True)

    for skill_name in self.skills:
        skill_listbox.insert(tk.END, skill_name)

    # =====================================
    # RIGHT PANEL
    # =====================================

    right = tk.Frame(win)
    right.pack(side="left", fill="both", expand=True)

    tk.Label(right, text="Skill Name").pack()

    name_entry = tk.Entry(right)
    name_entry.pack(fill="x", padx=10)

    tk.Label(right, text="Description").pack()

    desc_text = tk.Text(right, height=4)
    desc_text.pack(fill="x", padx=10)

    # =====================================
    # STATS
    # =====================================

    stats = tk.LabelFrame(right, text="Stats")
    stats.pack(fill="x", padx=10, pady=5)

    tk.Label(stats, text="SP Cost").grid(row=0,column=0)

    sp_entry = tk.Entry(stats, width=8)
    sp_entry.grid(row=0,column=1)

    tk.Label(stats, text="Power").grid(row=0,column=2)

    power_entry = tk.Entry(stats, width=8)
    power_entry.grid(row=0,column=3)

    tk.Label(stats, text="Anim Sprite").grid(row=0,column=4)

    anim_sprite_combo = ttk.Combobox(
        stats,
        state="readonly"
    )

    anim_sprite_combo["values"] = list(self.sprites.keys())

    anim_sprite_combo.grid(row=0,column=5)

    tk.Label(stats, text="Anim Clip").grid(row=1,column=4)

    animation_combo = ttk.Combobox(
        stats,
        state="readonly"
    )

    animation_combo.grid(row=1,column=5)


    tk.Label(stats, text="Target Shape").grid(row=2,column=4)

    target_shape_combo = ttk.Combobox(
        stats,
        state="readonly"
    )

    target_shape_combo["values"] = [
        "diamond",
        "cross",
        "line",
        "square",
        "ring",
        "cone"
    ]

    target_shape_combo.set("diamond")

    target_shape_combo.grid(row=2,column=5)

    tk.Label(stats, text="Range").grid(row=1,column=0)

    range_entry = tk.Entry(stats, width=8)
    range_entry.grid(row=1,column=1)

    # =====================================
    # EFFECT TYPE
    # =====================================

    tk.Label(stats, text="Effect").grid(row=1,column=2)

    effect_combo = ttk.Combobox(stats, state="readonly")

    effect_combo["values"] = [
        "damage",
        "heal",
        "move",
        "buff_attack",
        "buff_defense",
        "buff_speed",
        "revive",
        "status",
        "script"
    ]

    effect_combo.set("damage")

    effect_combo.grid(row=1,column=3)

    # =====================================
    # TARGET TYPE
    # =====================================

    tk.Label(stats, text="Target").grid(row=2,column=0)

    target_combo = ttk.Combobox(stats, state="readonly")

    target_combo["values"] = [
        "enemy",
        "ally",
        "self",
        "all_enemies",
        "all_allies",
        "tile"
    ]

    target_combo.set("enemy")

    target_combo.grid(row=2,column=1)

    # =====================================
    # STATUS
    # =====================================

    tk.Label(stats, text="Status").grid(row=2,column=2)

    status_entry = tk.Entry(stats)

    status_entry.grid(row=2,column=3)

    # =====================================
    # SCRIPT
    # =====================================

    tk.Label(right, text="Script").pack()

    script_text = tk.Text(right, height=12)
    script_text.pack(fill="both", expand=True, padx=10)

    current_skill = [None]

    def refresh_animation_clips(evt=None):

        sprite_name = anim_sprite_combo.get()

        if sprite_name not in self.sprites:
            return

        sprite = self.sprites[sprite_name]

        clips = []

        if hasattr(sprite, "base_clips"):

            for clip in sprite.base_clips:
                clips.append(clip.name)

        animation_combo["values"] = clips

        if clips:
            animation_combo.set(clips[0])

    anim_sprite_combo.bind(
    "<<ComboboxSelected>>",
    refresh_animation_clips
    )

    def load_skill(evt=None):

        sel = skill_listbox.curselection()

        if not sel:
            return

        skill_name = skill_listbox.get(sel[0])

        skill = self.skills[skill_name]

        current_skill[0] = skill

        name_entry.delete(0, tk.END)
        name_entry.insert(0, skill.name)

        desc_text.delete("1.0", tk.END)
        desc_text.insert("1.0", skill.description)

        sp_entry.delete(0, tk.END)
        sp_entry.insert(0, skill.sp_cost)

        power_entry.delete(0, tk.END)
        power_entry.insert(0, skill.power)

        range_entry.delete(0, tk.END)
        range_entry.insert(0, skill.range)

        effect_combo.set(skill.effect_type)

        target_combo.set(skill.target_type)

        target_shape_combo.set(skill.target_shape)

        status_entry.delete(0, tk.END)
        status_entry.insert(0, skill.status_effect)

        anim_sprite_combo.set(skill.animation_sprite)

        refresh_animation_clips()

        animation_combo.set(skill.animation_clip)

        script_text.delete("1.0", tk.END)
        script_text.insert("1.0", skill.script)

    skill_listbox.bind("<<ListboxSelect>>", load_skill)

    def new_skill():

        skill = SkillAsset()

        self.skills[skill.name] = skill

        skill_listbox.insert(tk.END, skill.name)

    def save_skill():

        if current_skill[0]:

            skill = current_skill[0]

        else:

            skill = SkillAsset()

        old_name = skill.name

        skill.name = name_entry.get()

        skill.description = desc_text.get("1.0", tk.END).strip()

        skill.sp_cost = int(sp_entry.get())

        skill.power = int(power_entry.get())

        skill.range = int(range_entry.get())

        skill.effect_type = effect_combo.get()

        skill.target_type = target_combo.get()

        skill.target_shape = target_shape_combo.get()

        skill.status_effect = status_entry.get()

        skill.script = script_text.get("1.0", tk.END)

        skill.animation_sprite = anim_sprite_combo.get()

        skill.animation_clip = animation_combo.get()

        if old_name in self.skills:
            del self.skills[old_name]

        self.skills[skill.name] = skill

        skill_listbox.delete(0, tk.END)

        for s in self.skills:
            skill_listbox.insert(tk.END, s)

    btns = tk.Frame(left)
    btns.pack(fill="x")

    tk.Button(
        btns,
        text="NEW",
        command=new_skill
    ).pack(fill="x")

    tk.Button(
        btns,
        text="SAVE",
        command=save_skill
    ).pack(fill="x")
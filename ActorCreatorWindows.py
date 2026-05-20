import os
import tkinter as tk
from tkinter import ttk, simpledialog, filedialog
from tkinter import messagebox

from ActorAsset import ActorAsset

def open_actor_creator_window(self, actor_name=None):
        win = tk.Toplevel()
        win.title("Actor Database Editor")
        win.geometry("650x900")

        editing_actor = None

        if actor_name:
            editing_actor = self.actors.get(actor_name)

        # ===============================
        # BASIC INFO
        # ===============================
        tk.Label(win, text="Actor Name").pack()
        name_entry = tk.Entry(win)
        name_entry.pack(fill="x", padx=10)

        tk.Label(win, text="Actor Type").pack()
        type_combo = ttk.Combobox(win, state="readonly")
        type_combo["values"] = ["main", "npc", "enemy", "party"]
        type_combo.set("npc")
        type_combo.pack(fill="x", padx=10)

        #tk.Label(win, text="Linked Event JSON").pack()

        #scene_files = []
        #if os.path.exists("scenes"):
         #   scene_files = [f for f in os.listdir("scenes") if f.endswith(".json")]

        #event_combo = ttk.Combobox(win, state="readonly")
        #event_combo["values"] = scene_files
        #if scene_files:
         #   event_combo.set(scene_files[0])
        #event_combo.pack(fill="x", padx=10)

        combat_frame = tk.LabelFrame(win, text="Combat Stats")
        combat_frame.pack(fill="x", padx=10, pady=8)

        tk.Label(combat_frame, text="HP").grid(row=0,column=0)
        hp_entry = tk.Entry(combat_frame, width=8)
        #hp_entry.insert(0,"100")
        hp_entry.grid(row=0,column=1)

        tk.Label(combat_frame, text="SP").grid(row=0,column=2)
        sp_entry = tk.Entry(combat_frame, width=8)
        #sp_entry.insert(0,"25")
        sp_entry.grid(row=0,column=3)

        tk.Label(combat_frame, text="ATK").grid(row=1,column=0)
        atk_entry = tk.Entry(combat_frame,width=6)
        #atk_entry.insert(0,"10")
        atk_entry.grid(row=1,column=1)

        tk.Label(combat_frame, text="Iniciativa").grid(row=3,column=2)
        iniciativa = tk.Entry(combat_frame,width=6)
        #iniciativa.insert(0,"10")
        iniciativa.grid(row=3,column=3)

        tk.Label(combat_frame, text="DEF").grid(row=1,column=2)
        def_entry = tk.Entry(combat_frame,width=6)
        #def_entry.insert(0,"5")
        def_entry.grid(row=1,column=3)

        tk.Label(combat_frame, text="MAG").grid(row=2,column=0)
        mag_entry = tk.Entry(combat_frame,width=6)
        #mag_entry.insert(0,"5")
        mag_entry.grid(row=2,column=1)

        tk.Label(combat_frame, text="RES").grid(row=2,column=2)
        res_entry = tk.Entry(combat_frame,width=6)
        #res_entry.insert(0,"5")
        res_entry.grid(row=2,column=3)

        tk.Label(combat_frame, text="SPD").grid(row=3,column=0)
        spd_entry = tk.Entry(combat_frame,width=6)
        #spd_entry.insert(0,"5")
        spd_entry.grid(row=3,column=1)

        tk.Label(combat_frame, text="Atk bonus").grid(row=0,column=4)
        atk_bonus_entry = tk.Entry(combat_frame,width=6)
        #atk_bonus_entry.insert(0,"2")
        atk_bonus_entry.grid(row=0,column=5)

        tk.Label(combat_frame, text="CA").grid(row=1,column=4)
        CA_entry = tk.Entry(combat_frame,width=6)
        #CA_entry.insert(0,"10")
        CA_entry.grid(row=1,column=5)

        tk.Label(combat_frame, text="Damage max").grid(row=2,column=4)
        damage_max_entry = tk.Entry(combat_frame,width=6)
        #damage_max_entry.insert(0,"6")
        damage_max_entry.grid(row=2,column=5)

        tk.Label(combat_frame, text="Body Type").grid(row=3,column=4)
        body_type_combo = ttk.Combobox(combat_frame, state="readonly")
        body_type_combo["values"] = ["delgado","normal","robusto"]
        body_type_combo.set("normal")
        body_type_combo.grid(row=3,column=5,columnspan=2,sticky="ew")

        tk.Label(combat_frame, text="Battle Team").grid(row=0,column=6)

        team_combo = ttk.Combobox(combat_frame, state="readonly")
        team_combo["values"] = ["player","enemy","ally","neutral"]
        team_combo.set("neutral")
        team_combo.grid(row=0,column=7,columnspan=2,sticky="ew")

        tk.Label(combat_frame, text="AI").grid(row=1,column=6)

        ai_combo = ttk.Combobox(combat_frame, state="readonly")
        ai_combo["values"] = [
            "idle",
            "aggressive",
            "guardian",
            "follow",
            "boss"
        ]
        ai_combo.set("idle")
        ai_combo.grid(row=1,column=7,columnspan=2,sticky="ew")

        tk.Label(combat_frame, text="Move").grid(row=4,column=0)
        move_entry = tk.Entry(combat_frame,width=6)
        #move_entry.insert(0,"4")
        move_entry.grid(row=4,column=1)

        tk.Label(combat_frame, text="Range").grid(row=4,column=2)
        range_entry = tk.Entry(combat_frame,width=6)
        #range_entry.insert(0,"1")
        range_entry.grid(row=4,column=3)

        special_frame = tk.LabelFrame(win, text="Special")
        special_frame.pack(fill="both", expand=True, padx=10, pady=8)

        skill_selector = ttk.Combobox(special_frame, state="readonly")
        skill_selector["values"] = list(self.skills.keys())
        skill_selector.pack(fill="x", pady=4)

        special_list = tk.Listbox(special_frame, height=5)
        special_list.pack(fill="both", expand=True)

        # ==================================
        # special BUTTONS
        # ==================================

        special_buttons = tk.Frame(special_frame)
        special_buttons.pack(fill="x", pady=4)

        def add_special_item():

            special_name = skill_selector.get()

            if not special_name:
                return

            # evitar duplicados
            existing = special_list.get(0, tk.END)

            if special_name in existing:
                return

            special_list.insert(tk.END, special_name)

        def remove_special_item():

            sel = special_list.curselection()

            if not sel:
                return

            special_list.delete(sel[0])

        tk.Button(
            special_buttons,
            text="ADD SPECIAL",
            command=add_special_item
        ).pack(side="left", padx=2)

        tk.Button(
            special_buttons,
            text="REMOVE SPECIAL",
            command=remove_special_item
        ).pack(side="left", padx=2)

        inv_frame = tk.LabelFrame(win, text="Inventory")
        inv_frame.pack(fill="both", expand=True, padx=10, pady=8)

        item_selector = ttk.Combobox(inv_frame, state="readonly")
        item_selector["values"] = list(self.items.keys())
        item_selector.pack(fill="x", pady=4)

        inventory_list = tk.Listbox(inv_frame, height=5)
        inventory_list.pack(fill="both", expand=True)

        # ==================================
        # INVENTORY BUTTONS
        # ==================================

        inv_buttons = tk.Frame(inv_frame)
        inv_buttons.pack(fill="x", pady=4)

        def add_inventory_item():

            item_name = item_selector.get()

            if not item_name:
                return

            # evitar duplicados
            existing = inventory_list.get(0, tk.END)

            if item_name in existing:
                return

            inventory_list.insert(tk.END, item_name)

        def remove_inventory_item():

            sel = inventory_list.curselection()

            if not sel:
                return

            inventory_list.delete(sel[0])

        tk.Button(
            inv_buttons,
            text="ADD ITEM",
            command=add_inventory_item
        ).pack(side="left", padx=2)

        tk.Button(
            inv_buttons,
            text="REMOVE ITEM",
            command=remove_inventory_item
        ).pack(side="left", padx=2)

        # ===============================
        # SPRITE ASSET SELECTOR
        # ===============================
        tk.Label(win, text="Available Sprite Assets").pack(pady=8)

        sprite_combo = ttk.Combobox(win, state="readonly")
        sprite_combo["values"] = list(self.sprites.keys())
        if self.sprites:
            sprite_combo.set(list(self.sprites.keys())[0])
        sprite_combo.pack(fill="x", padx=10)

        actor_sheet_list = tk.Listbox(win, height=8)
        actor_sheet_list.pack(fill="both", expand=True, padx=10, pady=8)

        # ===============================
        # IMPORT NEW SPRITE FROM WINDOW
        # ===============================
        def import_new_sprite_here():
            self.import_sprite_sheet_window()

            sprite_combo["values"] = list(self.sprites.keys())
            if self.sprites:
                sprite_combo.set(list(self.sprites.keys())[-1])

        tk.Button(win, text="IMPORT SPRITE", command=import_new_sprite_here).pack()

        # ===============================
        # SHEET CONFIG PANEL
        # ===============================
        cfg = tk.Frame(win)
        cfg.pack(fill="x", pady=8)

        tk.Label(cfg, text="Rows").grid(row=0,column=2)
        rows_entry = tk.Entry(cfg, width=5)
        rows_entry.insert(0,"7")
        rows_entry.grid(row=0,column=3)

        tk.Label(cfg, text="Cols").grid(row=0,column=0)
        cols_entry = tk.Entry(cfg, width=5)
        cols_entry.insert(0,"8")
        cols_entry.grid(row=0,column=1)

        tk.Label(cfg, text="Frame W").grid(row=0,column=4)
        fw_entry = tk.Entry(cfg, width=6)
        fw_entry.insert(0,"73")
        fw_entry.grid(row=0,column=5)

        tk.Label(cfg, text="Frame H").grid(row=0,column=6)
        fh_entry = tk.Entry(cfg, width=6)
        fh_entry.insert(0,"65")
        fh_entry.grid(row=0,column=7)

        actor_sheets = []

        if editing_actor:
            name_entry.insert(0, editing_actor.name)
            type_combo.set(editing_actor.kind)
            hp_entry.insert(0, editing_actor.max_hp)
            sp_entry.insert(0, editing_actor.max_sp)
            atk_entry.insert(0, editing_actor.atk)
            mag_entry.insert(0, editing_actor.magic)
            iniciativa.insert(0, editing_actor.initiative)
            def_entry.insert(0, editing_actor.defense)
            res_entry.insert(0, editing_actor.resistance)
            spd_entry.insert(0, editing_actor.speed)
            atk_bonus_entry.insert(0, editing_actor.attack_bonus)
            CA_entry.insert(0, editing_actor.armor_class)
            damage_max_entry.insert(0, editing_actor.damage_max)

            body_type_combo.set(editing_actor.body_type)
            team_combo.set(editing_actor.kind)
            ai_combo.set(editing_actor.ai_mode)
            move_entry.insert(0, editing_actor.move_range)
            range_entry.insert(0, editing_actor.attack_range)

            for item in editing_actor.inventory:
                inventory_list.insert(tk.END, item)

            for special in editing_actor.skills:
                special_list.insert(tk.END, special)
            
            actor_sheets = editing_actor.sprite_sheets.copy()

            for spr in actor_sheets:
                actor_sheet_list.insert("end", spr)

        else:
            hp_entry.insert(0, 10)
            sp_entry.insert(0, 25)
            atk_entry.insert(0, 10)
            mag_entry.insert(0, 5)
            iniciativa.insert(0, 10)
            def_entry.insert(0, 5)
            res_entry.insert(0, 5)
            spd_entry.insert(0, 5)
            atk_bonus_entry.insert(0, 2)
            CA_entry.insert(0, 10)
            damage_max_entry.insert(0, 6)

            move_entry.insert(0, 4)
            range_entry.insert(0, 1)


        def add_sheet_to_actor():
            spr = sprite_combo.get()
            if spr not in self.sprites:
                return

            try:
                self.sprites[spr].sheet_rows = int(rows_entry.get())
                self.sprites[spr].sheet_cols = int(cols_entry.get())
                self.sprites[spr].frame_w = int(fw_entry.get())
                self.sprites[spr].frame_h = int(fh_entry.get())
            except:
                pass

            actor_sheets.append(spr)
            actor_sheet_list.insert("end", spr)

        tk.Button(win, text="ADD SPRITE SHEET TO ACTOR", command=add_sheet_to_actor).pack(pady=5)

        # ===============================
        # SAVE ACTOR
        # ===============================
        def do_create():
                
            actor_name = name_entry.get().strip()

            if not actor_name:
                return

            first_sprite = actor_sheets[0] if actor_sheets else ""

            if editing_actor:
                actor = editing_actor
                old_name = editing_actor.name
                new_name = name_entry.get().strip()

                if old_name != new_name:

                    del self.actors[old_name]

                    actor.name = new_name

                    self.actors[new_name] = actor

            else:
                actor = ActorAsset(actor_name, first_sprite)
            actor.sprite_sheets = actor_sheets.copy()

            actor.kind = type_combo.get()
            #actor.event_file = os.path.join("scenes", event_combo.get()) if event_combo.get() else ""

            if actor.kind == "main" or len(self.actors) == 0:
                actor.is_main = True

            if actor.kind == "enemy":
                actor.interactive = False

            actor.hp = int(hp_entry.get())
            actor.max_hp = actor.hp

            actor.sp = int(sp_entry.get())
            actor.max_sp = actor.sp

            actor.atk = int(atk_entry.get())
            actor.defense = int(def_entry.get())
            actor.magic = int(mag_entry.get())
            actor.resistance = int(res_entry.get())
            actor.speed = int(spd_entry.get())
            actor.initiative = int(iniciativa.get())

            actor.attack_bonus = int(atk_bonus_entry.get())
            actor.armor_class = int(CA_entry.get())
            actor.damage_max = int(damage_max_entry.get())
            actor.body_type = body_type_combo.get()

            actor.team = team_combo.get()
            actor.ai_mode = ai_combo.get()

            actor.move_range = int(move_entry.get())
            actor.attack_range = int(range_entry.get())

            actor.inventory = list(inventory_list.get(0,tk.END))
            actor.skills = list(special_list.get(0,tk.END))

            self.actors[actor_name] = actor
            self.refresh_actor_listbox()

            print("ACTOR CREATED:", actor_name, actor.sprite_sheets)
            win.destroy()

        tk.Button(win, text="SAVE ACTOR", command=do_create).pack(pady=20)
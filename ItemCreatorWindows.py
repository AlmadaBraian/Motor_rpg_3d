import os
import tkinter as tk
from tkinter import ttk, simpledialog, filedialog
from tkinter import messagebox

from ItemAsset import ItemAsset

def open_item_editor(self):

    win = tk.Toplevel()
    win.title("item Database")
    win.geometry("900x700")

    # =====================================
    # LEFT PANEL
    # =====================================

    left = tk.Frame(win)
    left.pack(side="left", fill="y")

    item_listbox = tk.Listbox(left, width=30)
    item_listbox.pack(fill="y", expand=True)

    for item_name in self.items:
        item_listbox.insert(tk.END, item_name)

    # =====================================
    # RIGHT PANEL
    # =====================================

    right = tk.Frame(win)
    right.pack(side="left", fill="both", expand=True)

    tk.Label(right, text="item Name").pack()

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

    consumible_var = tk.BooleanVar(value=True)

    tk.Checkbutton(
        stats,
        text="Consumible",
        variable=consumible_var
    ).grid(row=0, column=0, columnspan=2, sticky="w")


    tk.Label(stats, text="Power").grid(row=0,column=2)

    power_entry = tk.Entry(stats, width=8)
    power_entry.grid(row=0,column=3)

    tk.Label(stats, text="Price").grid(row=1,column=2)

    price_entry = tk.Entry(stats, width=8)
    price_entry.grid(row=1,column=3)

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
        "buff_attack",
        "buff_defense",
        "buff_speed",
        "revive",
        "status",
        "script"
    ]

    effect_combo.set("heal")

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
        "all_allies"
    ]

    target_combo.set("enemy")

    target_combo.grid(row=2,column=1)

    # =====================================
    # SCRIPT
    # =====================================

    tk.Label(right, text="Script").pack()

    script_text = tk.Text(right, height=12)
    script_text.pack(fill="both", expand=True, padx=10)

    current_item = [None]

    def load_item(evt=None):

        sel = item_listbox.curselection()

        if not sel:
            return

        item_name = item_listbox.get(sel[0])

        item = self.items[item_name]

        current_item[0] = item

        name_entry.delete(0, tk.END)
        name_entry.insert(0, item.name)

        desc_text.delete("1.0", tk.END)
        desc_text.insert("1.0", item.description)

        power_entry.delete(0, tk.END)
        power_entry.insert(0, item.power)

        price_entry.delete(0, tk.END)
        price_entry.insert(0, item.price)

        range_entry.delete(0, tk.END)
        range_entry.insert(0, item.range)

        effect_combo.set(item.effect_type)

        target_combo.set(item.target_type)

        consumible_var.set(
            getattr(item, "consumable", True)
        )

        script_text.delete("1.0", tk.END)
        script_text.insert("1.0", item.script)

    item_listbox.bind("<<ListboxSelect>>", load_item)

    def new_item():

        item = ItemAsset()

        self.items[item.name] = item

        item_listbox.insert(tk.END, item.name)

    def save_item():

        if current_item[0]:

            item = current_item[0]

        else:

            item = ItemAsset()

        old_name = item.name

        item.name = name_entry.get()

        item.description = desc_text.get("1.0", tk.END).strip()

        item.power = int(power_entry.get())

        item.price = int(price_entry.get())

        item.consumable = consumible_var.get()

        item.range = int(range_entry.get())

        item.effect_type = effect_combo.get()

        item.target_type = target_combo.get()


        item.script = script_text.get("1.0", tk.END)

        if old_name in self.items:
            del self.items[old_name]

        self.items[item.name] = item

        item_listbox.delete(0, tk.END)

        for s in self.items:
            item_listbox.insert(tk.END, s)

    btns = tk.Frame(left)
    btns.pack(fill="x")

    tk.Button(
        btns,
        text="NEW",
        command=new_item
    ).pack(fill="x")

    tk.Button(
        btns,
        text="SAVE",
        command=save_item
    ).pack(fill="x")
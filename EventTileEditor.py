import os
import tkinter as tk
from tkinter import ttk


class EventTileEditor:

    def __init__(self, toolkit):
        self.toolkit = toolkit

    # =========================================================
    # OPEN
    # =========================================================

    def open(self, gx, gy, tile):

        o = self.toolkit

        win = tk.Toplevel()
        win.title("Event Tile Editor")
        win.geometry("460x700")
        win.resizable(False, False)

        # =====================================================
        # TITLE
        # =====================================================

        tk.Label(
            win,
            text=f"EVENT TILE [{gx},{gy}]",
            font=("Arial", 13, "bold")
        ).pack(pady=10)

        # =====================================================
        # ENABLED
        # =====================================================

        enabled_var = tk.BooleanVar(
            value=tile.event_data.get(
                "enabled",
                True
            )
        )

        tk.Checkbutton(
            win,
            text="Enabled",
            variable=enabled_var
        ).pack(anchor="w", padx=20)

        # =====================================================
        # TRIGGER
        # =====================================================

        tk.Label(
            win,
            text="Trigger Type"
        ).pack(anchor="w", padx=20, pady=(12, 0))

        trigger_combo = ttk.Combobox(
            win,
            state="readonly"
        )

        trigger_combo["values"] = [
            "step",
            "action",
            "autorun",
            "proximity"
        ]

        trigger_combo.set(
            tile.event_data.get(
                "trigger",
                "step"
            )
        )

        trigger_combo.pack(
            fill="x",
            padx=20
        )

        # =====================================================
        # PROXIMITY RADIUS
        # =====================================================

        tk.Label(
            win,
            text="Proximity Radius"
        ).pack(anchor="w", padx=20, pady=(12, 0))

        radius_var = tk.StringVar(
            value=str(
                tile.event_data.get(
                    "radius",
                    3
                )
            )
        )

        radius_entry = tk.Entry(
            win,
            textvariable=radius_var
        )

        radius_entry.pack(
            fill="x",
            padx=20
        )

        # =====================================================
        # SCENE
        # =====================================================

        tk.Label(
            win,
            text="Scene JSON"
        ).pack(anchor="w", padx=20, pady=(12, 0))

        scene_files = []

        if os.path.exists("scenes"):

            scene_files = sorted([
                f for f in os.listdir("scenes")
                if f.endswith(".json")
            ])

        scene_combo = ttk.Combobox(
            win,
            state="readonly"
        )

        scene_combo["values"] = scene_files

        current_scene = os.path.basename(
            tile.event_data.get(
                "scene",
                ""
            )
        )

        if current_scene:
            scene_combo.set(current_scene)

        elif scene_files:
            scene_combo.set(scene_files[0])

        scene_combo.pack(
            fill="x",
            padx=20
        )

        # =====================================================
        # SCENE PREVIEW
        # =====================================================

        preview_var = tk.StringVar(value="")

        preview_label = tk.Label(
            win,
            textvariable=preview_var,
            justify="left",
            anchor="w",
            bg="#202020",
            fg="white",
            relief="sunken",
            padx=8,
            pady=8,
            height=6
        )

        preview_label.pack(
            fill="x",
            padx=20,
            pady=(8, 0)
        )

        def refresh_preview():

            scene_name = scene_combo.get()

            if not scene_name:
                preview_var.set("NO SCENE")
                return

            path = os.path.join(
                "scenes",
                scene_name
            )

            if not os.path.exists(path):
                preview_var.set("SCENE NOT FOUND")
                return

            try:

                import json

                with open(
                    path,
                    "r",
                    encoding="utf-8"
                ) as f:

                    data = json.load(f)

                script = data.get(
                    "script",
                    []
                )

                lines = []

                lines.append(
                    f"Commands: {len(script)}"
                )

                for cmd in script[:4]:

                    action = cmd.get(
                        "action",
                        "?"
                    )

                    lines.append(
                        f"- {action}"
                    )

                preview_var.set(
                    "\n".join(lines)
                )

            except Exception as e:

                preview_var.set(
                    f"ERROR:\n{e}"
                )

        scene_combo.bind(
            "<<ComboboxSelected>>",
            lambda e: refresh_preview()
        )

        refresh_preview()

        # =====================================================
        # ONCE
        # =====================================================

        once_var = tk.BooleanVar(
            value=tile.event_data.get(
                "once",
                False
            )
        )

        tk.Checkbutton(
            win,
            text="Run Once",
            variable=once_var
        ).pack(anchor="w", padx=20, pady=(14, 0))

        # =====================================================
        # REQUIRED SWITCH
        # =====================================================

        tk.Label(
            win,
            text="Required Switch"
        ).pack(anchor="w", padx=20, pady=(12, 0))

        switch_required_entry = tk.Entry(win)

        switch_required_entry.insert(
            0,
            tile.event_data.get(
                "switch_required",
                ""
            )
        )

        switch_required_entry.pack(
            fill="x",
            padx=20
        )

        # =====================================================
        # SET SWITCH
        # =====================================================

        tk.Label(
            win,
            text="Set Switch"
        ).pack(anchor="w", padx=20, pady=(12, 0))

        switch_set_entry = tk.Entry(win)

        switch_set_entry.insert(
            0,
            tile.event_data.get(
                "switch_set",
                ""
            )
        )

        switch_set_entry.pack(
            fill="x",
            padx=20
        )

        # =====================================================
        # SAVE
        # =====================================================

        def save_event():

            evt = scene_combo.get()

            fullpath = ""

            if evt:

                fullpath = os.path.join(
                    "scenes",
                    evt
                )

            try:
                radius = int(
                    radius_var.get()
                )
            except:
                radius = 3

            tile.event_data = {

                "enabled":
                    enabled_var.get(),

                "trigger":
                    trigger_combo.get(),

                "scene":
                    fullpath,

                "once":
                    once_var.get(),

                "done":
                    False,

                "radius":
                    radius,

                "switch_required":
                    switch_required_entry.get(),

                "switch_set":
                    switch_set_entry.get()
            }

            print(
                "EVENT TILE SAVED:",
                gx,
                gy,
                tile.event_data
            )

            o.draw_grid()

            if hasattr(o, "viewport"):
                o.viewport.redraw()

            if hasattr(o, "auto_return_to_select"):
                o.auto_return_to_select()

            win.destroy()

        # =====================================================
        # DELETE
        # =====================================================

        def delete_event():

            tile.event_data = {

                "enabled": False,
                "trigger": "step",
                "scene": "",
                "once": False,
                "done": False,
                "radius": 3,
                "switch_required": "",
                "switch_set": ""
            }

            print(
                "EVENT TILE DELETED:",
                gx,
                gy
            )

            o.draw_grid()

            if hasattr(o, "viewport"):
                o.viewport.redraw()

            win.destroy()

        # =====================================================
        # BUTTONS
        # =====================================================

        btnframe = tk.Frame(win)
        btnframe.pack(
            fill="x",
            pady=18
        )

        tk.Button(
            btnframe,
            text="SAVE EVENT",
            height=2,
            command=save_event
        ).pack(
            side="left",
            expand=True,
            fill="x",
            padx=10
        )

        tk.Button(
            btnframe,
            text="DELETE EVENT",
            height=2,
            command=delete_event
        ).pack(
            side="left",
            expand=True,
            fill="x",
            padx=10
        )
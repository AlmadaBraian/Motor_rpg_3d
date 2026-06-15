import copy
import json
import os
import tkinter as tk

from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import filedialog

from SceneCommands import SCENE_COMMANDS, VN_SPRITE_ANIMATIONS, VN_TEXT_ANIMATIONS
from SceneManager import get_runtime_scene_manager


class SceneCreator(tk.Toplevel):

    def __init__(self, toolkit):

        super().__init__(toolkit.root)

        self.toolkit = toolkit

        self.title("Scene Creator")
        self.geometry("1200x700")

        self.scene_data = {}

        self.vn_sprites = []

        self.vn_texts = []

        self.build_ui()

        self.create_empty_scene()

    def build_ui(self):

        top = tk.Frame(self)
        top.pack(fill="x", padx=5, pady=5)
        

        # ======================
        # NAME
        # ======================

        tk.Label(
            top,
            text="Nombre"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        self.scene_name_var = tk.StringVar()

        tk.Entry(
            top,
            textvariable=self.scene_name_var,
            width=40
        ).grid(
            row=0,
            column=1,
            sticky="ew"
        )

        # ======================
        # TYPE
        # ======================

        tk.Label(
            top,
            text="Tipo"
        ).grid(
            row=1,
            column=0,
            sticky="w"
        )

        self.scene_type_var = tk.StringVar(
            value="world"
        )

        ttk.Combobox(
            top,
            textvariable=self.scene_type_var,
            values=[
                "world",
                "visual_novel"
            ],
            state="readonly"
        ).grid(
            row=1,
            column=1,
            sticky="ew"
        )

        # ======================
        # MAP
        # ======================

        self.map_label = tk.Label(
            top,
            text="Mapa Inicial"
        )
        self.map_label.grid(
            row=2,
            column=0,
            sticky="w"
        )

        self.start_map_var = tk.StringVar()

        self.map_combo = ttk.Combobox(
            top,
            textvariable=self.start_map_var,
            values=self.toolkit.get_map_names(),
            state="readonly"
        )

        self.map_combo.grid(
            row=2,
            column=1,
            sticky="ew"
        )

        top.columnconfigure(
            1,
            weight=1
        )

        # ======================
        # BODY
        # ======================

        body = tk.PanedWindow(
            self,
            orient="horizontal"
        )

        body.pack(
            fill="both",
            expand=True
        )

        center = tk.Frame(body)

        body.add(
            center,
            width=300
        )

        self.property_frame = center

        # ======================
        # COMMANDS
        # ======================

        left = tk.Frame(body)

        body.add(
            left,
            width=350
        )

        self.sprite_list = tk.Listbox(left)

        self.sprite_list.pack(
            fill="both",
            expand=True
        )

        self.sprite_list.bind(
            "<<ListboxSelect>>",
            self.on_vn_sprite_selected
        )

        self.text_list = tk.Listbox(left)

        self.text_list.pack(
            fill="both",
            expand=True
        )

        self.text_list.bind(
            "<<ListboxSelect>>",
            self.on_vn_text_selected
        )

        self.command_list = tk.Listbox(
            left
        )

        self.command_list.pack(
            fill="both",
            expand=True
        )

        self.command_list.bind(
            "<<ListboxSelect>>",
            self.on_command_selected
        )

        self.command_list.bind(
            "<Double-Button-1>",
            self.edit_selected_command
        )

        btns = tk.Frame(left)
        btns.pack(fill="x")

        sprite_buttons = tk.Frame(left)
        sprite_buttons.pack(fill="x")

        tk.Button(
            btns,
            text="Agregar",
            command=self.add_command
        ).pack(side="left")

        tk.Button(
            btns,
            text="Eliminar",
            command=self.delete_command
        ).pack(side="left")

        tk.Button(
            btns,
            text="↑",
            command=self.move_command_up
        ).pack(side="left")

        tk.Button(
            btns,
            text="↑",
            command=self.move_command_down
        ).pack(side="left")

        tk.Button(
            sprite_buttons,
            text="Agregar Sprite",
            command=self.add_vn_sprite
        ).pack(side="left")

        tk.Button(
            sprite_buttons,
            text="Agregar Texto",
            command=self.add_vn_text
        ).pack(side="left")


        tk.Button(
            btns,
            text="Probar",
            command=self.test_scene
        ).pack(side="left")

        # ======================
        # JSON
        # ======================

        right = tk.Frame(body)

        body.add(
            right
        )

        self.json_text = tk.Text(
            right
        )

        self.json_text.pack(
            fill="both",
            expand=True
        )

        self.scene_type_var.trace_add(
            "write",
            lambda *args: self.refresh_json()
        )

        self.scene_name_var.trace_add(
            "write",
            lambda *args: self.refresh_json()
        )

        self.start_map_var.trace_add(
            "write",
            lambda *args: self.refresh_json()
        )

        # ======================
        # BOTTOM
        # ======================

        bottom = tk.Frame(self)
        bottom.pack(fill="x")

        tk.Button(
            bottom,
            text="Abrir",
            command=self.open_scene
        ).pack(side="left")

        tk.Button(
            bottom,
            text="Guardar",
            command=self.save_scene
        ).pack(
            side="right"
        )

    def add_vn_text(self):

        text = {

            "name": "NuevoTexto",

            "text": "Texto",

            "x": 0,
            "y": 0,

            "visible": False,

            "scale": 1,

            "z": 10
        }

        self.vn_texts.append(text)

        self.refresh_vn_text_list()

        self.refresh_json()

    def add_vn_sprite(self):

        sprite = {
            "name": "NuevoSprite",
            "image": "",
            "x": 0,
            "y": 0,
            "w": 270,
            "h": 480,
            "visible": False,
            "z": 10
        }

        self.vn_sprites.append(sprite)

        self.refresh_vn_sprite_list()
        self.refresh_json()

    def delete_vn_sprite(self):

        sel = self.sprite_list.curselection()

        if not sel:
            return

        del self.vn_sprites[sel[0]]

        self.refresh_vn_sprite_list()
        self.refresh_json()

    def on_vn_sprite_selected(self, event=None):

        sel = self.sprite_list.curselection()

        if not sel:
            return

        index = sel[0]

        sprite = self.vn_sprites[index]

        self.clear_property_editor()

        # ==========================
        # NAME
        # ==========================

        tk.Label(
            self.property_frame,
            text="Nombre"
        ).pack(anchor="w")

        name_var = tk.StringVar(
            value=sprite.get("name", "")
        )

        tk.Entry(
            self.property_frame,
            textvariable=name_var
        ).pack(fill="x")

        # ==========================
        # IMAGE
        # ==========================

        tk.Label(
            self.property_frame,
            text="Imagen"
        ).pack(anchor="w")

        image_var = tk.StringVar(
            value=sprite.get("image", "")
        )

        ttk.Combobox(
            self.property_frame,
            textvariable=image_var,
            values=self.get_png_files(),
            state="readonly"
        ).pack(fill="x")

        # ==========================
        # X
        # ==========================

        tk.Label(
            self.property_frame,
            text="X"
        ).pack(anchor="w")

        x_var = tk.IntVar(
            value=sprite.get("x", 0)
        )

        tk.Entry(
            self.property_frame,
            textvariable=x_var
        ).pack(fill="x")

        # ==========================
        # Y
        # ==========================

        tk.Label(
            self.property_frame,
            text="Y"
        ).pack(anchor="w")

        y_var = tk.IntVar(
            value=sprite.get("y", 0)
        )

        tk.Entry(
            self.property_frame,
            textvariable=y_var
        ).pack(fill="x")

        # ==========================
        # WIDTH
        # ==========================

        tk.Label(
            self.property_frame,
            text="Width"
        ).pack(anchor="w")

        w_var = tk.IntVar(
            value=sprite.get("w", 270)
        )

        tk.Entry(
            self.property_frame,
            textvariable=w_var
        ).pack(fill="x")

        # ==========================
        # HEIGHT
        # ==========================

        tk.Label(
            self.property_frame,
            text="Height"
        ).pack(anchor="w")

        h_var = tk.IntVar(
            value=sprite.get("h", 480)
        )

        tk.Entry(
            self.property_frame,
            textvariable=h_var
        ).pack(fill="x")

        # ==========================
        # Z
        # ==========================

        tk.Label(
            self.property_frame,
            text="Z"
        ).pack(anchor="w")

        z_var = tk.IntVar(
            value=sprite.get("z", 10)
        )

        tk.Entry(
            self.property_frame,
            textvariable=z_var
        ).pack(fill="x")

        # ==========================
        # VISIBLE
        # ==========================

        visible_var = tk.BooleanVar(
            value=sprite.get("visible", False)
        )

        tk.Checkbutton(
            self.property_frame,
            text="Visible",
            variable=visible_var
        ).pack(anchor="w")

        # ==========================
        # UPDATE
        # ==========================

        def update(*args):

            sprite["name"] = name_var.get()
            sprite["image"] = image_var.get()

            sprite["x"] = x_var.get()
            sprite["y"] = y_var.get()

            sprite["w"] = w_var.get()
            sprite["h"] = h_var.get()

            sprite["z"] = z_var.get()

            sprite["visible"] = visible_var.get()

            self.refresh_vn_sprite_list()
            self.refresh_json()

        name_var.trace_add(
            "write",
            update
        )

        image_var.trace_add(
            "write",
            update
        )

        x_var.trace_add(
            "write",
            update
        )

        y_var.trace_add(
            "write",
            update
        )

        w_var.trace_add(
            "write",
            update
        )

        h_var.trace_add(
            "write",
            update
        )

        z_var.trace_add(
            "write",
            update
        )

        visible_var.trace_add(
            "write",
            update
        )

    def on_vn_text_selected(self, event=None):

            sel = self.text_list.curselection()

            if not sel:
                return

            index = sel[0]

            text = self.vn_texts[index]

            self.clear_property_editor()

            # ==========================
            # NAME
            # ==========================

            tk.Label(
                self.property_frame,
                text="Nombre"
            ).pack(anchor="w")

            name_var = tk.StringVar(
                value=text.get("name", "")
            )

            tk.Entry(
                self.property_frame,
                textvariable=name_var
            ).pack(fill="x")

            # ==========================
            # X
            # ==========================

            tk.Label(
                self.property_frame,
                text="X"
            ).pack(anchor="w")

            x_var = tk.IntVar(
                value=text.get("x", 0)
            )

            tk.Entry(
                self.property_frame,
                textvariable=x_var
            ).pack(fill="x")

            # ==========================
            # Y
            # ==========================

            tk.Label(
                self.property_frame,
                text="Y"
            ).pack(anchor="w")

            y_var = tk.IntVar(
                value=text.get("y", 0)
            )

            tk.Entry(
                self.property_frame,
                textvariable=y_var
            ).pack(fill="x")

            # ==========================
            # WIDTH
            # ==========================

            tk.Label(
                self.property_frame,
                text="scale"
            ).pack(anchor="w")

            scale_var = tk.IntVar(
                value=text.get("scale", 2)
            )

            tk.Entry(
                self.property_frame,
                textvariable=scale_var
            ).pack(fill="x")

            # ==========================
            # Z
            # ==========================

            tk.Label(
                self.property_frame,
                text="Z"
            ).pack(anchor="w")

            z_var = tk.IntVar(
                value=text.get("z", 10)
            )

            tk.Entry(
                self.property_frame,
                textvariable=z_var
            ).pack(fill="x")

            # ==========================
            # TEXTO
            # ==========================

            tk.Label(
                self.property_frame,
                text="Texto"
            ).pack(anchor="w")

            text_var = tk.StringVar(
                value=text.get("text", "")
            )

            tk.Entry(
                self.property_frame,
                textvariable=text_var
            ).pack(fill="x")

            # ==========================
            # VISIBLE
            # ==========================

            visible_var = tk.BooleanVar(
                value=text.get("visible", False)
            )

            tk.Checkbutton(
                self.property_frame,
                text="Visible",
                variable=visible_var
            ).pack(anchor="w")

            # ==========================
            # UPDATE
            # ==========================

            def update(*args):

                text["name"] = name_var.get()

                text["x"] = x_var.get()
                text["y"] = y_var.get()

                text["scale"] = scale_var.get()

                text["z"] = z_var.get()

                text["text"] = text_var.get()

                text["visible"] = visible_var.get()

                self.refresh_vn_text_list()
                self.refresh_json()

            name_var.trace_add(
                "write",
                update
            )

            x_var.trace_add(
                "write",
                update
            )

            y_var.trace_add(
                "write",
                update
            )

            scale_var.trace_add(
                "write",
                update
            )

            z_var.trace_add(
                "write",
                update
            )

            text_var.trace_add(
                "write",
                update
            )

            visible_var.trace_add(
                "write",
                update
            )
        
    
    def refresh_vn_sprite_list(self):

        self.sprite_list.delete(
            0,
            "end"
        )

        for spr in self.vn_sprites:

            self.sprite_list.insert(
                "end",
                spr.get("name", "")
            )

    def refresh_vn_text_list(self):

            self.text_list.delete(
                0,
                "end"
            )

            for txt in self.vn_texts:

                self.text_list.insert(
                    "end",
                    txt.get("name", "")
                )
    
    
    def get_png_files(self):

        result = []

        if os.path.isdir("png"):

            for f in os.listdir("png"):

                if f.lower().endswith(".png"):

                    result.append(
                        os.path.join("png", f)
                    )

        return sorted(result)

    def test_scene(self):

        self.refresh_json()

        temp_path = os.path.join(
            "scenes",
            "__scene_test__.json"
        )

        with open(
        temp_path,
        "w",
        encoding="utf-8"
            ) as f:

                json.dump(
                    self.scene_data,
                    f,
                    indent=4,
                    ensure_ascii=False
                )

        self.toolkit.initial_scene_file = temp_path

        self.toolkit.runtime.open_game_runtime()

    def open_scene(self):

        path = filedialog.askopenfilename(
            title="Abrir escena",
            filetypes=[
                ("Escenas JSON", "*.json")
            ],
            initialdir="scenes"
        )

        if not path:
            return

        self.load_scene(path)

    def edit_selected_command(self, event=None):
        pass


    def create_empty_scene(self):

        self.scene_data = {

            "scene": "",

            "start_map": "Map001",

            "script": []
        }

        self.refresh_command_list()
        self.refresh_json()

    def on_command_selected(self, event=None):

        sel = self.command_list.curselection()

        if not sel:
            return

        index = sel[0]

        cmd = self.scene_data["script"][index]

        if cmd["action"] == "show_dialog":

            self.show_dialog_editor(
                cmd
            )

            return
        
        if cmd["action"] == "audio_play":

            self.show_audio_editor(
                cmd
            )
            return
        
        if cmd["action"] == "change_scene":

            self.show_change_scene_editor(
                cmd
            )

            return
        
        if cmd["action"] in (
        "vn_start_animation",
        "vn_animation",
        "start_animation"
        ):
            self.show_vn_animation_editor(cmd)
            return

        self.show_command_editor(
            cmd
        )

    def move_command_down(self):

        sel = self.command_list.curselection()

        if not sel:
            return

        index = sel[0]

        script = self.scene_data["script"]

        if index >= len(script) - 1:
            return

        script[index], script[index + 1] = (
            script[index + 1],
            script[index]
        )

        self.refresh_command_list()

        self.command_list.selection_set(
            index + 1
        )

        self.refresh_json()
    
    def move_command_up(self):

        sel = self.command_list.curselection()

        if not sel:
            return

        index = sel[0]

        if index <= 0:
            return

        script = self.scene_data["script"]

        script[index], script[index - 1] = (
            script[index - 1],
            script[index]
        )

        self.refresh_command_list()

        self.command_list.selection_set(
            index - 1
        )

        self.refresh_json()

    def show_vn_animation_editor(self, cmd):

        self.clear_property_editor()

        tk.Label(
            self.property_frame,
            text="Animar"
        ).pack(anchor="w")

        anim_type_var = tk.StringVar()

        if cmd.get("text"):

            anim_type_var.set("text")

        else:

            anim_type_var.set("sprite")

        values = ["sprite", "text"]

        anim_type_combo = ttk.Combobox(
            self.property_frame,
            textvariable=anim_type_var,
            values=values,
            state="readonly"
        )

        anim_type_combo.pack(fill="x")

        target_label = tk.Label(
            self.property_frame,
            text="Sprite"
        )

        target_label.pack(anchor="w")

        sprite_names = []

        text_names = []

        for spr in self.vn_sprites:
            sprite_names.append(
                spr.get("name", "")
            )

        for txt in self.vn_texts:
            text_names.append(
                txt.get("name", "")
            )

        target_var = tk.StringVar()

        target_combo = ttk.Combobox(
            self.property_frame,
            textvariable=target_var,
            state="readonly"
        )

        target_combo.pack(fill="x")


        tk.Label(
            self.property_frame,
            text="Animation"
        ).pack(anchor="w")

        animation_var = tk.StringVar(
            value=cmd.get(
                "animation",
                ""
            )
        )

        if anim_type_var.get() == "sprite":

            animation_names = list(
                VN_SPRITE_ANIMATIONS.keys()
            )

        else:

            animation_names = list(
                VN_TEXT_ANIMATIONS.keys()
            )

        animation_combo = ttk.Combobox(
            self.property_frame,
            textvariable=animation_var,
            values=animation_names,
            state="readonly"
        )

        animation_combo.pack(fill="x")

        X_label = tk.Label(
            self.property_frame,
            text="Pos X Final"
        )
        X_label.pack()

        X_var = tk.StringVar(
            value=
                cmd.get(
                    "x"
                )
        )

        X_entry = tk.Entry(
            self.property_frame,
            textvariable=X_var
        )

        X_entry.pack(fill="x")

        Y_label = tk.Label(
            self.property_frame,
            text="Pos Y Final"
        )
        Y_label.pack()

        Y_var = tk.StringVar(
            value=
                cmd.get(
                    "y"
                )
        )

        Y_entry = tk.Entry(
            self.property_frame,
            textvariable=Y_var
        )

        Y_entry.pack(fill="x")

        speed_label = tk.Label(
            self.property_frame,
            text="speed"
        )
        speed_label.pack()

        speed_var = tk.StringVar(
            value=
                cmd.get(
                    "speed"
                )
        )

        speed_entry = tk.Entry(
            self.property_frame,
            textvariable=speed_var
        )

        speed_entry.pack(fill="x")

            
        duration_label = tk.Label(
            self.property_frame,
            text="duration"
        )
        duration_label.pack()

        duration_var = tk.StringVar(
            value=
                cmd.get(
                    "duration"
                )
        )

        duration_entry = tk.Entry(
            self.property_frame,
            textvariable=duration_var
        )

        duration_entry.pack(fill="x")

        #values=self.toolkit.get_vn_animation_names()

        wait_var = tk.BooleanVar(
            value=cmd.get("wait", False)
        )

        tk.Checkbutton(
            self.property_frame,
            text="Esperar fin de animación",
            variable=wait_var
        ).pack(anchor="w")

        def refresh_target_combo(*args):

            anim_type = anim_type_var.get()

            if anim_type == "sprite":

                target_label.config(
                    text="Sprite"
                )

                values = [
                    s.get("name", "")
                    for s in self.vn_sprites
                ]

                target_combo.configure(
                    values=values
                )

                cmd.pop(
                    "text",
                    None
                )

                target_var.set(
                    cmd.get(
                        "sprite",
                        ""
                    )
                )

            else:

                target_label.config(
                    text="Texto"
                )

                values = [
                    t.get("name", "")
                    for t in self.vn_texts
                ]

                target_combo.configure(
                    values=values
                )

                cmd.pop(
                    "sprite",
                    None
                )

                target_var.set(
                    cmd.get(
                        "text",
                        ""
                    )
                )

            refresh_animation_combo()

        def refresh_animation_combo(*args):

            if anim_type_var.get() == "sprite":

                animation_combo.configure(
                    values=list(
                        VN_SPRITE_ANIMATIONS.keys()
                    )
                )

            else:

                animation_combo.configure(
                    values=list(
                        VN_TEXT_ANIMATIONS.keys()
                    )
                )

        refresh_target_combo()

        def update(*args):

            if anim_type_var.get() == "sprite":

                cmd["sprite"] = target_var.get()

                cmd.pop(
                    "text",
                    None
                )

            else:

                cmd["text"] = target_var.get()

                cmd.pop(
                    "sprite",
                    None
                )

            cmd["animation"] = animation_var.get()

            cmd["wait"] = wait_var.get()

            cmd["x"] = X_var.get()

            cmd["y"] = Y_var.get()

            cmd["speed"] = speed_var.get()

            cmd["duration"] = duration_var.get()

            self.refresh_json()

        target_var.trace_add(
            "write",
            update
        )

        animation_var.trace_add(
            "write",
            update
        )

        wait_var.trace_add(
            "write",
            update
        )

        X_var.trace_add(
            "write",
            update
        )

        Y_var.trace_add(
            "write",
            update
        )

        speed_var.trace_add(
            "write",
            update
        )

        duration_var.trace_add(
            "write",
            update
        )

        anim_type_var.trace_add(
            "write",
            refresh_target_combo
        )

       

    def show_change_scene_editor(
        self,
        cmd
    ):
        self.clear_property_editor()

        manager = get_runtime_scene_manager(self)

        label = tk.Label(
            self.property_frame,
            text="Cambiar a escena:"
        )
        label.pack()

        scene_files  = manager.get_scene_names()
        var = tk.StringVar(
            value=
                cmd.get(
                    "scene_new",
                    cmd.get(
                        "scene",
                        cmd.get(
                            "file",
                            ""
                        )
                    )
                )
        )

        scene_files_combo = ttk.Combobox(
            self.property_frame,
            textvariable=var,
            values=scene_files,
            state="readonly"
        )

        scene_files_combo.pack(fill="x")

        def update(*args):

            cmd.pop("scene_new", None)
            cmd.pop("file", None)

            cmd["scene"] = var.get()

            self.refresh_json()

        var.trace_add(
            "write",
            update
        )

    def show_camera_move_editor(
        self,
        cmd
    ):
        return

    def show_audio_editor(
    self,
    cmd
    ):

        self.clear_property_editor()

        tracks = [
            "bgm",
            "sfx",
            "voice",
            "music",
            "sound"
        ]

        track_var = tk.StringVar(
            value=cmd.get(
                "track",
                "bgm"
            )
        )

        combo = ttk.Combobox(
            self.property_frame,
            textvariable=track_var,
            values=tracks,
            state="readonly"
        )

        combo.pack(fill="x")

        file_label = tk.Label(
            self.property_frame,
            text="Archivo"
        )
        file_label.pack()

        file_var = tk.StringVar(
            value=
                cmd.get(
                    "music",
                    cmd.get(
                        "sound",
                        ""
                    )
                )
        )

        entry = tk.Entry(
            self.property_frame,
            textvariable=file_var
        )

        entry.pack(fill="x")

        

        volume_var = tk.DoubleVar(
            value=cmd.get(
                "volume",
                1.0
            )
        )

        scale = tk.Scale(
            self.property_frame,
            variable=volume_var,
            from_=0,
            to=1,
            resolution=0.05,
            orient="horizontal"
        )

        scale.pack(fill="x")

        def update(*args):

            track = track_var.get()

            cmd["track"] = track
            cmd["volume"] = volume_var.get()

            cmd.pop("music", None)
            cmd.pop("sound", None)

            if track == "sfx":

                cmd["sound"] = file_var.get()

            else:

                cmd["music"] = file_var.get()

            self.refresh_json()

        track_var.trace_add(
            "write",
            update
        )

        file_var.trace_add(
            "write",
            update
        )

        volume_var.trace_add(
            "write",
            update
        )

        update()

    def show_dialog_editor(
    self,
    cmd
    ):

        self.clear_property_editor()

        tk.Label(
            self.property_frame,
            text="Speaker"
        ).pack(anchor="w")

        speaker_var = tk.StringVar(
            value=cmd.get(
                "speaker",
                ""
            )
        )

        speaker_entry = tk.Entry(
            self.property_frame,
            textvariable=speaker_var
        )

        speaker_entry.pack(fill="x")

        tk.Label(
            self.property_frame,
            text="Una línea vacía separa páginas del diálogo"
        ).pack(anchor="w")

        tk.Label(
            self.property_frame,
            text="Dialogo"
        ).pack(anchor="w")

        text_box = tk.Text(
            self.property_frame,
            height=12
        )

        text_box.pack(
            fill="both",
            expand=True
        )

        text_box.insert(
            "1.0",
            "\n\n".join(
                cmd.get("text", [])
            )
        )

        def save_dialog(event=None):

            cmd["speaker"] = (
                speaker_var.get()
            )

            raw_text = text_box.get(
                "1.0",
                "end-1c"
            )

            pages = []

            for page in raw_text.split("\n\n"):

                page = page.strip()

                if page:

                    pages.append(page)

            cmd["text"] = pages

            self.refresh_json()

        speaker_entry.bind(
            "<KeyRelease>",
            save_dialog
        )

        text_box.bind(
            "<KeyRelease>",
            save_dialog
        )

    def clear_property_editor(self):

        for w in self.property_frame.winfo_children():
            w.destroy()

    def update_property(
        self,
        cmd,
        key,
        value
    ):

        try:

            if value.isdigit():
                value = int(value)

            else:

                value = float(value)

        except:

            pass

        cmd[key] = value

        self.refresh_json()

    def show_command_editor(self, cmd):

        self.clear_property_editor()

        row = 0

        tk.Label(
            self.property_frame,
            text=f"Action: {cmd['action']}"
        ).grid(
            row=row,
            column=0,
            sticky="w"
        )

        row += 1

        for key, value in cmd.items():

            if key == "action":
                continue
            if isinstance(value, (list, dict)):
                continue

            tk.Label(
                self.property_frame,
                text=key
            ).grid(
                row=row,
                column=0,
                sticky="w"
            )

            var = tk.StringVar(
                value=str(value)
            )

            ent = tk.Entry(
                self.property_frame,
                textvariable=var
            )

            ent.grid(
                row=row,
                column=1,
                sticky="ew"
            )

            ent.bind(
                "<KeyRelease>",
                lambda e,
                c=cmd,
                k=key,
                v=var:
                self.update_property(
                    c,
                    k,
                    v.get()
                )
            )

            row += 1

    def add_command(self):

        names = list(
            SCENE_COMMANDS.keys()
        )

        win = tk.Toplevel(self)

        win.title(
            "Agregar Acción"
        )

        lb = tk.Listbox(win)

        lb.pack(
            fill="both",
            expand=True
        )

        for n in names:
            lb.insert("end", n)

        def ok():

            sel = lb.curselection()

            if not sel:
                return

            action = names[
                sel[0]
            ]

            cmd = {
                "action": action
            }

            cmd.update(
                copy.deepcopy(
                    SCENE_COMMANDS[action]
                )
            )

            self.scene_data[
                "script"
            ].append(cmd)

            self.refresh_command_list()
            self.refresh_json()

            win.destroy()

        tk.Button(
            win,
            text="Aceptar",
            command=ok
        ).pack()

    def delete_command(self):

        sel = self.command_list.curselection()

        if not sel:
            return

        index = sel[0]

        del self.scene_data[
            "script"
        ][index]

        self.refresh_command_list()
        self.refresh_json()

    def refresh_command_list(self):

        self.command_list.delete(
            0,
            "end"
        )

        for cmd in self.scene_data[
            "script"
        ]:

            self.command_list.insert(
                "end",
                cmd.get(
                    "action",
                    ""
                )
            )


    def sync_vn_sprites_texts(self):

            if "visual_novel" not in self.scene_data:

                self.scene_data["visual_novel"] = {
                    "enabled": True,
                    "sprites": [],
                    "texts":[]
                }

            self.scene_data["visual_novel"]["sprites"] = (
                copy.deepcopy(
                    self.vn_sprites
                )
            )

            self.scene_data["visual_novel"]["texts"] = (
                copy.deepcopy(
                    self.vn_texts
                )
            )

    def refresh_json(self):

        if getattr(
            self,
            "loading_scene",
            False
        ):
            return

        self.scene_data[
            "scene"
        ] = self.scene_name_var.get()


        if (
            self.scene_type_var.get()
            == "visual_novel"
        ):
            
            self.map_label.grid_remove()
            self.map_combo.grid_remove()

            self.scene_data["type"] = "visual_novel"

            self.sync_vn_sprites_texts()

            self.scene_data.pop(
                "start_map",
                None
            )

        else:

            self.map_label.grid()
            self.map_combo.grid()

            self.scene_data.pop(
                "type",
                None
            )

            self.scene_data.pop(
                "visual_novel",
                None
            )

            self.scene_data[
                "start_map"
            ] = self.start_map_var.get()

        self.json_text.delete(
            "1.0",
            "end"
        )

        self.json_text.insert(
            "1.0",
            json.dumps(
                self.scene_data,
                indent=4,
                ensure_ascii=False
            )
        )

    def save_scene(self):

        self.refresh_json()

        scene_name = self.scene_name_var.get()

        if not scene_name:

            messagebox.showerror(
                "Error",
                "Ingrese un nombre."
            )

            return

        file_name = (
            scene_name +
            ".json"
        )

        path = os.path.join(
            "scenes",
            file_name
        )

        os.makedirs(
            "scenes",
            exist_ok=True
        )

        self.sync_vn_sprites_texts()

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.scene_data,
                f,
                indent=4,
                ensure_ascii=False
            )

        self.toolkit.initial_scene_file = path

        if hasattr(
            self.toolkit,
            "refresh_project_selector"
        ):
            self.toolkit.refresh_project_selector()

        messagebox.showinfo(
            "OK",
            "Escena guardada."
        )

        self.destroy()

    def load_scene(self, path):

        self.loading_scene = True

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            self.scene_data = json.load(f)

        self.scene_name_var.set(
            self.scene_data.get(
                "scene",
                ""
            )
        )

        if self.scene_data.get("type") == "visual_novel":

            self.scene_type_var.set(
                "visual_novel"
            )

            vn = self.scene_data.get(
                "visual_novel",
                {}
            )

            self.sync_vn_sprites_texts()

        else:

            self.scene_type_var.set(
                "world"
            )

        self.start_map_var.set(
            self.scene_data.get(
                "start_map",
                "Map001"
            )
        )

        self.loading_scene = False
        self.refresh_command_list()
        self.refresh_json()
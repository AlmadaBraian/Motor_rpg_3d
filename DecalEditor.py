import os
import tkinter as tk

from PIL import Image, ImageTk

import config

from OpglManager import TextureManager

GRID_W = config.GRID_W
GRID_H = config.GRID_H
CELL_PIXELS = config.CELL_PIXELS
ASSET_GRID = config.ASSET_GRID
ASSET_CELL = config.ASSET_CELL

base_path = config.base_path
decal_tex_path = os.path.join(base_path, "decals")
DECAL_TEXTURE_FOLDER = decal_tex_path
EXPORT_FOLDER = base_path + "/export_dc"

from Decal import Decal

class DecalEditor(tk.Toplevel):

    def __init__(self, master, tile, toolkit):

        super().__init__(master)

        self.tile = tile
        self.toolkit = toolkit

        self.selected_texture = None

        self.current_index = None

        main = tk.Frame(self)
        main.pack(fill="both", expand=True)

        left = tk.Frame(main)
        left.pack(side="left", fill="both", expand=True)

        right = tk.Frame(main)
        right.pack(side="right", fill="y")

        self.geometry("400x600")

        self.texture_manager=TextureManager(folder = "decals")

        self.listbox = tk.Listbox(left)
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", lambda e: self.update_preview())

        self.listbox.bind(
            "<<ListboxSelect>>",
            self.on_list_select
        )


        btn_frame = tk.Frame(left)
        btn_frame.pack(fill="x")

        tk.Button(btn_frame, text="Agregar decall", command=self.add_decal).pack(side="left")
        tk.Button(btn_frame, text="Eliminar", command=self.remove_segment).pack(side="left")
        

        tk.Label(right, text="Textura seleccionada").pack(pady=4)

        self.preview = tk.Canvas(right, width=128, height=128, bg="black")
        self.preview.pack()

        self.texture_name = tk.Label(right, text="(sin textura)", wraplength=120)
        self.texture_name.pack()

        tk.Label(
            right,
            text="Width"
        ).pack()

        self.width_var = tk.DoubleVar(
            value=1.0
        )

        self.widht_slider = tk.Scale(
            right,
            from_=1,
            to=20,
            orient='horizontal',
            variable=self.width_var,
            length=100
        )
        self.widht_slider.pack(fill="x", padx=5)


        tk.Label(
            right,
            text="Height"
        ).pack()

        self.height_var = tk.DoubleVar(
            value=1.0
        )

        self.height_slider = tk.Scale(
            right,
            from_=1,
            to=20,
            orient='horizontal',
            variable=self.height_var,
            length=100
        )
        self.height_slider.pack(fill="x", padx=5)


        tk.Label(
            right,
            text="Rotation"
        ).pack()

        self.rotation_var = tk.DoubleVar(
            value=1.0
        )

        self.rot_slider = tk.Scale(
            right,
            from_=-360,
            to=360,
            orient='horizontal',
            variable=self.rotation_var,
            length=100
        )
        self.rot_slider.pack(fill="x", padx=5)

        self.texture_browser_wrap=tk.Frame(right)
        self.texture_browser_wrap.pack(pady=5)

        self.texture_scroll_canvas=tk.Canvas(
            self.texture_browser_wrap,
            width=145,
            height=220,
            bg='black',
            highlightthickness=0
        )
        self.texture_scroll_canvas.pack(side='left')

        self.texture_scrollbar=tk.Scrollbar(
            self.texture_browser_wrap,
            orient='vertical',
            command=self.texture_scroll_canvas.yview
        )
        self.texture_scrollbar.pack(side='left', fill='y')

        self.texture_scroll_canvas.configure(yscrollcommand=self.texture_scrollbar.set)

        self.texture_frame=tk.Frame(self.texture_scroll_canvas,bg='black')
        self.texture_scroll_canvas.create_window((0,0),window=self.texture_frame,anchor='nw')

        self.width_var.trace_add(
            "write",
            lambda *args: self.update_decal_values()
        )

        self.height_var.trace_add(
            "write",
            lambda *args: self.update_decal_values()
        )

        self.rotation_var.trace_add(
            "write",
            lambda *args: self.update_decal_values()
        )

        self.texture_frame.bind(
            '<Configure>',
            lambda e:self.texture_scroll_canvas.configure(
                scrollregion=self.texture_scroll_canvas.bbox('all')
            )
        )

        self.refresh()
        self.build_texture_browser()

    def on_list_select(self, e):

        sel = self.listbox.curselection()

        if sel:
            self.current_index = sel[0]

        self.update_preview()

    def update_decal_values(self):

        
        decal = self.get_segments()[self.current_index]

        try:
            decal.width = self.width_var.get()
            decal.height = self.height_var.get()
            decal.rotation = self.rotation_var.get()

            self.toolkit.redraw()

        except:
            pass
        

    def draw_texture_preview(self, texture_name):
        path = os.path.join(DECAL_TEXTURE_FOLDER, texture_name)
        if not os.path.exists(path):
            return

        img = Image.open(path).convert("RGBA")
        img = img.resize((128, 128), Image.NEAREST)

        tk_img = ImageTk.PhotoImage(img)
        self.texture_preview_ref = tk_img  # 🔥 evitar GC

        self.preview.delete("all")
        self.preview.create_image(64, 64, image=tk_img)

        self.texture_name.config(text=texture_name)

    def update_texture_selection(self):
        texture_names = self.texture_manager.decals

        for i,widget in enumerate(self.texture_frame.winfo_children()):
            tex_name=texture_names[i]

            if tex_name==self.selected_texture:
                widget.config(relief="solid",bd=3,bg="yellow")
            else:
                widget.config(relief="flat",bd=2,bg="black")

    def build_texture_browser(self):
        for widget in self.texture_frame.winfo_children():
            widget.destroy()

        self.texture_thumb_refs=[]

        cols=2
        size=64

        texture_names = self.texture_manager.decals

        
        print("DECAL PREVIEWS:", len(self.texture_manager.decal_previews))
        print(self.texture_manager.decal_previews.keys())
        

        for i, tex_name in enumerate(texture_names):
            path = os.path.join(DECAL_TEXTURE_FOLDER, tex_name)

            print("PATH:", path)
            print("EXISTS:", os.path.exists(path))

            if not os.path.exists(path):
                print("CHECK:", path, os.path.exists(path))
                continue

            img=Image.open(path).convert("RGBA")
            img=img.resize((size,size), Image.NEAREST)

            tk_img=ImageTk.PhotoImage(img)
            self.texture_thumb_refs.append(tk_img)

            btn=tk.Label(self.texture_frame,image=tk_img,bd=2,relief="flat",bg="black")
            btn.grid(row=i//cols,column=i%cols,padx=2,pady=2)

            def on_click(e,tex_name=tex_name):
                self.selected_texture = tex_name
                self.update_texture_selection()
                self.draw_texture_preview(tex_name)

                sel = self.listbox.curselection()
                if sel:
                    self.get_segments()[sel[0]].texture = tex_name
                    self.refresh()

            btn.bind("<Button-1>", on_click)

        if texture_names and not self.selected_texture:
            self.selected_texture=texture_names[0]
            self.draw_texture_preview(texture_names[0])

        self.update_texture_selection()
        print("children:", self.texture_frame.winfo_children())
        print("thumb refs:", len(self.texture_thumb_refs))

    def update_preview(self):
        sel = self.listbox.curselection()
        if not sel:
            return

        decal = self.get_segments()[sel[0]]
        tex = decal.texture

        self.texture_name.config(text=tex if tex else "(sin textura)")

        if not tex:
            self.preview.delete("all")
            return
        
        self.width_var.set(
            decal.width
        )

        self.height_var.set(
            decal.height
        )

        self.rotation_var.set(
            decal.rotation
        )
        
        self.selected_texture = tex
        self.update_texture_selection()
        self.draw_texture_preview(tex)

        sel = self.listbox.curselection()
        if sel:
            self.get_segments()[sel[0]].texture = tex
            self.refresh()

        #self.draw_texture_preview(tex)

    def assign_texture(self):
        sel = self.listbox.curselection()
        if not sel:
            return

        seg = self.get_segments()[sel[0]]

        tex = self.toolkit.selected_texture

        seg["tex"] = tex

        self.refresh()

    def on_texture_select(self, e):
        sel = self.tex_listbox.curselection()
        if not sel:
            return

        self.toolkit.selected_texture = self.tex_listbox.get(sel[0])

    def get_segments(self):
        return self.tile.decals

    def refresh(self):

        self.listbox.delete(
            0,
            tk.END
        )

        for i,d in enumerate(
            self.tile.decals
        ):

            self.listbox.insert(
                tk.END,
                f"{i}: {os.path.basename(d.texture)}"
            )

    def add_decal(self):

        d = Decal()

        d.texture = self.selected_texture

        d.width = self.width_var.get()

        d.height = self.height_var.get()

        d.rotation = self.rotation_var.get()

        d.x = 0.5
        d.y = 0.5

        self.tile.decals.append(d)

        self.refresh()

    def get_selected_decal(self):

        if self.current_index is None:
            return None

        if self.current_index >= len(self.tile.decals):
            return None

        return self.tile.decals[self.current_index]

    def remove_segment(self):

        print("CURRENT:", self.current_index)

        if self.current_index is None:
            return

        del self.tile.decals[self.current_index]

        self.current_index = None

        self.refresh()
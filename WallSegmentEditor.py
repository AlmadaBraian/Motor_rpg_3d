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
tex_path = config.tex_path
TEXTURE_FOLDER = tex_path
EXPORT_FOLDER = base_path + "/export_dc"

class WallSegmentEditor(tk.Toplevel):
    def __init__(self, master, tile, direction, toolkit):
        super().__init__(master)
        self.title(f"Editor de segmentos - {direction}")
        self.tile = tile
        self.direction = direction
        self.toolkit = toolkit
        self.selected_texture = None

        print("EDITOR DIR:", direction)

        main = tk.Frame(self)
        main.pack(fill="both", expand=True)

        left = tk.Frame(main)
        left.pack(side="left", fill="both", expand=True)

        right = tk.Frame(main)
        right.pack(side="right", fill="y")

        self.geometry("400x400")

        self.texture_manager=TextureManager()

        self.listbox = tk.Listbox(left)
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", lambda e: self.update_preview())

        btn_frame = tk.Frame(left)
        btn_frame.pack(fill="x")

        tk.Button(btn_frame, text="Agregar segmento", command=self.add_segment).pack(side="left")
        tk.Button(btn_frame, text="Eliminar", command=self.remove_segment).pack(side="left")
        

        tk.Label(right, text="Textura seleccionada").pack(pady=4)

        self.preview = tk.Canvas(right, width=128, height=128, bg="black")
        self.preview.pack()

        self.texture_name = tk.Label(right, text="(sin textura)", wraplength=120)
        self.texture_name.pack()

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

        self.texture_frame.bind(
            '<Configure>',
            lambda e:self.texture_scroll_canvas.configure(
                scrollregion=self.texture_scroll_canvas.bbox('all')
            )
        )

        self.refresh()
        self.build_texture_browser()

    def draw_texture_preview(self, texture_name):
        path = os.path.join(TEXTURE_FOLDER, texture_name)
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
        texture_names=list(self.texture_manager.previews.keys())

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

        texture_names=list(self.texture_manager.previews.keys())

        for i,tex_name in enumerate(texture_names):
            path=os.path.join(TEXTURE_FOLDER, tex_name)
            if not os.path.exists(path):
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
                    self.get_segments()[sel[0]]["tex"] = tex_name
                    self.refresh()

            btn.bind("<Button-1>", on_click)

        if texture_names and not self.selected_texture:
            self.selected_texture=texture_names[0]
            self.draw_texture_preview(texture_names[0])

        self.update_texture_selection()

    def update_preview(self):
        sel = self.listbox.curselection()
        if not sel:
            return

        seg = self.get_segments()[sel[0]]
        tex = seg.get("tex")

        self.texture_name.config(text=tex if tex else "(sin textura)")

        if not tex:
            self.preview.delete("all")
            return
        
        self.selected_texture = tex
        self.update_texture_selection()
        self.draw_texture_preview(tex)

        sel = self.listbox.curselection()
        if sel:
            self.get_segments()[sel[0]]["tex"] = tex
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
        return self.tile.wall_segments[self.direction]

    def refresh(self):
        self.listbox.delete(0, tk.END)
        for i, seg in enumerate(self.get_segments()):
            self.listbox.insert(tk.END, f"{i}: h={seg.get('h',1.0)}")

    def add_segment(self):
        seg = {
            "h": 1.0,
            "tex": self.selected_texture,
            "uv": "tile"
        }

        self.get_segments().append(seg)
        self.refresh()

    def remove_segment(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        del self.get_segments()[sel[0]]
        self.refresh()
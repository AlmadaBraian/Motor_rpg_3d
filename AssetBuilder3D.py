import tkinter as tk
from tkinter import ttk, simpledialog, filedialog
from tkinter import messagebox
from pyopengltk import OpenGLFrame
from OpenGL.GL import *
from OpenGL.GLU import *
ASSET_GRID = 16
ASSET_CELL = 20

class AssetBuilder3D:
    def __init__(self, parent_toolkit):
        self.parent_toolkit = parent_toolkit
        self.layer = 0
        self.mode = "add"
        self.voxels = []

        self.win = tk.Toplevel()
        self.win.title("Asset Builder 3D")
        self.selected_asset_name = None
        self.loaded_asset = None

        left = tk.Frame(self.win)
        left.pack(side="left", fill="y")

        ttk.Button(left, text="Layer +", command=self.layer_up).pack(fill="x")
        ttk.Button(left, text="Layer -", command=self.layer_down).pack(fill="x")
        ttk.Button(left, text="Add", command=lambda: self.set_mode("add")).pack(fill="x")
        ttk.Button(left, text="Erase", command=lambda: self.set_mode("erase")).pack(fill="x")
        ttk.Button(left, text="Rotate 90", command=self.rotate_asset).pack(fill="x")
        ttk.Button(left, text="Mirror X", command=self.mirror_x).pack(fill="x")
        ttk.Button(left, text="Mirror Y", command=self.mirror_y).pack(fill="x")

        ttk.Button(left, text="Guardar Asset", command=self.save_asset).pack(fill="x")
        ttk.Button(left, text="Load Existing Asset", command=self.load_existing_asset).pack(fill="x")

        tk.Label(left, text="Top Texture").pack()
        self.top_tex = ttk.Combobox(left, values=self.parent_toolkit.texture_manager.floor_textures)
        self.top_tex.pack(fill="x")

        tk.Label(left, text="Side Texture").pack()
        self.side_tex = ttk.Combobox(left, values=self.parent_toolkit.texture_manager.wall_textures)
        self.side_tex.pack(fill="x")

        self.grid = tk.Canvas(
            self.win,
            width=ASSET_GRID * ASSET_CELL,
            height=ASSET_GRID * ASSET_CELL,
            bg="#202020"
        )
        self.grid.pack(side="left")
        self.grid.bind("<Button-1>", self.paint)

        #self.preview_gl = AssetPreviewGL(self.win, width=420, height=420)
        self.preview_gl.pack(side="right", fill="both", expand=True)
        self.preview_gl.builder_ref = self

        self.draw_grid()
        

    def set_mode(self, mode):
        self.mode = mode

    def layer_up(self):
        self.layer += 1
        self.draw_grid()
        self.draw_preview()

    def load_existing_asset(self):
        sel = self.parent_toolkit.asset_listbox.curselection()
        if not sel:
            messagebox.showwarning("Asset Builder", "Seleccioná un asset en la lista principal.")
            return

        name = self.parent_toolkit.asset_listbox.get(sel[0])

        if name not in self.parent_toolkit.assets:
            return

        asset = self.parent_toolkit.assets[name]

        self.selected_asset_name = name
        self.loaded_asset = asset

        if asset.mode == "voxel":
            self.voxels = list(asset.cubes)
        else:
            self.voxels = []

        if hasattr(asset, "tex_top"):
            self.top_tex.set(asset.tex_top or "")

        if hasattr(asset, "tex_side"):
            self.side_tex.set(asset.tex_side or "")

        self.draw_grid()
        self.draw_preview()

    def layer_down(self):
        self.layer = max(0, self.layer - 1)
        self.draw_grid()
        self.draw_preview()

    def rotate_asset(self):
        self.voxels = [(vy, ASSET_GRID - 1 - vx, vz) for vx, vy, vz in self.voxels]
        self.draw_grid()
        self.draw_preview()

    def mirror_x(self):
        self.voxels = [(ASSET_GRID - 1 - vx, vy, vz) for vx, vy, vz in self.voxels]
        self.draw_grid()
        self.draw_preview()

    def mirror_y(self):
        self.voxels = [(vx, ASSET_GRID - 1 - vy, vz) for vx, vy, vz in self.voxels]
        self.draw_grid()
        self.draw_preview()

    def paint(self, e):
        gx = e.x // ASSET_CELL
        gy = e.y // ASSET_CELL

        voxel = (gx, gy, self.layer)

        if self.mode == "add" and voxel not in self.voxels:
            self.voxels.append(voxel)

        if self.mode == "erase" and voxel in self.voxels:
            self.voxels.remove(voxel)

        self.draw_grid()
        self.draw_preview()

    def iso(self, x, y, z):
        sx = 140 + (x - y) * 10
        sy = 220 + (x + y) * 5 - z * 12
        return sx, sy

    def draw_grid(self):
        self.grid.delete("all")

        for y in range(ASSET_GRID):
            for x in range(ASSET_GRID):
                px = x * ASSET_CELL
                py = y * ASSET_CELL
                color = "#303030"

                for vx, vy, vz in self.voxels:
                    if vx == x and vy == y and vz < self.layer:
                        color = "#305050"
                    if vx == x and vy == y and vz == self.layer:
                        color = "cyan"

                self.grid.create_rectangle(
                    px, py,
                    px + ASSET_CELL,
                    py + ASSET_CELL,
                    fill=color,
                    outline="#505050"
                )

    def draw_preview(self):
        if hasattr(self, "preview_gl"):
            self.preview_gl.redraw()

    def save_asset(self):
        name = self.selected_asset_name

        if not name:
            name = simpledialog.askstring("Guardar", "Nombre del asset:")
            if not name:
                return

        asset = LowPolyAsset(name)
        asset.mode = "voxel"
        asset.cubes = list(self.voxels)
        asset.tex_top = self.top_tex.get() or None
        asset.tex_side = self.side_tex.get() or None

        self.parent_toolkit.assets[name] = asset
        self.parent_toolkit.refresh_asset_list()
        self.loaded_asset = asset
        
        self.win.destroy()
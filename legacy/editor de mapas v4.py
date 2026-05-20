import copy
import tkinter as tk
from tkinter import ttk, simpledialog, filedialog
from tkinter import messagebox
from pyopengltk import OpenGLFrame
from OpenGL.GL import *
from OpenGL.GLU import *
from PIL import Image, ImageTk
import math
import os
import json
import shutil

GRID_W = 24
GRID_H = 24
CELL_PIXELS = 28

ASSET_GRID = 16
ASSET_CELL = 20

base_path = os.path.dirname(__file__)
tex_path = os.path.join(base_path, "textures")
TEXTURE_FOLDER = tex_path
EXPORT_FOLDER = base_path + "/export_dc"

def rotate_3d(x, y, z, rx, ry, rz):
        import math

        # X rotation
        cosa = math.cos(math.radians(rx))
        sina = math.sin(math.radians(rx))
        y, z = y*cosa - z*sina, y*sina + z*cosa

        # Y rotation
        cosb = math.cos(math.radians(ry))
        sinb = math.sin(math.radians(ry))
        x, z = x*cosb + z*sinb, -x*sinb + z*cosb

        # Z rotation
        cosc = math.cos(math.radians(rz))
        sinc = math.sin(math.radians(rz))
        x, y = x*cosc - y*sinc, x*sinc + y*cosc

        return x, y, z


# =========================================================
# DATA CLASSES
# =========================================================

class Tile:
    def __init__(self):
        self.floor_tex = None
        self.wall_tex = None

        self.floor_height = 0.0

        self.wall_n = False
        self.wall_s = False
        self.wall_e = False
        self.wall_w = False
        self.wall_ne = False
        self.wall_nw = False
        self.wall_se = False
        self.wall_sw = False

        self.wall_n_height = 1.0
        self.wall_s_height = 1.0
        self.wall_e_height = 1.0
        self.wall_w_height = 1.0
        self.wall_ne_height = 1.0
        self.wall_se_height = 1.0
        self.wall_nw_height = 1.0
        self.wall_sw_height = 1.0

        self.objects = []


class LowPolyAsset:
    def __init__(self, name):
        self.name = name
        self.cubes = []

        self.tex_top = None
        self.tex_side = None

        self.mode = "voxel"
        self.mesh_vertices = []
        self.mesh_faces = []
        self.mesh_uvs = []
        self.mesh_tex = None

        self.mesh_texcoords = []
        self.mesh_face_uvs = []
        self.mesh_material = None
        self.mesh_face_materials = []
        self.mesh_material_textures = {}


# =========================================================
# TEXTURE MANAGER
# =========================================================

class TextureManager:
    def __init__(self):
        self.floor_textures = []
        self.wall_textures = []
        self.previews = {}
        self.gl_textures = {}
        self.scan()

    def scan(self):
        if not os.path.exists(TEXTURE_FOLDER):
            os.makedirs(TEXTURE_FOLDER)

        self.floor_textures.clear()
        self.wall_textures.clear()
        self.previews.clear()

        for f in os.listdir(TEXTURE_FOLDER):
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                path = os.path.join(TEXTURE_FOLDER, f)

                try:
                    img = Image.open(path).resize((32, 32))
                    self.previews[f] = ImageTk.PhotoImage(img)

                    low = f.lower()

                    if "wall" in low:
                        self.wall_textures.append(f)
                    elif "floor" in low:
                        self.floor_textures.append(f)
                    else:
                        self.floor_textures.append(f)
                        self.wall_textures.append(f)

                except:
                    pass

    def load_gl_texture(self, name):
        if not name:
            return None

        if name in self.gl_textures:
            return self.gl_textures[name]

        path = os.path.join(TEXTURE_FOLDER, name)

        if not os.path.exists(path):
            print("TEXTURE NOT FOUND:", path)
            return None

        try:
            img = Image.open(path).convert("RGBA")
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
            data = img.tobytes()

            texid = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texid)

            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

            glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)

            glTexImage2D(
                GL_TEXTURE_2D,
                0,
                GL_RGBA,
                img.width,
                img.height,
                0,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                data
            )

            glBindTexture(GL_TEXTURE_2D, 0)

            self.gl_textures[name] = texid
            print("LOADED TEXTURE:", name)

            return texid

        except Exception as e:
            print("TEXTURE LOAD ERROR:", e)
            return None


# =========================================================
# ASSET BUILDER 3D
# =========================================================

class AssetPreviewGL(OpenGLFrame):

    def initgl(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)

        self.angx = 25
        self.angy = -35
        self.zoom = 4

        self.builder_ref = None

        self.bind("<Button-1>", self.start_rot)
        self.bind("<B1-Motion>", self.drag_rot)
        self.bind("<MouseWheel>", self.do_zoom)

    def start_rot(self, e):
        self.lx = e.x
        self.ly = e.y

    def drag_rot(self, e):
        dx = e.x - self.lx
        dy = e.y - self.ly
        self.angy += dx * 0.5
        self.angx += dy * 0.5
        self.lx = e.x
        self.ly = e.y
        self.redraw()

    def do_zoom(self, e):
        if e.delta > 0:
            self.zoom -= 0.3
        else:
            self.zoom += 0.3

        self.zoom = max(1.5, min(10, self.zoom))
        self.redraw()

    def draw_mesh_preview(self, asset):
        tm = self.builder_ref.parent_toolkit.texture_manager
        current_bound = None

        for fi, face in enumerate(asset.mesh_faces):

            face_mat = None
            if fi < len(asset.mesh_face_materials):
                face_mat = asset.mesh_face_materials[fi]

            texname = None
            if face_mat in asset.mesh_material_textures:
                texname = asset.mesh_material_textures[face_mat]

            texid = tm.load_gl_texture(texname) if texname else None

            if texid != current_bound:
                if texid:
                    glEnable(GL_TEXTURE_2D)
                    glBindTexture(GL_TEXTURE_2D, texid)
                    glColor3f(1,1,1)
                else:
                    glDisable(GL_TEXTURE_2D)
                    glColor3f(1,1,1)

                current_bound = texid

            uvids = asset.mesh_face_uvs[fi] if fi < len(asset.mesh_face_uvs) else []

            if len(face) < 3:
                continue

            for t in range(1, len(face)-1):
                tri = [0,t,t+1]

                glBegin(GL_TRIANGLES)

                for li in tri:
                    idx = face[li]
                    vx,vy,vz = asset.mesh_vertices[idx]

                    wx = vx * ASSET_GRID
                    wy = vy * ASSET_GRID
                    wz = vz * ASSET_GRID

                    if li < len(uvids) and uvids[li] < len(asset.mesh_texcoords):
                        tu,tv = asset.mesh_texcoords[uvids[li]]
                        glTexCoord2f(tu,1-tv)
                    else:
                        glTexCoord2f(0,0)

                    glVertex3f(wx,wy,wz)

                glEnd()

        glBindTexture(GL_TEXTURE_2D,0)
        glEnable(GL_TEXTURE_2D)

    def redraw(self):
        glViewport(0,0,self.winfo_width(),self.winfo_height())
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, self.winfo_width()/max(1,self.winfo_height()), 0.1, 100)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glTranslatef(-1.5,-1.0,-self.zoom)
        glRotatef(self.angx,1,0,0)
        glRotatef(self.angy,0,1,0)

        if not self.builder_ref:
            return

        builder = self.builder_ref

        # =========================================
        # SHOW LOADED ASSET IF EXISTS
        # =========================================
        asset = builder.loaded_asset

        if asset:
            if asset.mode == "mesh":
                self.draw_mesh_preview(asset)
            else:
                for cx,cy,cz in builder.voxels:
                    self.draw_solid_cube(cx,cz,cy)
        else:
            for cx,cy,cz in builder.voxels:
                self.draw_solid_cube(cx,cz,cy)

        # helper floor
        glDisable(GL_TEXTURE_2D)
        glColor3f(0.3,0.3,0.3)

        glBegin(GL_LINES)
        for i in range(ASSET_GRID+1):
            glVertex3f(i,0,0)
            glVertex3f(i,0,ASSET_GRID)

            glVertex3f(0,0,i)
            glVertex3f(ASSET_GRID,0,i)
        glEnd()

        glEnable(GL_TEXTURE_2D)

    def draw_solid_cube(self, x, y, z, s=1):
        p = [
            (x,y,z),
            (x+s,y,z),
            (x+s,y+s,z),
            (x,y+s,z),
            (x,y,z+s),
            (x+s,y,z+s),
            (x+s,y+s,z+s),
            (x,y+s,z+s)
        ]

        faces = [
            (0,1,2,3),
            (4,5,6,7),
            (0,1,5,4),
            (1,2,6,5),
            (2,3,7,6),
            (3,0,4,7)
        ]

        glBegin(GL_QUADS)
        for f in faces:
            for idx in f:
                glVertex3f(*p[idx])
        glEnd()
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

        self.preview_gl = AssetPreviewGL(self.win, width=420, height=420)
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

class GLViewport(OpenGLFrame):
    def initgl(self):
        self.manipulating_object = False
        self.space_held = True
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        glDisable(GL_CULL_FACE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glClearColor(0.08, 0.08, 0.1, 1)

        self.dragging_gizmo = False
        self.drag_mode = None
        self.last_mouse_x = 0
        self.last_mouse_y = 0

        self.cam_rot_x = 55
        self.cam_rot_y = 45
        self.cam_dist = 35

        self.pan_x = 12
        self.pan_z = 12

        self.last_x = 0
        self.last_y = 0

        self.hover_tile = None
        self.animate = 1

    def draw_mesh_asset(self, asset, inst, tilex, tiley, floor_h, texman):

        current_bound_tex = None

        for fi, face in enumerate(asset.mesh_faces):

            face_mat = None
            if fi < len(asset.mesh_face_materials):
                face_mat = asset.mesh_face_materials[fi]

            texname = None
            if face_mat in asset.mesh_material_textures:
                texname = asset.mesh_material_textures[face_mat]

            texid = texman.load_gl_texture(texname) if texname else None

            if texid != current_bound_tex:
                if texid:
                    glEnable(GL_TEXTURE_2D)
                    glBindTexture(GL_TEXTURE_2D, texid)
                    glColor3f(1,1,1)
                else:
                    glDisable(GL_TEXTURE_2D)
                    glColor3f(1,1,1)

                current_bound_tex = texid

            uvids = asset.mesh_face_uvs[fi] if fi < len(asset.mesh_face_uvs) else []

            # ====================================
            # triangulación fan
            # ====================================
            if len(face) < 3:
                continue

            for t in range(1, len(face)-1):
                tri_idx = [0, t, t+1]

                glBegin(GL_TRIANGLES)

                for local_i in tri_idx:
                    idx = face[local_i]

                    vx,vy,vz = asset.mesh_vertices[idx]

                    lx, ly, lz = rotate_3d(
                        vx, vy, vz,
                        inst["rot_x"],
                        inst["rot_y"],
                        inst["rot_z"])

                    wx = tilex + inst["offx"] + lx
                    wy = floor_h + inst["offz"] + ly
                    wz = tiley + inst["offy"] + lz

                    if local_i < len(uvids) and uvids[local_i] < len(asset.mesh_texcoords):
                        tu,tv = asset.mesh_texcoords[uvids[local_i]]
                        glTexCoord2f(tu,1-tv)
                    else:
                        glTexCoord2f(0,0)

                    glVertex3f(wx,wy,wz)

                glEnd()
                

        glBindTexture(GL_TEXTURE_2D,0)
        glEnable(GL_TEXTURE_2D)

    def project_world_to_screen_iso(self, wx, wz):
        sx = (wx - wz) * 32 + (self.winfo_width() // 2)
        sy = (wx + wz) * 16 + 120
        return sx, sy
    
    def pick_object_under_mouse(self, mx, my):
        if not hasattr(self, 'toolkit_ref'):
            return None

        tool = self.toolkit_ref

        best = None
        best_dist = 999999

        for y in range(GRID_H):
            for x in range(GRID_W):
                t = tool.grid[y][x]

                if not t.objects:
                    continue

                for inst in t.objects:
                    wx = x + inst["offx"] + 0.5
                    wz = y + inst["offy"] + 0.5

                    sx, sy = self.project_world_to_screen_iso(wx, wz)

                    d = ((mx - sx)**2 + (my - sy)**2)**0.5

                    if d < 150 and d < best_dist:
                        best = {
                            "inst": inst,
                            "gx": x,
                            "gy": y
                        }
                        best_dist = d

        return best

    def on_mouse_release(self, event):
        self.dragging_gizmo = False
        self.drag_mode = None
        self.manipulating_object = False

    def on_mouse_drag(self, event):
        if not self.dragging_gizmo:
            return

        tool = self.toolkit_ref

        if not tool.selected_instance:
            return

        sel = tool.selected_instance
        inst = sel["inst"]

        dx = event.x - self.last_mouse_x
        dy = event.y - self.last_mouse_y

        if self.drag_mode == "xy":
            inst["offx"] += dx * 0.01
            inst["offy"] += dy * 0.01

        elif self.drag_mode == "z":
            inst["offz"] -= dy * 0.01

        tool.load_instance_into_panel(sel)
        tool.draw_grid()

        self.last_mouse_x = event.x
        self.last_mouse_y = event.y


    def rotate_local_point(self, lx, ly, rot):
        if rot == 90:
            return -ly, lx
        elif rot == 180:
            return -lx, -ly
        elif rot == 270:
            return ly, -lx
        return lx, ly
    
    def draw_transform_gizmo(self, sel, floor_h=0):
        if not sel:
            return

        inst = self.toolkit_ref.selected_instance

        if not inst:
            return
        
        if "offx" not in inst:
            return

        ox = sel["gx"] + inst["offx"] + 0.5
        oy = floor_h + inst["offz"] + 0.5
        oz = sel["gy"] + inst["offy"] + 0.5

        glDisable(GL_TEXTURE_2D)
        glLineWidth(4)

        # X
        glColor3f(1,0,0)
        glBegin(GL_LINES)
        glVertex3f(ox,oy,oz)
        glVertex3f(ox+1.2,oy,oz)
        glEnd()

        # Y
        glColor3f(0,1,0)
        glBegin(GL_LINES)
        glVertex3f(ox,oy,oz)
        glVertex3f(ox,oy+1.2,oz)
        glEnd()

        # Z
        glColor3f(0,0,1)
        glBegin(GL_LINES)
        glVertex3f(ox,oy,oz)
        glVertex3f(ox,oy,oz+1.2)
        glEnd()

        # Rotation ring
        glColor3f(1,1,0)
        glBegin(GL_LINE_LOOP)
        for i in range(24):
            ang = math.radians(i * 15)
            px = ox + math.cos(ang) * 0.7
            pz = oz + math.sin(ang) * 0.7
            glVertex3f(px, oy, pz)
        glEnd()

        glLineWidth(1)
        glEnable(GL_TEXTURE_2D)
        glColor3f(1,1,1)

    def redraw(self):
        glViewport(0, 0, self.width, self.height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, max(1, self.width) / max(1, self.height), 0.1, 1000)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        radx = math.radians(self.cam_rot_x)
        rady = math.radians(self.cam_rot_y)

        cx = math.cos(rady) * math.cos(radx) * self.cam_dist
        cy = math.sin(radx) * self.cam_dist
        cz = math.sin(rady) * math.cos(radx) * self.cam_dist

        gluLookAt(
            cx + self.pan_x, cy, cz + self.pan_z,
            self.pan_x, 0, self.pan_z,
            0, 1, 0
        )

        if hasattr(self, "toolkit_ref"):
            self.draw_world(self.toolkit_ref)

        glFlush()

    def draw_quad(self, v1, v2, v3, v4):
        glBegin(GL_QUADS)
        glVertex3f(*v1)
        glVertex3f(*v2)
        glVertex3f(*v3)
        glVertex3f(*v4)
        glEnd()

    def textured_quad(self,p1,p2,p3,p4,texid,uv_scale_x=1,uv_scale_y=1):
        if texid is not None:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, texid)
            glColor3f(1,1,1)
        else:
            glDisable(GL_TEXTURE_2D)
            glColor3f(1,1,1)

        glBegin(GL_QUADS)

        glTexCoord2f(0,0); glVertex3f(*p1)
        glTexCoord2f(uv_scale_x,0); glVertex3f(*p2)
        glTexCoord2f(uv_scale_x,uv_scale_y); glVertex3f(*p3)
        glTexCoord2f(0,uv_scale_y); glVertex3f(*p4)

        glEnd()

        glBindTexture(GL_TEXTURE_2D,0)

    def cube(self, x, y, z, s=1, h=0.05, toptex=None, sidetex=None):
        # bottom
        self.textured_quad((x,z,y),(x+s,z,y),(x+s,z,y+s),(x,z,y+s), sidetex)

        # top
        self.textured_quad((x,z+h,y),(x+s,z+h,y),(x+s,z+h,y+s),(x,z+h,y+s), toptex)

        # north
        self.textured_quad((x,z,y),(x+s,z,y),(x+s,z+h,y),(x,z+h,y), sidetex)

        # east
        self.textured_quad((x+s,z,y),(x+s,z,y+s),(x+s,z+h,y+s),(x+s,z+h,y), sidetex)

        # west
        self.textured_quad((x,z,y+s),(x,z,y),(x,z+h,y),(x,z+h,y+s), sidetex)

        # south
        self.textured_quad((x+s,z,y+s),(x,z,y+s),(x,z+h,y+s),(x+s,z+h,y+s), sidetex)

    def get_exact_tile(self, mx, my):
        model = glGetDoublev(GL_MODELVIEW_MATRIX)
        proj = glGetDoublev(GL_PROJECTION_MATRIX)
        view = glGetIntegerv(GL_VIEWPORT)

        near = gluUnProject(mx, view[3]-my, 0, model, proj, view)
        far  = gluUnProject(mx, view[3]-my, 1, model, proj, view)

        dx = far[0] - near[0]
        dy = far[1] - near[1]
        dz = far[2] - near[2]

        if dy == 0:
            return None

        t = -near[1] / dy

        ix = near[0] + dx * t
        iz = near[2] + dz * t

        gx = int(ix)
        gy = int(iz)

        if 0 <= gx < GRID_W and 0 <= gy < GRID_H:
            return gx, gy

        return None
    
    def update_sprites(self, dt):
        for y in range(GRID_H):
            for x in range(GRID_W):
                tile = self.grid[y][x]

                for inst in tile.objects:
                    if inst.get("type") != "sprite":
                        continue

                    inst["time"] += dt

                    if inst["time"] >= 1.0 / inst["fps"]:
                        inst["frame"] = (inst["frame"] + 1) % (inst["cols"] * inst["rows"])
                        inst["time"] = 0
    
    def update_animated_textures(self, dt):
        for tex in self.animated_textures.values():
            tex["time"] += dt

            if tex["time"] > 1.0 / tex["fps"]:
                tex["current"] = (tex["current"] + 1) % len(tex["frames"])
                tex["time"] = 0

    def render_gizmos(self, tool):
        if tool.selected_instance:
            self.draw_transform_gizmo(tool.selected_instance)
    
    def draw_sprite_billboard(self, inst, cam):
        frames = inst["frames"]
        frame = frames[inst["frame"]]

        texid = self.texture_manager.load_gl_texture(frame)
        glBindTexture(GL_TEXTURE_2D, texid)

        x,y,z = inst["offx"], inst["offy"], inst["offz"]

        size = inst.get("size", 0.5)

        # billboard simple (cara a cámara)
        glBegin(GL_QUADS)

        glTexCoord2f(0,0); glVertex3f(x-size,y,z-size)
        glTexCoord2f(1,0); glVertex3f(x+size,y,z-size)
        glTexCoord2f(1,1); glVertex3f(x+size,y,z+size)
        glTexCoord2f(0,1); glVertex3f(x-size,y,z+size)

        glEnd()
    
    def render_sprites(self, tool):
        cam = tool.camera

        for y in range(GRID_H):
            for x in range(GRID_W):
                tile = tool.grid[y][x]

                for inst in tile.objects:
                    if inst.get("type") != "sprite":
                        continue

                    self.draw_sprite_billboard(inst, cam)

    def draw_sprite(self, inst, texid):
        cols = inst["cols"]
        rows = inst["rows"]

        frame = inst["frame"]

        u = frame % cols
        v = frame // cols

        du = 1.0 / cols
        dv = 1.0 / rows

        u0 = u * du
        v0 = v * dv
        u1 = u0 + du
        v1 = v0 + dv

        x = inst["offx"]
        y = inst["offy"]
        z = inst["offz"]

        size = 0.5

        glBindTexture(GL_TEXTURE_2D, texid)

        glBegin(GL_QUADS)

        glTexCoord2f(u0, v0); glVertex3f(x-size, y, z-size)
        glTexCoord2f(u1, v0); glVertex3f(x+size, y, z-size)
        glTexCoord2f(u1, v1); glVertex3f(x+size, y, z+size)
        glTexCoord2f(u0, v1); glVertex3f(x-size, y, z+size)

        glEnd()
    
    def render_meshes(self, tool):
        tm = tool.texture_manager

        for y in range(GRID_H):
            for x in range(GRID_W):
                tile = tool.grid[y][x]

                for inst in tile.objects:
                    asset = tool.assets.get(inst["asset"])
                    if not asset:
                        continue

                    if asset.mode == "mesh":
                        self.draw_mesh_asset(asset, inst, x, y, tile.floor_height, tm)

    def draw_diag_wall(self, x, y, t, tm):
        tex = tm.load_gl_texture(t.wall_tex) if t.wall_tex else None
        if not tex:
            return

        fh = t.floor_height
        h = fh + t.wall_n_height

        glBindTexture(GL_TEXTURE_2D, tex)
        glBegin(GL_TRIANGLES)

        if t.wall_ne or t.wall_sw:

            A = (x,   fh, y)
            B = (x+1, fh, y+1)
            C = (x+1, h,  y+1)
            D = (x,   h,  y)

        if t.wall_nw or t.wall_se:

            A = (x+1, fh, y)
            B = (x,   fh, y+1)
            C = (x,   h,  y+1)
            D = (x+1, h,  y)

        # NE wall (vertical split)
        if getattr(t, "wall_ne", False):

            # tri 1
            glTexCoord2f(0,0); glVertex3f(*A)
            glTexCoord2f(1,0); glVertex3f(*B)
            glTexCoord2f(1,1); glVertex3f(*C)

            # tri 2
            glTexCoord2f(0,0); glVertex3f(*A)
            glTexCoord2f(1,1); glVertex3f(*C)
            glTexCoord2f(0,1); glVertex3f(*D)

         # NW wall (vertical split)
        if getattr(t, "wall_nw", False):

            # tri 1
            glTexCoord2f(0,0); glVertex3f(*A)
            glTexCoord2f(1,0); glVertex3f(*B)
            glTexCoord2f(1,1); glVertex3f(*C)

            # tri 2
            glTexCoord2f(0,0); glVertex3f(*A)
            glTexCoord2f(1,1); glVertex3f(*C)
            glTexCoord2f(0,1); glVertex3f(*D)

        if getattr(t, "wall_se", False):

            # tri 1 (invertido en Y visual)
            glTexCoord2f(0,0); glVertex3f(*D)
            glTexCoord2f(1,0); glVertex3f(*C)
            glTexCoord2f(1,1); glVertex3f(*B)

            # tri 2
            glTexCoord2f(0,0); glVertex3f(*D)
            glTexCoord2f(1,1); glVertex3f(*B)
            glTexCoord2f(0,1); glVertex3f(*A)

        if getattr(t, "wall_sw", False):

            # tri 1
            glTexCoord2f(0,0); glVertex3f(*B)
            glTexCoord2f(1,0); glVertex3f(*A)
            glTexCoord2f(1,1); glVertex3f(*D)

            # tri 2
            glTexCoord2f(0,0); glVertex3f(*B)
            glTexCoord2f(1,1); glVertex3f(*D)
            glTexCoord2f(0,1); glVertex3f(*C)

        glEnd()

    def draw_tile_walls(self, x, y, t, tm):
        wall_texid = tm.load_gl_texture(t.wall_tex) if t.wall_tex else None
        fh = t.floor_height
        h = fh + t.wall_n_height
        

        if t.wall_n:
            h = fh + t.wall_n_height
            self.textured_quad(
                (x,fh,y),
                (x+1,fh,y),
                (x+1,h,y),
                (x,h,y),
                wall_texid,
                1,
                t.wall_n_height
            )

        if t.wall_s:
            self.textured_quad(
                (x,fh,y+1),
                (x+1,fh,y+1),
                (x+1,h,y+1),
                (x,h,y+1),
                wall_texid,
                1,
                t.wall_n_height
            )

        if t.wall_e:
            self.textured_quad(
                (x+1,fh,y),
                (x+1,fh,y+1),
                (x+1,h,y+1),
                (x+1,h,y),
                wall_texid,
                1,
                t.wall_n_height
            )

        if t.wall_w:
            self.textured_quad(
                (x,fh,y),
                (x,fh,y+1),
                (x,h,y+1),
                (x,h,y),
                wall_texid,
                1,
                t.wall_n_height
            )

        self.draw_diag_wall(x, y, t, tm)


    
    def render_tiles(self, tool):
        tm = tool.texture_manager

        # FLOORS
        merged_floors = tool.build_merged_floors()

        for x,y,w,h,tex,fh in merged_floors:
            texid = tm.load_gl_texture(tex) if tex else None

            self.textured_quad(
                (x,fh,y),
                (x+w,fh,y),
                (x+w,fh,y+h),
                (x,fh,y+h),
                texid,
                w,
                h
            )

        # WALLS
        for y in range(GRID_H):
            for x in range(GRID_W):
                t = tool.grid[y][x]
                self.draw_tile_walls(x,y,t,tm)

    def draw_world(self, tool):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glEnable(GL_TEXTURE_2D)
        glColor3f(1,1,1)

        tm = tool.texture_manager

        # ======================================
        # PIPELINE NUEVO
        # ======================================
        self.render_tiles(tool)
        self.render_meshes(tool)
        self.render_sprites(tool)

        # ======================================
        # HOVER TILE (DEBUG VISUAL)
        # ======================================
        if self.hover_tile:
            gx, gy = self.hover_tile
            hf = tool.grid[gy][gx].floor_height

            glDisable(GL_TEXTURE_2D)
            glColor4f(1,1,0,0.35)

            self.draw_quad(
                (gx,hf+0.05,gy),
                (gx+1,hf+0.05,gy),
                (gx+1,hf+0.05,gy+1),
                (gx,hf+0.05,gy+1)
            )

            glEnable(GL_TEXTURE_2D)
            glColor3f(1,1,1)

        # ======================================
        # GIZMO (solo si hay selección válida)
        # ======================================
        if tool.selected_instance:
            inst = tool.selected_instance

            if "gx" in inst and "gy" in inst:
                fh = tool.grid[inst["gy"]][inst["gx"]].floor_height
                self.draw_transform_gizmo(inst, fh)

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0
        self.yaw = 0
        self.pitch = 0
        self.zoom = 1

class Toolkit:
    def __init__(self,root):
        self.root=root
        self.root.title('Dreamcast Toolkit V8.1')
        self.grid=[[Tile() for _ in range(GRID_W)] for _ in range(GRID_H)]
        self.assets={}
        self.selected_tool='floorpaint'
        self.selected_asset=None
        self.selected_instance = None
        self.obj_offx = tk.DoubleVar(value=0.0)
        self.obj_offy = tk.DoubleVar(value=0.0)
        self.obj_offz = tk.DoubleVar(value=0.0)
        self.obj_rot_x = tk.IntVar(value=0)
        self.obj_rot_y = tk.IntVar(value=0)
        self.obj_rot_z = tk.IntVar(value=0)
        self.texture_manager=TextureManager()
        self.selected_texture=None
        self.texture_assign_mode=tk.StringVar(value='floor')
        self.texture_thumb_refs=[]
        self.texture_preview_ref=None
        self.current_floor_height = tk.DoubleVar(value=0.0)
        self.current_wall_height = tk.DoubleVar(value=1.0)
        self.prefab_buffer = None
        self.prefab_start = None
        self.prefab_end = None
        self.camera = Camera()
        self.build_ui()

    def build_ui(self):
        left=tk.Frame(self.root)
        left.pack(side='left',fill='y')
        center=tk.Frame(self.root)
        center.pack(side='left')
        top_map_panel = tk.Frame(center)
        top_map_panel.pack(fill='x', pady=4)

        asset_top_frame = tk.Frame(top_map_panel)
        asset_top_frame.pack(side='left', padx=5, anchor='n')

        prop_frame = tk.Frame(top_map_panel)
        prop_frame.pack(side='left', padx=20, anchor='n')

        prop_frame_2 = tk.Frame(top_map_panel)
        prop_frame_2.pack(side='left', padx=40, anchor='n')

        prop_frame_3 = tk.Frame(top_map_panel)
        prop_frame_3.pack(side='left', padx=60, anchor='n')

        for txt,val in [
            ('Pintar Piso','floorpaint'),
            ('Pared N','wall_n'),
            ('Pared NE','wall_ne'),
            ('Pared NO','wall_nw'),
            ('Pared S','wall_s'),
            ('Pared SE','wall_se'),
            ('Pared SO','wall_sw'),
            ('Pared E','wall_e'),
            ('Pared O','wall_w'),
            ('Colocar Asset','placeobj')
        ]:
            ttk.Button(left,text=txt,command=lambda v=val:self.set_tool(v)).pack(fill='x')

        tk.Button(prop_frame,text='Import OBJ Asset',command=self.import_obj_asset).pack(fill='x')
        tk.Button(prop_frame,text='Import OBJ Mesh',command=self.import_obj_mesh_asset).pack(fill='x')
        tk.Button(prop_frame,text='Select Obj',command=lambda:self.set_tool('selectobj')).pack(fill='x')

        tk.Button(left,text='Prefab Start',command=lambda:self.set_tool('prefab_start')).pack(fill='x')
        tk.Button(left,text='Prefab End',command=lambda:self.set_tool('prefab_end')).pack(fill='x')
        tk.Button(left,text='Paste Prefab',command=lambda:self.set_tool('prefab_paste')).pack(fill='x')

        ttk.Button(left,text='Abrir Asset Builder',command=self.open_asset_builder).pack(fill='x')
        ttk.Button(left,text='Guardar Proyecto',command=self.save_project).pack(fill='x')
        ttk.Button(left,text='Cargar Proyecto',command=self.load_project).pack(fill='x')
        ttk.Button(left,text='EXPORT DREAMCAST',command=self.export_dreamcast).pack(fill='x')

        tk.Label(left,text='Preview textura').pack(pady=4)

        self.texture_canvas=tk.Canvas(left,width=128,height=128,bg='black')
        self.texture_canvas.pack()

        self.texture_name_label=tk.Label(left,text='(sin textura)',wraplength=130)
        self.texture_name_label.pack()

        tk.Label(prop_frame,text='Asignar como').pack()

        tk.Radiobutton(prop_frame,text='Floor',variable=self.texture_assign_mode,value='floor').pack(anchor='w')
        tk.Radiobutton(prop_frame,text='Wall',variable=self.texture_assign_mode,value='wall').pack(anchor='w')

        tk.Label(prop_frame,text='Floor Height').pack()
        tk.Spinbox(
            prop_frame,
            from_=-2.0,
            to=5.0,
            increment=0.1,
            textvariable=self.current_floor_height,
            width=8
        ).pack()

        tk.Label(prop_frame,text='Wall Height').pack()
        tk.Spinbox(
            prop_frame,
            from_=0.2,
            to=6.0,
            increment=0.1,
            textvariable=self.current_wall_height,
            width=8
        ).pack()

        tk.Label(prop_frame_2,text='Object Transform').pack(pady=(10,0))

        tk.Label(prop_frame_2,text='Offset X').pack()
        tk.Scale(
            prop_frame_2,
            from_=-50,
            to=50,
            orient='horizontal',
            variable=self.obj_offx,
            command=lambda v: self.update_selected_instance_transform()
        ).pack(fill='x')
        #tk.Spinbox(prop_frame_2,from_=-1.0,to=1.0,increment=0.1,textvariable=self.obj_offx,width=8,
         #       command=self.update_selected_instance_transform).pack()

        tk.Label(prop_frame_2,text='Offset Y').pack()
        tk.Scale(
            prop_frame_2,
            from_=-50,
            to=50,
            orient='horizontal',
            variable=self.obj_offy,
            command=lambda v: self.update_selected_instance_transform()
        ).pack(fill='x')
        #tk.Spinbox(prop_frame_2,from_=-1.0,to=1.0,increment=0.1,textvariable=self.obj_offy,width=8,
         #       command=self.update_selected_instance_transform).pack()

        tk.Label(prop_frame_2,text='Offset Z').pack()
        tk.Scale(
            prop_frame_2,
            from_=-50,
            to=50,
            orient='horizontal',
            variable=self.obj_offz,
            command=lambda v: self.update_selected_instance_transform()
        ).pack(fill='x')
        #tk.Spinbox(prop_frame_2,from_=-1.0,to=2.0,increment=0.1,textvariable=self.obj_offz,width=8,
         #       command=self.update_selected_instance_transform).pack()

        tk.Label(prop_frame_3,text='Rotation').pack()

        tk.Label(prop_frame_3,text='Rotation X').pack()
        tk.Scale(
            prop_frame_3,
            from_=-360,
            to=360,
            orient='horizontal',
            variable=self.obj_rot_x,
            command=lambda v: self.update_selected_instance_transform()
        ).pack(fill='x')

        tk.Label(prop_frame_3,text='Rotation Y').pack()
        tk.Scale(
            prop_frame_3,
            from_=-360,
            to=360,
            orient='horizontal',
            variable=self.obj_rot_y,
            command=lambda v: self.update_selected_instance_transform()
        ).pack(fill='x')

        tk.Label(prop_frame_3,text='Rotation Z').pack()
        tk.Scale(
            prop_frame_3,
            from_=-360,
            to=360,
            orient='horizontal',
            variable=self.obj_rot_z,
            command=lambda v: self.update_selected_instance_transform()
        ).pack(fill='x')

        tk.Button(prop_frame_2,text='Delete Selected Obj',command=self.delete_selected_instance).pack(fill='x',pady=4)

        self.texture_browser_wrap=tk.Frame(left)
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

        tk.Label(asset_top_frame,text='Assets').pack()
        self.asset_listbox = tk.Listbox(asset_top_frame,height=10,width=22)
        self.asset_listbox.pack()
        self.asset_listbox.bind('<<ListboxSelect>>',self.select_asset)
        

        self.grid_canvas=tk.Canvas(center,width=GRID_W*CELL_PIXELS,height=GRID_H*CELL_PIXELS,bg='#202020')
        self.grid_canvas.pack()
        self.grid_canvas.bind('<Button-1>',self.paint_2d)

        self.viewport=GLViewport(self.root,width=900,height=700)
        self.viewport.pack(side='left',fill='both',expand=True)
        self.viewport.toolkit_ref=self

        self.viewport.bind("<ButtonPress-1>", self.on_mouse_press)
        self.viewport.bind("<B1-Motion>", self.viewport_mouse_drag)
        self.viewport.bind("<ButtonRelease-1>", self.viewport.on_mouse_release)

        self.viewport.bind("<Button-3>", self.start_pan)
        self.viewport.bind("<B3-Motion>", self.pan_camera)

        self.viewport.bind("<MouseWheel>", self.zoom_camera)
        self.viewport.bind("<Motion>", self.hover_3d)
        self.viewport.bind("<Double-Button-1>", self.paint_3d)

        self.root.bind("<KeyPress-Control_L>", self.space_down)
        self.root.bind("<KeyRelease-Control_L>", self.space_up)
        

        self.build_texture_browser()
        self.draw_grid()

    def find_texture_file(self, obj_dir, texname):
        target = os.path.basename(texname).strip().lower()

        search_dirs = [
            obj_dir,
            os.path.join(obj_dir, "textures")
        ]

        print("OBJ DIR =", obj_dir)
        print("TARGET TEX =", target)

        for folder in search_dirs:
            print("CHECK FOLDER =", folder)

            if not os.path.exists(folder):
                print("folder missing")
                continue

            print("FILES =", os.listdir(folder))

            for fname in os.listdir(folder):
                if fname.strip().lower() == target:
                    print("FOUND MATCH =", fname)
                    return os.path.join(folder, fname)

        return None
    
    
    def space_down(self, e):
        self.viewport.space_held = True

    def space_up(self, e):
        self.viewport.space_held = False

    def import_obj_mesh_asset(self):
        path = filedialog.askopenfilename(filetypes=[("OBJ Model","*.obj")])
        if not path:
            return

        obj_dir = os.path.dirname(path)

        verts = []
        texcoords = []
        faces = []
        face_uvs = []
        face_materials = []

        mtl_file = None
        current_material = None

        # ==========================================
        # PARSE OBJ
        # ==========================================
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for raw in f:
                line = raw.strip()

                if not line:
                    continue

                if line.startswith("mtllib"):
                    parts = line.split(maxsplit=1)
                    if len(parts) > 1:
                        mtl_file = parts[1].strip()

                elif line.startswith("usemtl"):
                    parts = line.split(maxsplit=1)
                    if len(parts) > 1:
                        current_material = parts[1].strip()

                elif line.startswith("v "):
                    p = line.split()
                    verts.append((float(p[1]), float(p[2]), float(p[3])))

                elif line.startswith("vt "):
                    p = line.split()
                    texcoords.append((float(p[1]), float(p[2])))

                elif line.startswith("f "):
                    idxs = []
                    uvs = []

                    parts = line.split()[1:]

                    for pp in parts:
                        sub = pp.split('/')

                        vidx = int(sub[0]) - 1
                        idxs.append(vidx)

                        if len(sub) > 1 and sub[1]:
                            tidx = int(sub[1]) - 1
                            uvs.append(tidx)

                    if len(idxs) >= 3:
                        faces.append(idxs)
                        face_uvs.append(uvs)
                        face_materials.append(current_material)

        if not verts or not faces:
            messagebox.showerror("OBJ Mesh", "No mesh data found.")
            return

        # ==========================================
        # PARSE MTL
        # ==========================================
        material_lib = {}

        if mtl_file:
            mtl_path = os.path.join(obj_dir, mtl_file)

            if os.path.exists(mtl_path):
                active_mat = None

                with open(mtl_path, "r", encoding="utf-8", errors="ignore") as mf:
                    for raw in mf:
                        line = raw.strip()

                        if not line:
                            continue

                        if line.startswith("newmtl"):
                            parts = line.split(maxsplit=1)
                            if len(parts) > 1:
                                active_mat = parts[1].strip()

                        elif line.startswith("map_Kd"):
                            parts = line.split(maxsplit=1)
                            if len(parts) > 1 and active_mat:
                                texname = os.path.basename(parts[1].strip())
                                material_lib[active_mat] = texname

        print("MTL materials =", material_lib)

        # ==========================================
        # COPY TEXTURES FOUND
        # ==========================================
        material_textures = {}

        for matname, texname in material_lib.items():
            tex_src = self.find_texture_file(obj_dir, texname)

            print("SEARCHING:", texname, "->", tex_src)

            if tex_src:
                tex_dst = os.path.join(TEXTURE_FOLDER, texname)

                try:
                    shutil.copy(tex_src, tex_dst)
                except:
                    pass

                material_textures[matname] = texname

        print("FACE MATERIAL TEXTURES =", material_textures)

        # ==========================================
        # NORMALIZE VERTICES TO TILE SPACE
        # ==========================================
        minx = min(v[0] for v in verts)
        maxx = max(v[0] for v in verts)
        miny = min(v[1] for v in verts)
        maxy = max(v[1] for v in verts)
        minz = min(v[2] for v in verts)
        maxz = max(v[2] for v in verts)

        sx = maxx - minx or 1
        sy = maxy - miny or 1
        sz = maxz - minz or 1

        nverts = []

        for vx, vy, vz in verts:
            nx = (vx - minx) / sx
            ny = (vy - miny) / sy
            nz = (vz - minz) / sz
            nverts.append((nx, ny, nz))

        # ==========================================
        # CREATE ASSET
        # ==========================================
        name = os.path.splitext(os.path.basename(path))[0]

        asset = LowPolyAsset(name)
        asset.mode = "mesh"
        asset.mesh_vertices = nverts
        asset.mesh_faces = faces
        asset.mesh_texcoords = texcoords
        asset.mesh_face_uvs = face_uvs
        asset.mesh_face_materials = face_materials
        asset.mesh_material_textures = material_textures
        asset.mesh_tex = None

        self.assets[name] = asset
        self.asset_listbox.insert(tk.END, name)

        messagebox.showinfo("OBJ Mesh", f"Imported textured mesh '{name}'")
    def copy_prefab_region(self):
        if not self.prefab_start or not self.prefab_end:
            return

        x1 = min(self.prefab_start[0], self.prefab_end[0])
        y1 = min(self.prefab_start[1], self.prefab_end[1])
        x2 = max(self.prefab_start[0], self.prefab_end[0])
        y2 = max(self.prefab_start[1], self.prefab_end[1])

        buf = []

        for y in range(y1, y2+1):
            row = []
            for x in range(x1, x2+1):
                row.append(copy.deepcopy(self.grid[y][x]))
            buf.append(row)

        self.prefab_buffer = buf
        messagebox.showinfo("Prefab", "Region copied.")

    def paste_prefab_region(self, gx, gy):
        if not self.prefab_buffer:
            return

        for y,row in enumerate(self.prefab_buffer):
            for x,tile in enumerate(row):
                tx = gx + x
                ty = gy + y

                if 0 <= tx < GRID_W and 0 <= ty < GRID_H:
                    self.grid[ty][tx] = copy.deepcopy(tile)

        self.draw_grid()

    def open_asset_builder(self):
        AssetBuilder3D(self)

    def parse_obj_vertices_faces(self, filepath):
        verts = []
        faces = []

        with open(filepath, 'r') as f:
            for line in f:
                if line.startswith('v '):
                    parts = line.strip().split()
                    verts.append((
                        float(parts[1]),
                        float(parts[2]),
                        float(parts[3])
                    ))

                elif line.startswith('f '):
                    parts = line.strip().split()[1:]
                    idxs = []

                    for p in parts:
                        idx = p.split('/')[0]
                        idxs.append(int(idx)-1)

                    if len(idxs) >= 3:
                        faces.append(idxs)

        return verts, faces
    
    def voxelize_obj(self, verts, faces, resolution=6):
        if not verts:
            return []

        minx = min(v[0] for v in verts)
        maxx = max(v[0] for v in verts)

        miny = min(v[1] for v in verts)
        maxy = max(v[1] for v in verts)

        minz = min(v[2] for v in verts)
        maxz = max(v[2] for v in verts)

        sx = maxx - minx
        sy = maxy - miny
        sz = maxz - minz

        sx = sx if sx != 0 else 1
        sy = sy if sy != 0 else 1
        sz = sz if sz != 0 else 1

        cubes = set()

        for vx,vy,vz in verts:
            gx = int(((vx - minx) / sx) * resolution)
            gy = int(((vz - minz) / sz) * resolution)
            gz = int(((vy - miny) / sy) * resolution)

            cubes.add((gx,gy,gz))

        return list(cubes)
    
    def import_obj_asset(self):
        path = filedialog.askopenfilename(filetypes=[("OBJ Model","*.obj")])
        if not path:
            return

        verts, faces = self.parse_obj_vertices_faces(path)

        cubes = self.voxelize_obj(verts, faces, resolution=6)

        if not cubes:
            messagebox.showerror("OBJ Import","No geometry found.")
            return

        name = os.path.splitext(os.path.basename(path))[0]

        asset = LowPolyAsset(name)
        asset.cubes = cubes

        # texturas default actuales seleccionadas
        asset.tex_top = self.selected_texture
        asset.tex_side = self.selected_texture

        self.assets[name] = asset

        self.asset_listbox.insert(tk.END, name)

        messagebox.showinfo("OBJ Import", f"Imported asset '{name}' with {len(cubes)} voxels.")

    def update_selected_instance_transform(self):
        if not self.selected_instance:
            return

        inst = self.selected_instance["inst"]

        inst["rot_x"] = float(self.obj_rot_x.get())
        inst["rot_y"] = float(self.obj_rot_y.get())
        inst["rot_z"] = float(self.obj_rot_z.get())
        inst["offx"] = float(self.obj_offx.get())
        inst["offy"] = float(self.obj_offy.get())
        inst["offz"] = float(self.obj_offz.get())

        self.draw_grid()

    def cycle_select_object_at_tile(self, gx, gy, tile):
        if not tile.objects:
            return

        if not self.selected_instance or self.selected_instance["inst"] not in tile.objects:
            self.load_instance_into_panel({
                "inst": tile.objects[0],
                "gx": gx,
                "gy": gy
            })
            return

        idx = tile.objects.index(self.selected_instance["inst"])
        idx = (idx + 1) % len(tile.objects)

        self.load_instance_into_panel({
            "inst": tile.objects[idx],
            "gx": gx,
            "gy": gy
        })

    def load_instance_into_panel(self, picked):
        print("SELECTED OBJECT =", picked)
        if not picked:
            return

        self.selected_instance = picked

        inst = picked["inst"]

        self.obj_offx.set(inst["offx"])
        self.obj_offy.set(inst["offy"])
        self.obj_offz.set(inst["offz"])
        self.obj_rot_x.set(inst["rot_x"])
        self.obj_rot_y.set(inst["rot_y"])
        self.obj_rot_z.set(inst["rot_z"])

    def delete_selected_instance(self):
        if not self.selected_instance["inst"]:
            return

        for row in self.grid:
            for t in row:
                if self.selected_instance["inst"] in t.objects:
                    t.objects.remove(self.selected_instance["inst"])
                    self.selected_instance["inst"] = None
                    self.draw_grid()
                    return

    def refresh_asset_list(self):
        self.asset_list.delete(0,'end')
        for k in self.assets.keys():
            self.asset_list.insert('end',k)
    
    def draw_texture_preview(self, texture_name):
        path=os.path.join(TEXTURE_FOLDER, texture_name)
        if not os.path.exists(path):
            return

        img=Image.open(path).convert("RGBA")
        img=img.resize((128,128), Image.NEAREST)

        tk_img=ImageTk.PhotoImage(img)
        self.texture_preview_ref=tk_img

        self.texture_canvas.delete("all")
        self.texture_canvas.create_image(64,64,image=tk_img)
        self.texture_name_label.config(text=texture_name)

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
                self.selected_texture=tex_name
                self.update_texture_selection()
                self.draw_texture_preview(tex_name)

            btn.bind("<Button-1>", on_click)

        if texture_names and not self.selected_texture:
            self.selected_texture=texture_names[0]
            self.draw_texture_preview(texture_names[0])

        self.update_texture_selection()

    def select_asset(self,e):
        s=self.asset_listbox.curselection()
        if s:
            self.selected_asset=self.asset_listbox.get(s[0])

    def hover_3d(self,e):
        self.viewport.hover_tile=self.viewport.get_exact_tile(e.x,e.y)

    def paint_3d(self,e):
        pos=self.viewport.get_exact_tile(e.x,e.y)
        if pos:
            self.apply_tool(*pos)

    def start_rotate(self,e):
        self.viewport.last_x=e.x; self.viewport.last_y=e.y

    def viewport_mouse_press(self, event):
        self.viewport.last_mouse_x = event.x
        self.viewport.last_mouse_y = event.y

        picked = self.viewport.pick_object_under_mouse(event.x, event.y)

        if picked:
            self.load_instance_into_panel(picked)

        if self.viewport.is_click_near_gizmo(event.x, event.y):
            self.viewport.dragging_gizmo = True

            if event.state & 0x0001:
                self.viewport.drag_mode = "z"
            else:
                self.viewport.drag_mode = "xy"
        else:
            self.viewport.dragging_gizmo = False
            self.start_rotate(event)

    def viewport_mouse_release(self, event):
        self.viewport.dragging_gizmo = False
        self.viewport.drag_mode = None

    def viewport_mouse_drag(self, event):
        if self.viewport.dragging_gizmo:
            self.viewport.on_mouse_drag(event)
        elif self.viewport.space_held:
            self.rotate_camera(event)

    def rotate_camera(self,e):
        dx=e.x-self.viewport.last_x
        dy=e.y-self.viewport.last_y
        self.viewport.cam_rot_y+=dx*0.5
        self.viewport.cam_rot_x+=dy*0.3
        self.viewport.last_x=e.x
        self.viewport.last_y=e.y

    def start_pan(self,e):
        self.viewport.last_x=e.x; self.viewport.last_y=e.y

    def is_click_near_gizmo(self, mx, my):
        if not hasattr(self, 'toolkit_ref'):
            return False

        tool = self.toolkit_ref

        if not tool.selected_instance:
            return False

        sel = tool.selected_instance

        if "gx" not in sel or "gy" not in sel:
            return False

        inst = sel["inst"]

        gx = sel["gx"] + inst["offx"] + 0.5
        gz = sel["gy"] + inst["offy"] + 0.5

        screen_x = (gx - gz) * 32 + (self.winfo_width() // 2)
        screen_y = (gx + gz) * 16 + 120

        dx = mx - screen_x
        dy = my - screen_y

        return abs(dx) < 170 and abs(dy) < 170

    def on_mouse_press(self, event):
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        self.manipulating_object = False
        self.dragging_gizmo = False

        picked = self.viewport.pick_object_under_mouse(event.x, event.y)

        if picked:
            # SIEMPRE seleccionar primero
            self.load_instance_into_panel(picked)

            # luego evaluar gizmo
            if self.is_click_near_gizmo(event.x, event.y):
                self.dragging_gizmo = True
                self.manipulating_object = True

                self.drag_mode = "z" if (event.state & 0x0001) else "xy"
                print("PICKED:", picked)
                print("SELECTED:", self.selected_instance)

            return

    def pan_camera(self,e):
        dx=e.x-self.viewport.last_x
        dy=e.y-self.viewport.last_y
        self.viewport.pan_x-=dx*0.03
        self.viewport.pan_z+=dy*0.03
        self.viewport.last_x=e.x
        self.viewport.last_y=e.y

    def zoom_camera(self,e):
        self.viewport.cam_dist=max(6,self.viewport.cam_dist-(1 if e.delta>0 else -1))

    def set_tool(self,t):
        self.selected_tool=t

    def apply_tool(self,gx,gy):
        t = self.grid[gy][gx]

        if self.selected_tool == 'floorpaint':
            if self.texture_assign_mode.get() == 'floor':
                t.floor_tex = self.selected_texture
            t.floor_height = float(self.current_floor_height.get())

        elif self.selected_tool == 'wall_n':
            t.wall_n = not t.wall_n
            if self.texture_assign_mode.get() == 'wall':
                t.wall_tex = self.selected_texture
            t.wall_n_height = float(self.current_wall_height.get())

        elif self.selected_tool == 'wall_s':
            t.wall_s = not t.wall_s
            if self.texture_assign_mode.get() == 'wall':
                t.wall_tex = self.selected_texture
            t.wall_s_height = float(self.current_wall_height.get())

        elif self.selected_tool == 'wall_e':
            t.wall_e = not t.wall_e
            if self.texture_assign_mode.get() == 'wall':
                t.wall_tex = self.selected_texture
            t.wall_e_height = float(self.current_wall_height.get())

        elif self.selected_tool == 'wall_w':
            t.wall_w = not t.wall_w
            if self.texture_assign_mode.get() == 'wall':
                t.wall_tex = self.selected_texture
            t.wall_w_height = float(self.current_wall_height.get())
        
        elif self.selected_tool == 'wall_ne':
            t.wall_ne = not t.wall_ne
            if self.texture_assign_mode.get() == 'wall':
                t.wall_tex = self.selected_texture
            t.wall_ne_height = float(self.current_wall_height.get())

        elif self.selected_tool == 'wall_se':
            t.wall_se = not t.wall_se
            if self.texture_assign_mode.get() == 'wall':
                t.wall_tex = self.selected_texture
            t.wall_se_height = float(self.current_wall_height.get())

        elif self.selected_tool == 'wall_nw':
            t.wall_nw = not t.wall_nw
            if self.texture_assign_mode.get() == 'wall':
                t.wall_tex = self.selected_texture
            t.wall_nw_height = float(self.current_wall_height.get())

        elif self.selected_tool == 'wall_sw':
            t.wall_sw = not t.wall_sw
            if self.texture_assign_mode.get() == 'wall':
                t.wall_tex = self.selected_texture
            t.wall_ws_height = float(self.current_wall_height.get())

        elif self.selected_tool == 'placeobj' and self.selected_asset:
            inst = {
                "asset": self.selected_asset,
                "offx": 0.0,
                "offy": 0.0,
                "offz": 0.0,
                "rot_x": 0,
                "rot_y": 0,
                "rot_z": 0
            }
            t.objects.append(inst)

            self.load_instance_into_panel({
                "inst": inst,
                "gx": gx,
                "gy": gy
            })

        elif self.selected_tool == 'selectobj':
            self.cycle_select_object_at_tile(gx, gy, t)

        elif self.selected_tool == 'prefab_start':
            self.prefab_start = (gx, gy)

        elif self.selected_tool == 'prefab_end':
            self.prefab_end = (gx, gy)
            self.copy_prefab_region()

        elif self.selected_tool == 'prefab_paste':
            self.paste_prefab_region(gx, gy)

        self.draw_grid()

    def paint_2d(self,e):
        gx=e.x//CELL_PIXELS
        gy=e.y//CELL_PIXELS
        if 0<=gx<GRID_W and 0<=gy<GRID_H:
            self.apply_tool(gx,gy)

    def save_project(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Project","*.json")]
        )
        if not path:
            return

        data = {
            "grid": [[t.__dict__ for t in row] for row in self.grid],
            "assets": {}
        }

        for name, a in self.assets.items():
            data["assets"][name] = {
            "cubes": a.cubes,
            "tex_top": a.tex_top,
            "tex_side": a.tex_side,
            "mode": a.mode,
            "mesh_vertices": a.mesh_vertices,
            "mesh_faces": a.mesh_faces,
            "mesh_uvs": a.mesh_uvs,
            "mesh_tex": a.mesh_tex,
            "mesh_texcoords": a.mesh_texcoords,
            "mesh_face_uvs": a.mesh_face_uvs,
            "mesh_face_materials": a.mesh_face_materials,
            "mesh_material_textures": a.mesh_material_textures,
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=4)

        messagebox.showinfo("Save", "Project saved.")
        
    def load_project(self):
        path = filedialog.askopenfilename(filetypes=[("JSON Project","*.json")])
        if not path:
            return

        with open(path,"r") as f:
            data = json.load(f)

        for y,row in enumerate(data["grid"]):
            for x,td in enumerate(row):
                t = Tile()
                t.__dict__.update(td)

                if not hasattr(t, "objects"):
                    t.objects = []

                self.grid[y][x] = t

        self.assets = {}

        self.asset_listbox.delete(0, tk.END)

        for name,ad in data["assets"].items():
            a = LowPolyAsset(name)
            a.cubes = ad.get("cubes", [])
            a.tex_top = ad.get("tex_top")
            a.tex_side = ad.get("tex_side")

            a.mode = ad.get("mode", "voxel")
            a.mesh_vertices = ad.get("mesh_vertices", [])
            a.mesh_faces = ad.get("mesh_faces", [])
            a.mesh_uvs = ad.get("mesh_uvs", [])
            a.mesh_tex = ad.get("mesh_tex")
            a.mesh_texcoords = ad.get("mesh_texcoords", [])
            a.mesh_face_uvs = ad.get("mesh_face_uvs", [])
            a.mesh_face_materials = ad.get("mesh_face_materials", [])
            a.mesh_material_textures = ad.get("mesh_material_textures", {})

            self.assets[name] = a
            self.asset_listbox.insert(tk.END, name)

        self.draw_grid()
        messagebox.showinfo("Load","Project loaded.")

    def build_merged_floors(self):
        visited = [[False for _ in range(GRID_W)] for _ in range(GRID_H)]
        merged = []

        for y in range(GRID_H):
            for x in range(GRID_W):
                if visited[y][x]:
                    continue

                t = self.grid[y][x]

                if not t.floor_tex:
                    continue

                tex = t.floor_tex
                h = t.floor_height

                width = 1
                while x + width < GRID_W:
                    nt = self.grid[y][x + width]
                    if visited[y][x + width]:
                        break
                    if nt.floor_tex != tex or abs(nt.floor_height - h) > 0.001:
                        break
                    width += 1

                height = 1
                can_expand = True

                while y + height < GRID_H and can_expand:
                    for xx in range(x, x + width):
                        nt = self.grid[y + height][xx]
                        if visited[y + height][xx]:
                            can_expand = False
                            break
                        if nt.floor_tex != tex or abs(nt.floor_height - h) > 0.001:
                            can_expand = False
                            break
                    if can_expand:
                        height += 1

                for yy in range(y, y + height):
                    for xx in range(x, x + width):
                        visited[yy][xx] = True

                merged.append((x, y, width, height, tex, h))

        return merged
    
    def build_merged_walls(self):
        walls = []

        # NORTH/SOUTH horizontal strips
        for side in ['n','s']:
            visited = [[False for _ in range(GRID_W)] for _ in range(GRID_H)]

            for y in range(GRID_H):
                for x in range(GRID_W):
                    if visited[y][x]:
                        continue

                    t = self.grid[y][x]
                    active = getattr(t, f'wall_{side}')
                    h = getattr(t, f'wall_{side}_height')

                    if not active:
                        continue

                    tex = t.wall_tex
                    fh = t.floor_height

                    width = 1
                    while x + width < GRID_W:
                        nt = self.grid[y][x + width]
                        if visited[y][x + width]:
                            break
                        if not getattr(nt, f'wall_{side}'):
                            break
                        if nt.wall_tex != tex:
                            break
                        if abs(getattr(nt, f'wall_{side}_height') - h) > 0.001:
                            break
                        if abs(nt.floor_height - fh) > 0.001:
                            break
                        width += 1

                    for xx in range(x, x + width):
                        visited[y][xx] = True

                    walls.append((side, x, y, width, tex, fh, h))

        # EAST/WEST vertical strips
        for side in ['e','w']:
            visited = [[False for _ in range(GRID_W)] for _ in range(GRID_H)]

            for y in range(GRID_H):
                for x in range(GRID_W):
                    if visited[y][x]:
                        continue

                    t = self.grid[y][x]
                    active = getattr(t, f'wall_{side}')
                    h = getattr(t, f'wall_{side}_height')

                    if not active:
                        continue

                    tex = t.wall_tex
                    fh = t.floor_height

                    heightrun = 1
                    while y + heightrun < GRID_H:
                        nt = self.grid[y + heightrun][x]
                        if visited[y + heightrun][x]:
                            break
                        if not getattr(nt, f'wall_{side}'):
                            break
                        if nt.wall_tex != tex:
                            break
                        if abs(getattr(nt, f'wall_{side}_height') - h) > 0.001:
                            break
                        if abs(nt.floor_height - fh) > 0.001:
                            break
                        heightrun += 1

                    for yy in range(y, y + heightrun):
                        visited[yy][x] = True

                    walls.append((side, x, y, heightrun, tex, fh, h))

        return walls
    
    def build_visible_asset_faces(self, asset, tile_x, tile_y, floor_h):
        faces = []
        cubeset = set(tuple(c) for c in asset.cubes)
        s = 0.2

        directions = [
            ((1,0,0), 'xp'),
            ((-1,0,0), 'xn'),
            ((0,1,0), 'yp'),
            ((0,-1,0), 'yn'),
            ((0,0,1), 'zp'),
            ((0,0,-1), 'zn')
        ]

        for vx,vy,vz in cubeset:
            bx = tile_x + vx * s
            by = floor_h + vz * s
            bz = tile_y + vy * s

            for (dx,dy,dz), faceid in directions:
                neighbor = (vx+dx, vy+dy, vz+dz)

                if neighbor in cubeset:
                    continue

                if faceid == 'xp':
                    quad = [
                        (bx+s,by,bz),
                        (bx+s,by,bz+s),
                        (bx+s,by+s,bz+s),
                        (bx+s,by+s,bz)
                    ]

                elif faceid == 'xn':
                    quad = [
                        (bx,by,bz),
                        (bx,by+s,bz),
                        (bx,by+s,bz+s),
                        (bx,by,bz+s)
                    ]

                elif faceid == 'yp':
                    quad = [
                        (bx,by,bz+s),
                        (bx+s,by,bz+s),
                        (bx+s,by+s,bz+s),
                        (bx,by+s,bz+s)
                    ]

                elif faceid == 'yn':
                    quad = [
                        (bx,by,bz),
                        (bx,by+s,bz),
                        (bx+s,by+s,bz),
                        (bx+s,by,bz)
                    ]

                elif faceid == 'zp':
                    quad = [
                        (bx,by+s,bz),
                        (bx+s,by+s,bz),
                        (bx+s,by+s,bz+s),
                        (bx,by+s,bz+s)
                    ]

                elif faceid == 'zn':
                    quad = [
                        (bx,by,bz),
                        (bx+s,by,bz),
                        (bx+s,by,bz+s),
                        (bx,by,bz+s)
                    ]

                faces.append(quad)

        return faces

    def export_dreamcast(self):
        export_path = filedialog.askdirectory(title="Seleccionar carpeta de exportacion Dreamcast")
        if not export_path:
            return

        tex_folder = os.path.join(export_path, "textures")

        if not os.path.exists(tex_folder):
            os.makedirs(tex_folder)

        used_textures = set()

        # recolectar texturas usadas
        for row in self.grid:
            for t in row:
                if t.floor_tex:
                    used_textures.add(t.floor_tex)
                if t.wall_tex:
                    used_textures.add(t.wall_tex)

        for a in self.assets.values():
            if a.tex_top:
                used_textures.add(a.tex_top)
            if a.tex_side:
                used_textures.add(a.tex_side)

        # copiar texturas
        for tex in used_textures:
            src = os.path.join(TEXTURE_FOLDER, tex)
            dst = os.path.join(tex_folder, tex)

            if os.path.exists(src):
                try:
                    img = Image.open(src)
                    img.save(dst)
                except:
                    pass

        # manifest
        with open(os.path.join(export_path, 'textures_manifest.txt'), 'w') as f:
            for tex in used_textures:
                f.write(tex + '\n')

        # json backup map
        with open(os.path.join(export_path, 'map.json'), 'w') as f:
            json.dump([[t.__dict__ for t in row] for row in self.grid], f, indent=4)

        # json assets
        with open(os.path.join(export_path, 'assets.json'), 'w') as f:
            json.dump({
                k:{
                    'cubes':a.cubes,
                    'tex_top':a.tex_top,
                    'tex_side':a.tex_side
                } for k,a in self.assets.items()
            }, f, indent=4)

        # generar geometry c
            geo_lines = []
            geo_lines.append("// AUTO GENERATED DREAMCAST GEOMETRY")
            geo_lines.append("typedef struct { float x,y,z,u,v; } DCVTX;")
            geo_lines.append("DCVTX scene_quads[] = {")

            # ===========================
            # MERGED FLOORS
            # ===========================
            merged_floors = self.build_merged_floors()

            for x,y,w,h,tex,fh in merged_floors:
                geo_lines.append(
                    f"{{{x},{fh},{y},0,0}},{{{x+w},{fh},{y},1,0}},{{{x+w},{fh},{y+h},1,1}},{{{x},{fh},{y+h},0,1}},"
                )

            # ===========================
            # MERGED WALLS
            # ===========================
            merged_walls = self.build_merged_walls()

            for side,x,y,run,tex,fh,wh in merged_walls:
                top = fh + wh

                if side == 'n':
                    geo_lines.append(
                        f"{{{x},{fh},{y},0,0}},{{{x+run},{fh},{y},1,0}},{{{x+run},{top},{y},1,1}},{{{x},{top},{y},0,1}},"
                    )

                elif side == 's':
                    geo_lines.append(
                        f"{{{x},{fh},{y+1},0,0}},{{{x+run},{fh},{y+1},1,0}},{{{x+run},{top},{y+1},1,1}},{{{x},{top},{y+1},0,1}},"
                    )

                elif side == 'e':
                    geo_lines.append(
                        f"{{{x+1},{fh},{y},0,0}},{{{x+1},{fh},{y+run},1,0}},{{{x+1},{top},{y+run},1,1}},{{{x+1},{top},{y},0,1}},"
                    )

                elif side == 'w':
                    geo_lines.append(
                        f"{{{x},{fh},{y},0,0}},{{{x},{fh},{y+run},1,0}},{{{x},{top},{y+run},1,1}},{{{x},{top},{y},0,1}},"
                    )

            # ===========================
            # ASSETS OPTIMIZED VISIBLE FACES ONLY
            # ===========================
            for y in range(GRID_H):
                for x in range(GRID_W):
                    t = self.grid[y][x]

                    if not t.objects:
                        continue

                    for inst in t.objects:
                        asset_name = inst["asset"]

                        if asset_name not in self.assets:
                            continue

                        asset = self.assets[asset_name]

                        if asset.mode == "mesh":
                            for face in asset.mesh_faces:
                                pts = []

                                for idx in face[:4]:
                                    vx,vy,vz = asset.mesh_vertices[idx]
                                    
                                    lx, ly, lz = rotate_3d(
                                        vx, vy, vz,
                                        inst["rot_x"],
                                        inst["rot_y"],
                                        inst["rot_z"]
                                    )

                                    wx = x + inst["offx"] + lx
                                    wy = t.floor_height + inst["offz"] + ly
                                    wz = y + inst["offy"] + lz

                                    pts.append((wx,wy,wz))

                                if len(pts) == 3:
                                    pts.append(pts[2])

                                p1,p2,p3,p4 = pts

                                geo_lines.append(
                                    f"{{{p1[0]},{p1[1]},{p1[2]},0,0}},"
                                    f"{{{p2[0]},{p2[1]},{p2[2]},1,0}},"
                                    f"{{{p3[0]},{p3[1]},{p3[2]},1,1}},"
                                    f"{{{p4[0]},{p4[1]},{p4[2]},0,1}},"
                                )

                            continue

                        visible_faces = self.build_visible_asset_faces(asset, 0, 0, 0)

                        for quad in visible_faces:
                            transformed = []

                            for px,py,pz in quad:
                                lx = px
                                lz = pz

                                rot = inst["rot"]

                                if rot == 90:
                                    lx, lz = -lz, lx
                                elif rot == 180:
                                    lx, lz = -lx, -lz
                                elif rot == 270:
                                    lx, lz = lz, -lx

                                wx = x + inst["offx"] + lx
                                wy = t.floor_height + inst["offz"] + py
                                wz = y + inst["offy"] + lz

                                transformed.append((wx,wy,wz))

                            p1,p2,p3,p4 = transformed

                            geo_lines.append(
                                f"{{{p1[0]},{p1[1]},{p1[2]},0,0}},"
                                f"{{{p2[0]},{p2[1]},{p2[2]},1,0}},"
                                f"{{{p3[0]},{p3[1]},{p3[2]},1,1}},"
                                f"{{{p4[0]},{p4[1]},{p4[2]},0,1}},"
                            )

            geo_lines.append("};")

        with open(os.path.join(export_path, 'scene_geometry.c'), 'w') as f:
            f.write("\n".join(geo_lines))

        # stub loader
        with open(os.path.join(export_path, 'pvr_loader_stub.c'), 'w') as f:
            f.write("""// PVR Loader Stub for KOS
    // convert textures manually to .pvr using texconv

    void load_all_textures(){
        // TODO load pvr textures here
    }
    """)

        print("Export Dreamcast completado en:", export_path)

    def draw_grid(self):
        self.grid_canvas.delete('all')
        for y in range(GRID_H):
            for x in range(GRID_W):
                px=x*CELL_PIXELS
                py=y*CELL_PIXELS
                t=self.grid[y][x]
                base = 60 + int((t.floor_height + 2) * 25)
                base = max(30, min(180, base))

                if t.floor_tex:
                    c = f'#{base:02x}{base:02x}{base:02x}'
                else:
                    c = f'#{base//2:02x}{base//2:02x}{base//2:02x}'
                self.grid_canvas.create_rectangle(px,py,px+CELL_PIXELS,py+CELL_PIXELS,fill=c,outline='#202020')

                if t.objects:
                    self.grid_canvas.create_oval(
                        px+10, py+10,
                        px+CELL_PIXELS-10, py+CELL_PIXELS-10,
                        outline='cyan',
                        width=2
                    )

                    if self.selected_instance["inst"] and self.selected_instance["inst"] in t.objects:
                        self.grid_canvas.create_rectangle(
                            px+4, py+4,
                            px+CELL_PIXELS-4, py+CELL_PIXELS-4,
                            outline='yellow',
                            width=3
                        )

                    self.grid_canvas.create_text(
                        px+CELL_PIXELS//2,
                        py+CELL_PIXELS//2,
                        text=str(len(t.objects)),
                        fill='cyan',
                        font=('Arial',8,'bold')
                    )
                if abs(t.floor_height) > 0.01:
                    self.grid_canvas.create_text(
                        px + CELL_PIXELS//2,
                        py + CELL_PIXELS//2,
                        text=str(round(t.floor_height,1)),
                        fill='white',
                        font=('Arial',7)
    )
                if t.objects:
                    self.grid_canvas.create_oval(px+8,py+8,px+20,py+20,fill='cyan')
                if t.wall_n:self.grid_canvas.create_line(px,py,px+CELL_PIXELS,py,fill='red',width=2)
                if t.wall_s:self.grid_canvas.create_line(px,py+CELL_PIXELS,px+CELL_PIXELS,py+CELL_PIXELS,fill='red',width=2)
                if t.wall_e:self.grid_canvas.create_line(px+CELL_PIXELS,py,px+CELL_PIXELS,py+CELL_PIXELS,fill='red',width=2)
                if t.wall_w:self.grid_canvas.create_line(px,py,px,py+CELL_PIXELS,fill='red',width=2)
                if getattr(t, "wall_ne", False):
                    self.grid_canvas.create_line(
                        px, py,
                        px+CELL_PIXELS, py+CELL_PIXELS,
                        fill='orange', width=2
                    )

                if getattr(t, "wall_nw", False):
                    self.grid_canvas.create_line(
                        px+CELL_PIXELS, py,
                        px, py+CELL_PIXELS,
                        fill='orange', width=2
                    )

                if getattr(t, "wall_se", False):
                    self.grid_canvas.create_line(
                        px+CELL_PIXELS, py,
                        px, py+CELL_PIXELS,
                        fill='yellow', width=2
                    )

                if getattr(t, "wall_sw", False):
                    self.grid_canvas.create_line(
                        px, py,
                        px+CELL_PIXELS, py+CELL_PIXELS,
                        fill='yellow', width=2
                    )

if __name__=='__main__':
    root=tk.Tk()
    app=Toolkit(root)
    root.mainloop()
from pyopengltk import OpenGLFrame
from OpenGL.GL import *
from OpenGL.GLU import *
from PIL import Image, ImageTk
import os




GRID_W = 24
GRID_H = 24
CELL_PIXELS = 28

ASSET_GRID = 16
ASSET_CELL = 20

base_path = os.path.dirname(__file__)
tex_path = os.path.join(base_path, "textures")
TEXTURE_FOLDER = tex_path
EXPORT_FOLDER = base_path + "/export_dc"


class TextureManager:
    def __init__(self):
        self.floor_textures = []
        self.wall_textures = []
        self.previews = {}
        self.gl_textures = {}
        self.gl_textures = {}
        self.texture_alpha = {}
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
                    img = Image.open(path).convert("RGBA")

                    # -----------------------------------------
                    # SI ES AUTOTILE MOSTRAR CELDA CENTRAL
                    # -----------------------------------------
                    if "_auto" in f.lower():
                        tw = img.width // 4
                        th = img.height // 6

                        idx = 18   # tile central sólido
                        cx = (idx % 4) * tw
                        cy = (idx // 4) * th

                        img = img.crop((cx, cy, cx+tw, cy+th))

                    img = img.resize((32,32))
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

    def is_alpha_texture(self, name):
        return self.texture_alpha.get(name, False)
    

    def load_gl_texture(self, name):
        if name in self.gl_textures:
            return self.gl_textures[name]

        if os.path.exists(name):
            path = name
            
        else:
            path = os.path.join(TEXTURE_FOLDER, name)

        if not os.path.exists(path):
            print("TEXTURE NOT FOUND:", path)
            return None

        img = Image.open(path).convert("RGBA")

        

        alpha = img.getchannel("A")
        has_alpha = alpha.getextrema()[0] < 255
        self.texture_alpha[name] = has_alpha

        img = img.transpose(Image.FLIP_TOP_BOTTOM)

        # ============================================
        # FIX HALO NEGRO EN PIXELS TRANSPARENTES
        # copia RGB de vecinos a pixels alpha=0
        # ============================================
        px = img.load()
        w, h = img.size

        for y in range(h):
            for x in range(w):
                r,g,b,a = px[x,y]

                if a == 0:
                    found = False

                    for oy in (-1,0,1):
                        for ox in (-1,0,1):
                            nx = x + ox
                            ny = y + oy

                            if nx < 0 or ny < 0 or nx >= w or ny >= h:
                                continue

                            rr,gg,bb,aa = px[nx,ny]

                            if aa > 0:
                                px[x,y] = (rr,gg,bb,0)
                                found = True
                                break
                        if found:
                            break

        data = img.tobytes()

        texid = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texid)

        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        

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
        return texid


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
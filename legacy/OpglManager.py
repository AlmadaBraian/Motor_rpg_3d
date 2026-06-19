import time
from pyopengltk import OpenGLFrame
from OpenGL.GL import *
from OpenGL.GLU import *
from PIL import Image, ImageTk
import os
import math

from ActorInstance import ActorInstance
from CameraAnimator import CameraAnimator
import HUDManager
from SpriteInstance import SpriteInstance
from TextureManager import TextureManager
from EventManager import *

import config


GRID_W = config.GRID_W
GRID_H = config.GRID_H
CELL_PIXELS = config.CELL_PIXELS
ASSET_GRID = config.ASSET_GRID
ASSET_CELL = config.ASSET_CELL

base_path = config.base_path
tex_path = config.tex_path
TEXTURE_FOLDER = tex_path
EXPORT_FOLDER = base_path + "/export_dc"

import tkinter as tk
from pyopengltk import OpenGLFrame
from OpenGL.GL import *
from OpenGL.GLU import *
from PIL import Image, ImageTk
import math
import os
from SpriteManager import *
from Camera import Camera


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


class GLViewport(OpenGLFrame):

    def __init__(self, master, **kw):
        super().__init__(master, **kw)

        #self.editor = editor

        # -------- atributos python seguros --------
        self.manipulating_object = False
        self.space_held = True

        self.last_anim_time = time.time()

        self.local_texture_manager = TextureManager()
        

        self.dragging_gizmo = False
        self.drag_mode = None
        self.last_mouse_x = 0
        self.last_mouse_y = 0

        self.editor_camera = Camera()
        self.game_camera = Camera()

        self.camera = self.editor_camera
        self.active_camera_mode = "editor"

        # setup inicial game camera
        self.game_camera.x = 5
        self.game_camera.y = 1
        self.game_camera.z = 5
        self.game_camera.yaw = 180
        self.game_camera.pitch = -10
        self.game_camera.distance = 6


        self.preview_paused = False

        self.last_x = 0
        self.last_y = 0

        self.hover_tile = None
        self.animate = 1
        
    def initgl(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        glDisable(GL_CULL_FACE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glClearColor(0.08, 0.08, 0.1, 1)

    def get_active_camera(self):
        return self.camera


    def get_camera_world_pos(self):
        cam = self.camera   # o self.toolkit_ref.viewport.camera según dónde estés

        rx = math.radians(cam.pitch)
        ry = math.radians(cam.yaw)

        cx = cam.x + math.sin(ry) * math.cos(rx) * cam.distance
        cy = cam.y + math.sin(rx) * cam.distance
        cz = cam.z + math.cos(ry) * math.cos(rx) * cam.distance

        return (cx, cy, cz)
    
    def toggle_camera_mode(self):
        if self.active_camera_mode == "editor":
            self.active_camera_mode = "game"
            self.camera = self.game_camera
            print("VIEWPORT NOW USING GAME CAMERA")
        else:
            self.active_camera_mode = "editor"
            self.camera = self.editor_camera
            print("VIEWPORT NOW USING EDITOR CAMERA")

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
                grid = tool.get_active_grid()
                t = grid[y][x]

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

        now = time.time()
        dt = now - self.last_anim_time
        self.last_anim_time = now

        # =====================================================
        # 1. animaciones de cámara cinematicas
        # =====================================================
        if hasattr(self.toolkit_ref.game_view, "game_cam_anim"):

            if self.toolkit_ref.game_view.game_cam_anim:

                self.toolkit_ref.game_view.game_cam_anim.update(dt)

        # =====================================================
        # 2. update runtime actor / movimiento / cambio de clips
        # =====================================================
        if hasattr(self, "toolkit_ref"):
            if hasattr(self.toolkit_ref.runtime_actor, "update_runtime_actor"):
                self.toolkit_ref.runtime_actor.update_runtime_actor(dt)
                HUDManager.update_runtime_hud(self)

        # =====================================================
        # 3. cámara sigue actor DESPUES del movimiento
        # =====================================================
        if self.toolkit_ref.play_mode:

            if not self.toolkit_ref.battle_mode:

                if hasattr(self.toolkit_ref, "runtime_world"):
                    
                    print(
                        "FOLLOW:",
                        self.toolkit_ref.world_event_running,
                        self.toolkit_ref.actor_to_follow
                    )

                    if self.toolkit_ref.actor_to_follow:

                        pack = self.toolkit_ref.actor_to_follow

                    else:

                        pack = self.toolkit_ref.runtime_world.main_actor

                    if self.toolkit_ref.runtime_world:

                        if not self.toolkit_ref.runtime_camera_locked:

                            self.follow_runtime_camera()

        # =====================================================
        # 4. construir matrices con cámara ya actualizada
        # =====================================================
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, max(1, self.width) / max(1, self.height), 0.1, 1000)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        radx = math.radians(self.camera.pitch)
        rady = math.radians(self.camera.yaw)

        camx = self.camera.x + math.sin(rady) * math.cos(radx) * self.camera.distance
        camy = self.camera.y + math.sin(radx) * self.camera.distance
        camz = self.camera.z + math.cos(rady) * math.cos(radx) * self.camera.distance

        gluLookAt(
            camx, camy, camz,
            self.camera.x, self.camera.y, self.camera.z,
            0, 1, 0
        )

        # =====================================================
        # 5. update animadores comunes
        # =====================================================
        if hasattr(self, "toolkit_ref"):

            if hasattr(self.toolkit_ref, "update_animators"):
                self.toolkit_ref.update_animators(dt)

            if hasattr(self.toolkit_ref, "play_mode"):
                if self.toolkit_ref.play_mode and self is self.toolkit_ref.viewport:
                    return

            self.draw_world(self.toolkit_ref)

##        self.debug_draw_autotile_sheet("esquinasAgua_Auto.png")

        glFlush()

    

    def follow_runtime_camera(self):
        tool = self.toolkit_ref

        print(
            "FOLLOW:",
            tool.world_event_running,
            tool.actor_to_follow
        )

        if not hasattr(tool, "runtime_world"):
            return

        if tool.runtime_world is None:
            return

        if not tool.runtime_world.main_actor:
            return
        
        if tool.actor_to_follow:

            pack = tool.actor_to_follow

        else:

            pack = tool.runtime_world.main_actor

            if not pack:
                return

        inst = pack["inst"]

        px = pack["gx"] + inst.offx + 0.5
        py = pack["gy"] + inst.offy + 0.5

        target_x = px
        target_z = py
        target_y = inst.offz + 0.8

        self.game_camera.yaw = tool.runtime_cam_orbit
        self.game_camera.pitch = 35
        self.game_camera.distance = 7

        # ==========================================
        # CATCHUP SUAVE DESPUES DEL MANTLE
        # ==========================================
        if getattr(tool, "runtime_camera_catchup", False):
            speed = 0.08

            self.game_camera.x += (target_x - self.game_camera.x) * speed
            self.game_camera.y += (target_y - self.game_camera.y) * speed
            self.game_camera.z += (target_z - self.game_camera.z) * speed

            dx = abs(target_x - self.game_camera.x)
            dy = abs(target_y - self.game_camera.y)
            dz = abs(target_z - self.game_camera.z)

            if dx < 0.05 and dy < 0.05 and dz < 0.05:
                tool.runtime_camera_catchup = False

        else:
            # seguimiento normal caminando
            speed = 0.35

            self.game_camera.x += (target_x - self.game_camera.x) * speed
            self.game_camera.y += (target_y - self.game_camera.y) * speed
            self.game_camera.z += (target_z - self.game_camera.z) * speed

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


##NUEVO, PARA COPIAR############
################################
    def textured_quad_auto_tile(self, p1, p2, p3, p4, texid, uv1, uv2, uv3, uv4):
            if texid is not None:
                glEnable(GL_TEXTURE_2D)
                glBindTexture(GL_TEXTURE_2D, texid)
                glColor3f(1, 1, 1)

            glBegin(GL_QUADS)
            glTexCoord2f(uv1[0], uv1[1]); glVertex3f(p1[0], p1[1], p1[2]) # Sup-Izq
            glTexCoord2f(uv2[0], uv2[1]); glVertex3f(p2[0], p2[1], p2[2]) # Sup-Der
            glTexCoord2f(uv3[0], uv3[1]); glVertex3f(p3[0], p3[1], p3[2]) # Inf-Der
            glTexCoord2f(uv4[0], uv4[1]); glVertex3f(p4[0], p4[1], p4[2]) # Inf-Izq
            glEnd()
########################################################################################
########################################################################################
    def textured_quad_custom_uv(self, p1, p2, p3, p4, texid, u0, v0, u1, v1):
        if texid is not None:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, texid)
            glColor3f(1,1,1)
        else:
            glDisable(GL_TEXTURE_2D)
            glColor3f(1,1,1)

        glBegin(GL_QUADS)

        glTexCoord2f(u0, v0); glVertex3f(*p1)
        glTexCoord2f(u1, v0); glVertex3f(*p2)
        glTexCoord2f(u1, v1); glVertex3f(*p3)
        glTexCoord2f(u0, v1); glVertex3f(*p4)

        glEnd()

        glBindTexture(GL_TEXTURE_2D, 0)
        

        
    def cube(self, x, y, z, s=1, h=0.05, toptex=None, sidetex=None, uv_mode="tile"):
    
        if uv_mode == "tile":
            ru = s
            rv = s
            side_ru = s
            side_rv = h
        else:
            ru = rv = 1
            side_ru = side_rv = 1

        # bottom
        self.textured_quad((x,z,y),(x+s,z,y),(x+s,z,y+s),(x,z,y+s), sidetex, ru, rv)

        # top
        self.textured_quad((x,z+h,y),(x+s,z+h,y),(x+s,z+h,y+s),(x,z+h,y+s), toptex, ru, rv)

        # north
        self.textured_quad((x,z,y),(x+s,z,y),(x+s,z+h,y),(x,z+h,y), sidetex, side_ru, side_rv)

        # east
        self.textured_quad((x+s,z,y),(x+s,z,y+s),(x+s,z+h,y+s),(x+s,z+h,y), sidetex, side_ru, side_rv)

        # west
        self.textured_quad((x,z,y+s),(x,z,y),(x,z+h,y),(x,z+h,y+s), sidetex, side_ru, side_rv)

        # south
        self.textured_quad((x+s,z,y+s),(x,z,y+s),(x,z+h,y+s),(x+s,z+h,y+s), sidetex, side_ru, side_rv)

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
    
    def update(self, dt):
        for spr in self.all_sprites:
            spr.animator.update(dt)

    
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


    def draw_sprite_instance(self, sprite, inst, wx, wy, wz, cam):

        if not hasattr(inst, "animator"):
            return

        anim = inst.animator
        if anim is None:
            return

        if anim.current is None:
            return

        if anim.current not in anim.clips:
            return

        clip = anim.clips[anim.current]

        if not clip.frames:
            return

        if anim.frame >= len(clip.frames):
            anim.frame = 0

        raw = clip.frames[anim.frame]

        # =====================================================
        # COMPATIBILIDAD VIEJO/NUEVO FORMATO
        # =====================================================

        if isinstance(raw, dict):
            frame_index = raw.get("frame", 0)

            crop_x = raw.get("crop_x", 0)
            crop_y = raw.get("crop_y", 0)
            crop_w = raw.get("crop_w", sprite.frame_w)
            crop_h = raw.get("crop_h", sprite.frame_h)

            custom_fw = raw.get("w", crop_w)
            custom_fh = raw.get("h", crop_h)

            offset_x = raw.get("ox", 0)
            offset_y = raw.get("oy", 0)
            flip_x = raw.get("flip_x", False)
            rot = raw.get("rot", 0)
        else:
            frame_index = raw

            crop_x = 0
            crop_y = 0
            crop_w = sprite.frame_w
            crop_h = sprite.frame_h

            custom_fw = sprite.frame_w
            custom_fh = sprite.frame_h

            offset_x = 0
            offset_y = 0
            flip_x = False
            rot = 0

        cols = max(1, sprite.sheet_cols)
        rows = max(1, sprite.sheet_rows)

        fw = sprite.frame_w
        fh = sprite.frame_h

        fx = frame_index % cols
        fy = frame_index // cols
        fy = (rows - 1) - fy

        tex_w = fw * cols
        tex_h = fh * rows

        px0 = fx * fw + crop_x
        px1 = fx * fw + crop_x + crop_w

        py0 = fy * fh + crop_y
        py1 = fy * fh + crop_y + crop_h

        u0 = px0 / tex_w
        u1 = px1 / tex_w

        v0 = py0 / tex_h
        v1 = py1 / tex_h

        if flip_x:
            u0, u1 = u1, u0

        full_img_path = self.get_asset_full_path(sprite.image_path)

        texid = self.local_texture_manager.load_gl_texture(full_img_path)
        glBindTexture(GL_TEXTURE_2D, texid)
        

        # =====================================================
        # ESCALA CUSTOM POR FRAME
        # =====================================================

        size_w = sprite.width * (custom_fw / sprite.frame_w)
        size_h = sprite.height * (custom_fh / sprite.frame_h)

        half_w = size_w * 0.5

        # offsets convertidos a unidades mundo
        world_ox = (offset_x / sprite.frame_w) * sprite.width
        world_oy = (offset_y / sprite.frame_h) * sprite.height

        crop_center_shift_x = ((crop_x + crop_w * 0.5) - (sprite.frame_w * 0.5)) / sprite.frame_w
        crop_bottom_shift_y = ((sprite.frame_h) - (crop_y + crop_h)) / sprite.frame_h

        world_ox += crop_center_shift_x * sprite.width
        world_oy += crop_bottom_shift_y * sprite.height

        cx, cy, cz = cam

        to_cam_x = cx - wx
        to_cam_z = cz - wz

        length = math.sqrt(to_cam_x * to_cam_x + to_cam_z * to_cam_z)
        if length == 0:
            length = 1.0

        to_cam_x /= length
        to_cam_z /= length

        right_x = to_cam_z * half_w
        right_z = -to_cam_x * half_w

        wx += right_x * 0 + world_ox * to_cam_z
        wz += right_z * 0 - world_ox * to_cam_x
        wy += world_oy

        verts = [
            [-half_w, 0],
            [ half_w, 0],
            [ half_w, size_h],
            [-half_w, size_h]
        ]

        if rot != 0:
            ang = math.radians(rot)
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)

            cx2 = 0
            cy2 = size_h * 0.5

            for v in verts:
                lx = v[0] - cx2
                ly = v[1] - cy2

                rx = lx * cos_a - ly * sin_a
                ry = lx * sin_a + ly * cos_a

                v[0] = rx + cx2
                v[1] = ry + cy2

        glBegin(GL_QUADS)

        glTexCoord2f(u0, v0); glVertex3f(wx + to_cam_z*verts[0][0], wy + verts[0][1], wz - to_cam_x*verts[0][0])
        glTexCoord2f(u1, v0); glVertex3f(wx + to_cam_z*verts[1][0], wy + verts[1][1], wz - to_cam_x*verts[1][0])
        glTexCoord2f(u1, v1); glVertex3f(wx + to_cam_z*verts[2][0], wy + verts[2][1], wz - to_cam_x*verts[2][0])
        glTexCoord2f(u0, v1); glVertex3f(wx + to_cam_z*verts[3][0], wy + verts[3][1], wz - to_cam_x*verts[3][0])

        glEnd()

    def get_asset_full_path(self, rel_path):
        if not rel_path:
            return None

        rel_path = rel_path.lstrip("/\\")
        return os.path.normpath(os.path.join(base_path, rel_path))

    def draw_actor_instance(self, sprite, inst, wx, wy, wz, cam):

        if inst.animator is None:
            return

        anim = inst.animator

        if anim.current is None:
            return

        if anim.current not in anim.clips:
            return

        clip = anim.clips[anim.current]

        if not clip.frames:
            return

        if anim.frame >= len(clip.frames):
            anim.frame = 0

        raw = clip.frames[anim.frame]

        if isinstance(raw, dict):
            frame_index = raw.get("frame", 0)

            crop_x = raw.get("crop_x", 0)
            crop_y = raw.get("crop_y", 0)
            crop_w = raw.get("crop_w", sprite.frame_w)
            crop_h = raw.get("crop_h", sprite.frame_h)

            custom_fw = raw.get("w", crop_w)
            custom_fh = raw.get("h", crop_h)

            offset_x = raw.get("ox", 0)
            offset_y = raw.get("oy", 0)

            flip_x = raw.get("flip_x", False)
            rot = raw.get("rot", 0)
        else:
            frame_index = raw

            crop_x = 0
            crop_y = 0
            crop_w = sprite.frame_w
            crop_h = sprite.frame_h

            custom_fw = sprite.frame_w
            custom_fh = sprite.frame_h

            offset_x = 0
            offset_y = 0

            flip_x = False
            rot = 0

        cols = max(1, sprite.sheet_cols)
        rows = max(1, sprite.sheet_rows)

        fw = sprite.frame_w
        fh = sprite.frame_h

        fx = frame_index % cols
        fy = frame_index // cols
        fy = (rows - 1) - fy

        tex_w = fw * cols
        tex_h = fh * rows

        px0 = fx * fw + crop_x
        px1 = fx * fw + crop_x + crop_w

        py0 = fy * fh + crop_y
        py1 = fy * fh + crop_y + crop_h

        u0 = px0 / tex_w
        u1 = px1 / tex_w

        v0 = py0 / tex_h
        v1 = py1 / tex_h

        if flip_x:
            u0, u1 = u1, u0

        texid = self.local_texture_manager.load_gl_texture(sprite.image_path)
        if texid is None:
            return

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texid)

        size_w = sprite.width * (custom_fw / sprite.frame_w)
        size_h = sprite.height * (custom_fh / sprite.frame_h)

        half_w = size_w * 0.5

        world_ox = (offset_x / sprite.frame_w) * sprite.width
        world_oy = (offset_y / sprite.frame_h) * sprite.height

        crop_center_shift_x = ((crop_x + crop_w * 0.5) - (sprite.frame_w * 0.5)) / sprite.frame_w
        crop_bottom_shift_y = ((sprite.frame_h) - (crop_y + crop_h)) / sprite.frame_h

        world_ox += crop_center_shift_x * sprite.width
        world_oy += crop_bottom_shift_y * sprite.height

        cx, cy, cz = cam

        to_cam_x = cx - wx
        to_cam_z = cz - wz

        length = math.sqrt(to_cam_x * to_cam_x + to_cam_z * to_cam_z)
        if length == 0:
            length = 1.0

        to_cam_x /= length
        to_cam_z /= length

        wx += world_ox * to_cam_z
        wz -= world_ox * to_cam_x
        wy += world_oy

        verts = [
            [-half_w, 0],
            [ half_w, 0],
            [ half_w, size_h],
            [-half_w, size_h]
        ]

        if rot != 0:
            ang = math.radians(rot)
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)

            cx2 = 0
            cy2 = size_h * 0.5

            for v in verts:
                lx = v[0] - cx2
                ly = v[1] - cy2

                rx = lx * cos_a - ly * sin_a
                ry = lx * sin_a + ly * cos_a

                v[0] = rx + cx2
                v[1] = ry + cy2

        glBegin(GL_QUADS)

        glTexCoord2f(u0, v0); glVertex3f(wx + to_cam_z*verts[0][0], wy + verts[0][1], wz - to_cam_x*verts[0][0])
        glTexCoord2f(u1, v0); glVertex3f(wx + to_cam_z*verts[1][0], wy + verts[1][1], wz - to_cam_x*verts[1][0])
        glTexCoord2f(u1, v1); glVertex3f(wx + to_cam_z*verts[2][0], wy + verts[2][1], wz - to_cam_x*verts[2][0])
        glTexCoord2f(u0, v1); glVertex3f(wx + to_cam_z*verts[3][0], wy + verts[3][1], wz - to_cam_x*verts[3][0])

        glEnd()
    
    
    def render_sprites(self, tool):
        cam = self.get_camera_world_pos()

        for y in range(GRID_H):
            for x in range(GRID_W):
                grid = tool.get_active_grid()
                t = grid[y][x]

                if not hasattr(t, "sprites"):
                    continue

                for inst in t.sprites:
                    if inst.asset not in tool.sprites:
                        continue

                    sprite = tool.sprites[inst.asset]

                    wx = x + inst.offx + 0.5
                    wy = t.floor_height + inst.offz
                    wz = y + inst.offy + 0.5

                    inst.animator.update(0.016)

                    self.draw_sprite_instance(sprite, inst, wx, wy, wz, cam)

    
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

        glBindTexture(GL_TEXTURE_2D, tex)
        glBegin(GL_TRIANGLES)

        # NE wall (vertical split)
        if getattr(t, "wall_ne", False):
            hgt = t.wall_ne_height
            h = fh + hgt
            vrep = hgt if t.wall_uv_mode == "tile" else 1
            urep = 1.41 if t.wall_uv_mode == "tile" else 1

            A = (x,   fh, y)
            B = (x+1, fh, y+1)
            C = (x+1, h,  y+1)
            D = (x,   h,  y)

            glTexCoord2f(0,0); glVertex3f(*A)
            glTexCoord2f(urep,0); glVertex3f(*B)
            glTexCoord2f(urep,vrep); glVertex3f(*C)

            glTexCoord2f(0,0); glVertex3f(*A)
            glTexCoord2f(urep,vrep); glVertex3f(*C)
            glTexCoord2f(0,vrep); glVertex3f(*D)

         # NW wall (vertical split)
        if getattr(t, "wall_nw", False):
            hgt = t.wall_nw_height
            h = fh + hgt
            vrep = hgt if t.wall_uv_mode == "tile" else 1
            urep = 1.41 if t.wall_uv_mode == "tile" else 1

            A = (x+1, fh, y)
            B = (x,   fh, y+1)
            C = (x,   h,  y+1)
            D = (x+1, h,  y)
            # tri 1
            glTexCoord2f(0,0); glVertex3f(*A)
            glTexCoord2f(urep,0); glVertex3f(*B)
            glTexCoord2f(urep,vrep); glVertex3f(*C)

            # tri 2
            glTexCoord2f(0,0); glVertex3f(*A)
            glTexCoord2f(urep,vrep); glVertex3f(*C)
            glTexCoord2f(0,vrep); glVertex3f(*D)

        if getattr(t, "wall_se", False):

            hgt = t.wall_se_height
            h = fh + hgt
            vrep = hgt if t.wall_uv_mode == "tile" else 1
            urep = 1.41 if t.wall_uv_mode == "tile" else 1

            A = (x+1, fh, y)
            B = (x,   fh, y+1)
            C = (x,   h,  y+1)
            D = (x+1, h,  y)

            # tri 1 (invertido en Y visual)
            glTexCoord2f(0,0); glVertex3f(*D)
            glTexCoord2f(urep,0); glVertex3f(*C)
            glTexCoord2f(urep,vrep); glVertex3f(*B)

            # tri 2
            glTexCoord2f(0,0); glVertex3f(*D)
            glTexCoord2f(urep,vrep); glVertex3f(*B)
            glTexCoord2f(0,vrep); glVertex3f(*A)

        if getattr(t, "wall_sw", False):

            hgt = t.wall_sw_height
            h = fh + hgt
            vrep = hgt if t.wall_uv_mode == "tile" else 1
            urep = 1.41 if t.wall_uv_mode == "tile" else 1

            A = (x,   fh, y)
            B = (x+1, fh, y+1)
            C = (x+1, h,  y+1)
            D = (x,   h,  y)

            # tri 1
            glTexCoord2f(0,0); glVertex3f(*B)
            glTexCoord2f(urep,0); glVertex3f(*A)
            glTexCoord2f(urep,vrep); glVertex3f(*D)

            # tri 2
            glTexCoord2f(0,0); glVertex3f(*B)
            glTexCoord2f(urep,vrep); glVertex3f(*D)
            glTexCoord2f(0,vrep); glVertex3f(*C)

        glEnd()

    def draw_segmented_wall_n(self, x, y, t, tm):
        base = t.floor_height

        for seg in t.wall_n_segments:
            h0 = base
            h1 = base + seg["h"]

            texid = tm.load_gl_texture(seg["tex"]) if seg["tex"] else None

            rv = seg["h"] if seg.get("uv","tile") == "tile" else 1

            self.textured_quad(
                (x,h0,y),
                (x+1,h0,y),
                (x+1,h1,y),
                (x,h1,y),
                texid,
                1,
                rv
            )

            base = h1

    def use_segments(self, segs, fallback_height, fallback_tex):
        if segs and len(segs) > 0:
            return True
        return False


    def draw_runtime_actor_tile_highlight(self, tool):
        if not hasattr(tool, "runtime_world"):
            return

        if not tool.runtime_world:
            return

        if not tool.runtime_world.main_actor:
            return

        pack = tool.runtime_world.main_actor

        gx = pack["gx"]
        gy = pack["gy"]

        grid = tool.runtime_world.grid
        fh = grid[gy][gx].floor_height

        glDisable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glColor4f(0.2, 0.8, 1.0, 0.22)

        self.draw_quad(
            (gx,   fh+0.02, gy),
            (gx+1, fh+0.02, gy),
            (gx+1, fh+0.02, gy+1),
            (gx,   fh+0.02, gy+1)
        )

        glDisable(GL_BLEND)
        glEnable(GL_TEXTURE_2D)
        glColor3f(1,1,1)

    def draw_blob_shadow(self, wx, wy, wz, size=0.30):
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glColor4f(0, 0, 0, 0.30)

        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(wx, wy + 0.015, wz)

        steps = 20
        for i in range(steps + 1):
            ang = math.radians((360 / steps) * i)
            px = wx + math.cos(ang) * size
            pz = wz + math.sin(ang) * size
            glVertex3f(px, wy + 0.015, pz)

        glEnd()

        glDisable(GL_BLEND)
        glEnable(GL_TEXTURE_2D)
        glColor3f(1,1,1)


    
    def render_tiles(self, tool):
        tm = self.local_texture_manager

        merged_floors = tool.build_merged_floors()
        grid = tool.get_active_grid()

        # PISOS NORMALES
        for x,y,w,h,tex,fh in merged_floors:
            texid = tm.load_gl_texture(tex) if tex else None

            t = grid[y][x]
            ru = w if t.floor_uv_mode=="tile" else 1
            rv = h if t.floor_uv_mode=="tile" else 1

            self.textured_quad(
                (x,fh,y),
                (x+w,fh,y),
                (x+w,fh,y+h),
                (x,fh,y+h),
                texid,
                ru,
                rv
            )

        # AUTOTILES
        for y in range(GRID_H):
            for x in range(GRID_W):
                t = grid[y][x]
                

                if t.floor_tex and "_auto" in t.floor_tex.lower():
                    self.draw_auto_floor_tile(x, y, t, tm)

                if getattr(t, "is_block", False):
                    self.draw_solid_block(x, y, t, grid, tm)
     
                self.draw_tile_walls(x,y,t,tm)



##NUEVO, PARA COPIAR############
################################
                
    def is_autotile_texture(self, texname):
        return "auto" in texname.lower()

#################### PAREDES NORMALES Y CON AUTO-TILE
    def draw_tile_walls(self, x, y, t, tm):
        directions = ['n', 's', 'e', 'w']

        for side in directions:

            if getattr(t, f"wall_{side}"):
                segments = t.wall_segments.get(side, [])
                if not segments:
                    h_simple = getattr(t, f"wall_{side}_height", 1.0)
                    segments = [{"h": h_simple, "tex": t.wall_tex}]
                
                base = t.floor_height
                for i, seg in enumerate(segments):
                    h0 = base
                    h1 = base + seg.get("h", 1.0)
                    texname = seg.get("tex")
                    if not texname: continue
                    
                    texid = tm.load_gl_texture(texname)
                    mid_h = (h0 + h1) / 2.0
                    q = 0.5
                    rv = seg.get("h", 1.0) if seg.get("uv","tile") == "tile" else 1
           
                    ### PAREDES CON AUTO-TILE
                    if self.is_autotile_texture(texname):

                            
                            
                            U = 1 if (i + 1 < len(segments) and segments[i+1].get("tex") == texname) else 0
                            D = 1 if (i - 1 >= 0 and segments[i-1].get("tex") == texname) else 0
                            
                            if side == 'n':   L, R = self.toolkit_ref.check_neighbor_segment(x-1, y, 'n', h0,h1, texname), self.toolkit_ref.check_neighbor_segment(x+1, y, 'n', h0,h1, texname)
                            elif side == 's': L, R = self.toolkit_ref.check_neighbor_segment(x+1, y, 's', h0,h1, texname), self.toolkit_ref.check_neighbor_segment(x-1, y, 's', h0,h1, texname)
                            elif side == 'w': L, R = self.toolkit_ref.check_neighbor_segment(x, y-1, 'w', h0,h1, texname), self.toolkit_ref.check_neighbor_segment(x, y+1, 'w', h0,h1, texname)
                            elif side == 'e': L, R = self.toolkit_ref.check_neighbor_segment(x, y+1, 'e', h0,h1, texname), self.toolkit_ref.check_neighbor_segment(x, y-1, 'e', h0,h1, texname)

                            LU = self.toolkit_ref.check_neighbor_segment(x-1, y, 'n', h1, h1 + 0.1, texname) if L else 0
                            RU = self.toolkit_ref.check_neighbor_segment(x+1, y, 'n', h1, h1 + 0.1, texname) if R else 0
                            LD = self.toolkit_ref.check_neighbor_segment(x-1, y, 'n', h0 - 0.1, h0, texname) if L else 0
                            RD = self.toolkit_ref.check_neighbor_segment(x+1, y, 'n', h0 - 0.1, h0, texname) if R else 0
                            
                            idxs = self.toolkit_ref.calculate_autotile_bits(L, R, U, D, LU, RU, LD, RD)


                            if side == 'n':
                                sub_quads = [
                                    ((x,   h1,    y), (x+q, h1,    y), (x+q, mid_h, y), (x,   mid_h, y)), # NW
                                    ((x+q, h1,    y), (x+1, h1,    y), (x+1, mid_h, y), (x+q, mid_h, y)), # NE
                                    ((x,   mid_h, y), (x+q, mid_h, y), (x+q, h0,    y), (x,   h0,    y)), # SW
                                    ((x+q, mid_h, y), (x+1, mid_h, y), (x+1, h0,    y), (x+q, h0,    y))  # SE (Orden arreglado)
                                ]
                            elif side == 's':
                                sub_quads = [
                                    ((x+q, h1,    y+1), (x+1, h1,    y+1), (x+1, mid_h, y+1), (x+q, mid_h, y+1)), # NW
                                    ((x,   h1,    y+1), (x+q, h1,    y+1), (x+q, mid_h, y+1), (x,   mid_h, y+1)), # NE
                                    ((x+q, mid_h, y+1), (x+1, mid_h, y+1), (x+1, h0,    y+1), (x+q, h0,    y+1)), # SW
                                    ((x,   mid_h, y+1), (x+q, mid_h, y+1), (x+q, h0,    y+1), (x,   h0,    y+1))  # SE
                                ]

                            elif side == 'w': # Eje Z
                                sub_quads = [
                                    ((x, h1, y), (x, h1, y+q), (x, mid_h, y+q), (x, mid_h, y)), # NW
                                    ((x, h1, y+q), (x, h1, y+1), (x, mid_h, y+1), (x, mid_h, y+q)), # NE
                                    ((x, mid_h, y), (x, mid_h, y+q), (x, h0, y+q), (x, h0, y)), # SW
                                    ((x, mid_h, y+q), (x, mid_h, y+1), (x, h0, y+1), (x, h0, y+q)) # SE
                                ]
                            elif side == 'e': # Eje Z
                                sub_quads = [
                                    ((x+1, h1, y+q), (x+1, h1, y+1), (x+1, mid_h, y+1), (x+1, mid_h, y+q)), # NW
                                    ((x+1, h1, y), (x+1, h1, y+q), (x+1, mid_h, y+q), (x+1, mid_h, y)), # NE
                                    ((x+1, mid_h, y+q), (x+1, mid_h, y+1), (x+1, h0, y+1), (x+1, h0, y+q)), # SW
                                    ((x+1, mid_h, y), (x+1, mid_h, y+q), (x+1, h0, y+q), (x+1, h0, y)) # SE
                                ]

                            for j, idx in enumerate(idxs):
                                u0, u1, v0, v1 = self.toolkit_ref.get_uvs_from_idx(idx)
                                p1, p2, p3, p4 = sub_quads[j]
                                
                                if side in ['s', 'e']:
                                    uvs = [(u1,v1), (u0,v1), (u0,v0), (u1,v0)]
                                else:
                                    uvs = [(u0,v1), (u1,v1), (u1,v0), (u0,v0)]
                                
                                self.textured_quad_auto_tile(p1, p2, p3, p4, texid, *uvs)

                            base = h1
                            
                    ### PAREDES NORMALES
                    else:
                        ## CON ALPHA
                        is_alpha = tm.is_alpha_texture(seg["tex"]) if seg["tex"] else False
                        if is_alpha:
                                if side == 'n': self.alpha_wall_queue.append(("n", x, y, h0, h1, texid, rv))
                                elif side == 's': self.alpha_wall_queue.append(("s", x, y, h0, h1, texid, rv))
                                elif side == 'w': self.alpha_wall_queue.append(("w", x, y, h0, h1, texid, rv))
                                elif side == 'e': self.alpha_wall_queue.append(("e", x, y, h0, h1, texid, rv))
                                base = h1


                        ## SIN ALPHA          
                        else:


                            if side == 'n':
                                    self.textured_quad(
                                    (x,h0,y),
                                    (x+1,h0,y),
                                    (x+1,h1,y),
                                    (x,h1,y),
                                    texid,
                                    1,
                                    rv
                                )

                            if side == 'e':
                                    self.textured_quad(
                                    (x+1,h0,y),
                                    (x+1,h0,y+1),
                                    (x+1,h1,y+1),
                                    (x+1,h1,y),
                                    texid,
                                    1,
                                    rv
                                )

                            if side == 'w':
                                    self.textured_quad(
                                    (x,h0,y),
                                    (x,h0,y+1),
                                    (x,h1,y+1),
                                    (x,h1,y),
                                    texid,
                                    1,
                                    rv
                                )
                                

                            if side == 's':
                                    self.textured_quad(
                                    (x,h0,y+1),
                                    (x+1,h0,y+1),
                                    (x+1,h1,y+1),
                                    (x,h1,y+1),
                                    texid,
                                    1,
                                    rv
                                )

                            base = h1


        self.draw_diag_wall(x, y, t, tm)

##############################################################
##############################################################
        
    def draw_auto_floor_tile(self, x, y, t, tm):
        texid = tm.load_gl_texture(t.floor_tex)
        if texid is None:
            return

        idxs = self.toolkit_ref.get_autotile_indices(x, y, t.floor_tex)


        cols = 4  # 64 / 16
        rows = 6  # 96 / 16
        
        q = 0.5 # Si el tile total mide 1.0, cada sub-tile mide 0.5
        fh = t.floor_height

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texid)
        glColor3f(1,1,1)

 

        quads = [
                    (x,     y,     x+q,   y+q),   # NW
                    (x+q,   y,     x+1,   y+q),   # NE
                    (x,     y+q,   x+q,   y+1),   # SW
                    (x+q,   y+q,   x+1,   y+1)    # SE
                ]



        for i, idx in enumerate(idxs):
                tx = idx % cols
                ty = idx // cols

                # 2. Convertimos a UV (0.0 a 1.0)
                u0 = tx / float(cols)
                u1 = (tx + 1) / float(cols)

                # 3. Invertimos el eje V para OpenGL (Fila 0 arriba)
                v0 = 1.0 - ((ty + 1) / float(rows)) # Borde inferior del sub-tile
                v1 = 1.0 - (ty / float(rows))  

                x1, z1, x2, z2 = quads[i]

                glBegin(GL_QUADS)

                # ESTE ORDEN ES EL IMPORTANTE
                glTexCoord2f(u0, v1); glVertex3f(x1, fh, z1)
                glTexCoord2f(u1, v1); glVertex3f(x2, fh, z1)
                glTexCoord2f(u1, v0); glVertex3f(x2, fh, z2)
                glTexCoord2f(u0, v0); glVertex3f(x1, fh, z2)

                glEnd()

        glBindTexture(GL_TEXTURE_2D, 0)

    def draw_solid_block(self, x, y, t, grid, tm):
        side_tex = tm.load_gl_texture(t.block_side_tex) if t.block_side_tex else None
        top_tex = tm.load_gl_texture(t.block_top_tex) if t.block_top_tex else None

        b = t.block_bottom
        h = t.block_top

        if t.block_uv_mode == "tile":
            top_ru = 1
            top_rv = 1
            side_ru = 1
            side_rv = h - b
        else:
            top_ru = top_rv = 1
            side_ru = side_rv = 1

        # ==========================
        # TOP FACE
        # ==========================
        self.textured_quad(
            (x,   h, y),
            (x+1, h, y),
            (x+1, h, y+1),
            (x,   h, y+1),
            top_tex,
            top_ru,
            top_rv
        )

        # helper vecino bloque
        def is_neighbor_block(nx, ny):
            if nx < 0 or ny < 0 or nx >= GRID_W or ny >= GRID_H:
                return False

            nt = grid[ny][nx]

            if not getattr(nt, "is_block", False):
                return False

            # si vecino llega al menos a la misma altura, oculta cara
            return nt.block_top >= h and nt.block_bottom <= b

        # ==========================
        # NORTH
        # ==========================
        if not is_neighbor_block(x, y-1):
            self.textured_quad(
                (x,   b, y),
                (x+1, b, y),
                (x+1, h, y),
                (x,   h, y),
                side_tex,
                side_ru,
                side_rv
            )

        # ==========================
        # SOUTH
        # ==========================
        if not is_neighbor_block(x, y+1):
            self.textured_quad(
                (x+1, b, y+1),
                (x,   b, y+1),
                (x,   h, y+1),
                (x+1, h, y+1),
                side_tex,
                side_ru,
                side_rv
            )

        # ==========================
        # WEST
        # ==========================
        if not is_neighbor_block(x-1, y):
            self.textured_quad(
                (x, b, y+1),
                (x, b, y),
                (x, h, y),
                (x, h, y+1),
                side_tex,
                side_ru,
                side_rv
            )

        # ==========================
        # EAST
        # ==========================
        if not is_neighbor_block(x+1, y):
            self.textured_quad(
                (x+1, b, y),
                (x+1, b, y+1),
                (x+1, h, y+1),
                (x+1, h, y),
                side_tex,
                side_ru,
                side_rv
            )

    def debug_draw_autotile_sheet(self, texname):
        texid = self.local_texture_manager.load_gl_texture(texname)
        if texid is None:
            return

        cols = 4
        rows = 6

        startx = -6
        startz = -6

        for idx in range(24):
            tx = idx % cols
            ty = idx // cols

            u0 = tx / cols
            u1 = (tx+1) / cols
            v0 = 1.0 - ((ty+1)/rows)
            v1 = 1.0 - (ty/rows)

            x = startx + (idx % 4)
            z = startz + (idx // 4)

            self.textured_quad_custom_uv(
                (x,0,z),
                (x+1,0,z),
                (x+1,0,z+1),
                (x,0,z+1),
                texid,u0,v0,u1,v1
            )

##            print("DEBUG IDX", idx, "row", ty, "col", tx)

    def draw_runtime_player(self, p):
        glDisable(GL_TEXTURE_2D)

        x = p.x
        y = p.y
        z = p.z

        s = 0.25
        h = 1.0

        glBegin(GL_QUADS)

        # frente
        glVertex3f(x-s, y, z-s)
        glVertex3f(x+s, y, z-s)
        glVertex3f(x+s, y+h, z-s)
        glVertex3f(x-s, y+h, z-s)

        # atrás
        glVertex3f(x+s, y, z+s)
        glVertex3f(x-s, y, z+s)
        glVertex3f(x-s, y+h, z+s)
        glVertex3f(x+s, y+h, z+s)

        # izquierda
        glVertex3f(x-s, y, z+s)
        glVertex3f(x-s, y, z-s)
        glVertex3f(x-s, y+h, z-s)
        glVertex3f(x-s, y+h, z+s)

        # derecha
        glVertex3f(x+s, y, z-s)
        glVertex3f(x+s, y, z+s)
        glVertex3f(x+s, y+h, z+s)
        glVertex3f(x+s, y+h, z-s)

        glEnd()

        glEnable(GL_TEXTURE_2D)

    def render_actors(self, tool):
        grid = tool.get_active_grid()
        cam = self.get_camera_world_pos()

        for y in range(GRID_H):
            for x in range(GRID_W):
                t = grid[y][x]

                if not hasattr(t, "actors"):
                    continue

                for pack in t.actors:
                    inst = pack["inst"]
                    if inst.actor_name not in tool.actors:
                        continue

                    actor_def = tool.actors[inst.actor_name]

                    if not actor_def.sprite_sheets:
                        continue

                    sprname = actor_def.sprite_sheets[0]

                    if sprname not in tool.sprites:
                        continue

                    sprite = tool.sprites[actor_def.sprite_sheets[0]]

                    wx = x + inst.offx + 0.5
                    wy = t.floor_height + inst.offz
                    wz = y + inst.offy + 0.5

                    self.draw_actor_instance(sprite, inst, wx, wy, wz, cam)

    def render_alpha_pass(self, tool):
        cam = self.get_camera_world_pos()
        alpha_queue = []

        grid = tool.get_active_grid()

        # ============================
        # ALPHA WALLS
        # ============================
        for side, x, y, h0, h1, texid, rv in self.alpha_wall_queue:

            wx = x + 0.5
            wy = (h0 + h1) * 0.5
            wz = y + 0.5

            dist = (wx-cam[0])**2 + (wy-cam[1])**2 + (wz-cam[2])**2

            alpha_queue.append(("wall", dist, side, x, y, h0, h1, texid, rv))

        # ============================
        # SPRITES + ACTORS
        # ============================
        for y in range(GRID_H):
            for x in range(GRID_W):
                t = grid[y][x]
                

                if hasattr(t, "sprites"):
                    for inst in t.sprites:
                        if inst.asset not in tool.sprites:
                            continue

                        sprite = tool.sprites[inst.asset]

                        wx = x + inst.offx + 0.5
                        wy = t.floor_height + inst.offz
                        wz = y + inst.offy + 0.5

                        dist = (wx-cam[0])**2 + (wy-cam[1])**2 + (wz-cam[2])**2
                        alpha_queue.append(("sprite", dist, sprite, inst, wx, wy, wz))

                if hasattr(t, "actors"):
                    for pack in t.actors:
                        inst = pack["inst"]

                        if inst.actor_name not in tool.actors:
                            continue

                        actor_def = tool.actors[inst.actor_name]

                        if not actor_def.sprite_sheets:
                            continue

                        sprname = actor_def.sprite_sheets[0]

                        if sprname not in tool.sprites:
                            continue

                        sprite = tool.sprites[actor_def.sprite_sheets[0]]

                        wx = pack["gx"] + inst.offx + 0.5
                        wy = grid[pack["gy"]][pack["gx"]].floor_height + inst.offz
                        wz = pack["gy"] + inst.offy + 0.5

                        dist = (wx-cam[0])**2 + (wy-cam[1])**2 + (wz-cam[2])**2
                        alpha_queue.append(("actor", dist, sprite, inst, wx, wy, wz))

        # ============================
        # SORT BACK TO FRONT
        # ============================
        alpha_queue.sort(key=lambda q: q[1], reverse=True)

        for item in alpha_queue:
            kind = item[0]

            if kind == "wall":
                _, dist, side, x, y, h0, h1, texid, rv = item

                if side == "n":
                    self.textured_quad((x,h0,y),(x+1,h0,y),(x+1,h1,y),(x,h1,y),texid,1,rv)

                elif side == "s":
                    self.textured_quad((x,h0,y+1),(x+1,h0,y+1),(x+1,h1,y+1),(x,h1,y+1),texid,1,rv)

                elif side == "e":
                    self.textured_quad((x+1,h0,y),(x+1,h0,y+1),(x+1,h1,y+1),(x+1,h1,y),texid,1,rv)

                elif side == "w":
                    self.textured_quad((x,h0,y),(x,h0,y+1),(x,h1,y+1),(x,h1,y),texid,1,rv)

            elif kind == "sprite":
                _, dist, sprite, inst, wx, wy, wz = item

                if inst.animator:
                    inst.animator.update(0.016)

                self.draw_sprite_instance(sprite, inst, wx, wy, wz, cam)

            elif kind == "actor":
                _, dist, sprite, inst, wx, wy, wz = item

                if inst.animator:
                    inst.animator.update(0.016)

                #dibujo de sombra y actor

                ground_y = grid[pack["gy"]][pack["gx"]].floor_height
                self.draw_blob_shadow(wx, ground_y, wz, 0.28)

                self.draw_actor_instance(sprite, inst, wx, wy, wz, cam)

    def draw_dialog_hud(self, tool):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_TEXTURE_2D)

        # caja dialogo
        glColor4f(0, 0, 0, 0.7)

        x1 = 40
        y1 = self.height - 180
        x2 = self.width - 40
        y2 = self.height - 40

        glBegin(GL_QUADS)
        glVertex2f(x1,y1)
        glVertex2f(x2,y1)
        glVertex2f(x2,y2)
        glVertex2f(x1,y2)
        glEnd()

        glEnable(GL_DEPTH_TEST)

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    def draw_event_markers(self, tool):
        grid = tool.get_active_grid()

        glDisable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        for y in range(GRID_H):
            for x in range(GRID_W):
                t = grid[y][x]

                if not getattr(t, "event_data", {}).get("enabled", False):
                    continue

                mode = t.event_data.get("trigger", "step")

                if mode == "step":
                    glColor4f(0,1,1,0.30)      # cyan
                elif mode == "action":
                    glColor4f(1,0.6,0,0.30)    # orange
                elif mode == "autorun":
                    glColor4f(1,0,0,0.30)      # red
                elif mode == "proximity":
                    glColor4f(0.7,0,1,0.30)    # purple
                else:
                    glColor4f(1,1,1,0.25)

                h = t.floor_height + 0.03

                self.draw_quad(
                    (x,h,y),
                    (x+1,h,y),
                    (x+1,h,y+1),
                    (x,h,y+1)
                )

        glDisable(GL_BLEND)
        glEnable(GL_TEXTURE_2D)
        glColor3f(1,1,1)

    def draw_world(self, tool):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        glColor3f(1,1,1)

        # ======================================
        # PASS 1 - GEOMETRIA SOLIDA
        # ======================================
        glDisable(GL_BLEND)
        glDepthMask(GL_TRUE)

        self.alpha_wall_queue = []

        self.render_tiles(tool)
        #if is_combat:
            #self.draw_runtime_actor_tile_highlight(tool)

        self.render_meshes(tool)

        # ======================================
        # PASS 2 - ALPHA SORTED
        # ======================================

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glEnable(GL_ALPHA_TEST)
        glAlphaFunc(GL_GREATER, 0.05)

        glDepthMask(GL_FALSE)

        self.render_alpha_pass(tool)

        glDepthMask(GL_TRUE)
        glDisable(GL_ALPHA_TEST)

        glDepthMask(GL_TRUE)

        # runtime player opcional
        if hasattr(tool, "player"):
            self.draw_runtime_player(tool.player)

        # ======================================
        # HOVER TILE
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

        self.draw_event_markers(tool)

        # gizmo
        if tool.selected_instance:
            inst = tool.selected_instance
            if "gx" in inst and "gy" in inst:
                fh = tool.grid[inst["gy"]][inst["gx"]].floor_height
                self.draw_transform_gizmo(inst, fh)

        if hasattr(tool, "dialog_visible"):
            if tool.dialog_visible:
                self.draw_dialog_hud(tool)

        

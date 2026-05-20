import tkinter as tk
from tkinter import filedialog
from tkinter import simpledialog
import pygame
import threading
import json
import struct
import math
import os

# ---------------- CONFIG ----------------
GRID_W, GRID_H = 30, 30
TILE_SIZE = 32

VIEW_W = 640
VIEW_H = 480

FOV = math.pi / 3
NUM_RAYS = 80
MAX_DEPTH = 600

# ------------ TILE DEFINICIÓN ----------
TILE_TYPES = {
    0: {"name": "vacío", "color": (30,30,30), "height": 0, "segments": []},
    1: {"name": "pared", "color": (200,0,0), "height": 4, "segments": []},
    2: {"name": "piso", "color": (0,200,0), "height": 0, "segments": []},
    3: {"name": "caja", "color": (0,0,200), "height": 1, "segments": []},
    4: {"name": "puerta", "color": (0,0,200), "height": 4, "segments": []},
}
selected_tile = {"x": None, "y": None}
segment_listbox = None
library_listbox = None
segment_library = {}
current_segments = []
current_segments_listbox = None

ui_needs_refresh = False

# ------------ EDITOR STATE -------------
class Editor:
    def __init__(self):
        self.grid = [[{"id":0, "h":0, "segments": []} for _ in range(GRID_W)] for _ in range(GRID_H)]
        self.selected = 1
        self.running = True
        self.current_height = 2

        # cámara preview
        self.cam_x = 3.5
        self.cam_y = 3.5
        self.cam_angle = 0
        self.cam_height = 1   # 👈 NUEVO (offset vertical)
        self.pitch = 0
        self.texture_files = {}

editor = Editor()

# ------------ PYGAME -------------------
def load_texture_list():
    base_path = os.path.dirname(__file__)
    tex_path = os.path.join(base_path, "textures")

    textures = {}

    if not os.path.exists(tex_path):
        print("No existe carpeta textures")
        return textures

    for i, filename in enumerate(os.listdir(tex_path)):
        if filename.lower().endswith((".png", ".jpg", ".bmp")):
            textures[i] = filename

    return textures

def cast_rays(screen, textures):
    start_angle = editor.cam_angle - FOV / 2
    proj_plane = (VIEW_W / 2) / math.tan(FOV / 2)
    col_width = VIEW_W // NUM_RAYS

    camera_z = editor.cam_height * TILE_SIZE
    #zbuffer = [float("inf")] * NUM_RAYS

    for ray in range(NUM_RAYS):
        angle = start_angle + ray * (FOV / NUM_RAYS)
        sin_a = math.sin(angle)
        cos_a = math.cos(angle)

        visible_segments = [(0, VIEW_H)]

        for depth in range(1, MAX_DEPTH):
            x = editor.cam_x + cos_a * depth * 0.02
            y = editor.cam_y + sin_a * depth * 0.02

            if not (0 <= int(x) < GRID_W and 0 <= int(y) < GRID_H):
                continue

            tile = editor.grid[int(y)][int(x)]
            segments = tile.get("segments", [])

            if tile["id"] == 0 and not segments:
                continue

            # distancia corregida (fisheye fix)
            dist = depth * math.cos(angle - editor.cam_angle)
            dist = max(dist, 0.0001)

            horizon = (VIEW_H / 2) + editor.pitch

            # fallback si no hay segmentos
            if not segments:
                segments = [{
                    "tex": tile["id"],
                    "z0": 0,
                    "z1": tile["h"],
                    "solid": True
                }]

            # ordenar por altura
            segments = sorted(segments, key=lambda s: s["z0"])

            new_segments = visible_segments[:]

            for seg in segments:
                seg_z0 = seg["z0"] * TILE_SIZE
                seg_z1 = seg["z1"] * TILE_SIZE

                # proyección
                proj_z0 = ((seg_z0 - camera_z) / dist) * proj_plane
                proj_z1 = ((seg_z1 - camera_z) / dist) * proj_plane

                screen_top = horizon - proj_z1
                screen_bottom = horizon - proj_z0

                if screen_top > screen_bottom:
                    screen_top, screen_bottom = screen_bottom, screen_top

                texture = textures.get(seg["tex"])
                if texture is None:
                    continue

                # cálculo UV
                prev_x = editor.cam_x + cos_a * (depth - 1) * 0.02
                prev_y = editor.cam_y + sin_a * (depth - 1) * 0.02

                if int(prev_x) != int(x):
                    wall_x = y % 1
                    if cos_a > 0:
                        wall_x = 1 - wall_x
                else:
                    wall_x = x % 1
                    if sin_a < 0:
                        wall_x = 1 - wall_x

                tex_x = int(wall_x * texture.get_width())
                tex_x = max(0, min(texture.get_width() - 1, tex_x))

                temp_segments = []

                for seg_top, seg_bottom in new_segments:
                    draw_top = max(screen_top, seg_top)
                    draw_bottom = min(screen_bottom, seg_bottom)

                    if draw_bottom <= draw_top:
                        temp_segments.append((seg_top, seg_bottom))
                        continue

                    # dibujar columna
                    column = texture.subsurface(tex_x, 0, 1, texture.get_height())
                    column = pygame.transform.scale(
                        column,
                        (col_width, int(draw_bottom - draw_top))
                    )
                    screen.blit(column, (ray * col_width, int(draw_top)))

                    if seg.get("solid", True):
                        # bloquea
                        if seg_top < draw_top:
                            temp_segments.append((seg_top, draw_top))
                        if draw_bottom < seg_bottom:
                            temp_segments.append((draw_bottom, seg_bottom))
                    else:
                        # transparente
                        temp_segments.append((seg_top, seg_bottom))

                # actualizar visibilidad
                new_segments = temp_segments

                # filtrar ruido
                filtered_segments = [
                    (t, b) for (t, b) in new_segments if (b - t) > 1
                ]

                visible_segments = filtered_segments

                if not visible_segments:
                    break

def load_textures():
    textures = {}
    base_path = os.path.dirname(__file__)
    tex_path = os.path.join(base_path, "textures")

    texture_files = load_texture_list()

    for k, filename in texture_files.items():
        path = os.path.join(tex_path, filename)
        textures[k] = pygame.image.load(path).convert_alpha()

    return textures, texture_files
                    
def refresh_segments():
    global segment_listbox
    #segment_listbox.delete(0, tk.END)
    if segment_listbox is not None:
        segment_listbox.delete(0, tk.END)

    x = selected_tile["x"]
    y = selected_tile["y"]

    if x is None:
        return

    tile = editor.grid[y][x]

    for i, seg in enumerate(tile.get("segments", [])):
        segment_listbox.insert(
            tk.END,
            f"{i}: tex={seg['tex']} z0={seg['z0']} z1={seg['z1']}"
        )

#map_surface = pygame.Surface((VIEW_W, VIEW_H))
#map_surface.fill((0,0,0))

def redraw_map():
    #map_surface.fill((0,0,0))
    print("redraw_map")
    for y in range(GRID_H):
        for x in range(GRID_W):
            tile = editor.grid[y][x]

            #if tile.get("segments"):
                #pygame.draw.rect(map_surface, (255,255,0),
                   # (x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE), 2)

            #pygame.draw.rect(map_surface, (50,50,50),
             #   (x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE), 1)

def pygame_loop():
    pygame.init()
    screen = pygame.display.set_mode((VIEW_W, VIEW_H))
    clock = pygame.time.Clock()
    global ui_needs_refresh

    textures, texture_files = load_textures()
    editor.texture_files = texture_files
    #redraw_map()
    while editor.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                editor.running = False

        keys = pygame.key.get_pressed()
        speed = 0.5
        # movimiento FPS
        if keys[pygame.K_w]:
            editor.cam_x += math.cos(editor.cam_angle) * speed
            editor.cam_y += math.sin(editor.cam_angle) * speed
        if keys[pygame.K_s]:
            editor.cam_x -= math.cos(editor.cam_angle) * speed
            editor.cam_y -= math.sin(editor.cam_angle) * speed
        if keys[pygame.K_a]:
            editor.cam_angle -= 0.05
        if keys[pygame.K_d]:
            editor.cam_angle += 0.05

        if keys[pygame.K_UP]:
            editor.pitch -= 5

        if keys[pygame.K_DOWN]:
            editor.pitch += 5

        screen.fill((0,0,0))

        # -------- MAPA 2D --------
        #screen.blit(map_surface, (0, 0))
                
        # --------- DIBUJAR CÁMARA ----------
        cam_px = int(editor.cam_x * TILE_SIZE)
        cam_py = int(editor.cam_y * TILE_SIZE)

        # punto
        #pygame.draw.circle(screen, (255,255,0), (cam_px, cam_py), 5)

        # dirección
        dir_x = math.cos(editor.cam_angle)
        dir_y = math.sin(editor.cam_angle)

        pygame.draw.line(
        screen,
            (255,255,0),
            (cam_px, cam_py),
            (cam_px + int(dir_x * 20), cam_py + int(dir_y * 20)),
            2
        )
        pygame.draw.rect(screen, (80, 120, 200), (0, 0, VIEW_W, VIEW_H//2))
        pygame.draw.rect(screen, (40, 40, 40), (0, VIEW_H//2, VIEW_W, VIEW_H//2))
        # -------- RENDER 3D --------
        cast_rays(screen, textures)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

# ------------ EXPORT -------------------
def save_map():
    path = filedialog.asksaveasfilename(defaultextension=".json")
    if not path:
        return

    data = {
        "grid_w": GRID_W,
        "grid_h": GRID_H,
        "grid": editor.grid,
        "camera": {
            "x": editor.cam_x,
            "y": editor.cam_y,
            "angle": editor.cam_angle,
            "height": editor.cam_height,
            "pitch": editor.pitch
        }
    }

    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    print("Mapa guardado correctamente")

def export_mesh_json():
    path = filedialog.asksaveasfilename(defaultextension=".json")
    if not path:
        return

    mesh = generate_mesh()

    with open(path, "w") as f:
        json.dump(mesh, f, indent=2)

    print("Mesh exportado:", path)

def export_mesh_bin():
    path = filedialog.asksaveasfilename(defaultextension=".bin")
    if not path:
        return

    mesh = generate_mesh()

    with open(path, "wb") as f:
        f.write(struct.pack("i", len(mesh)))

        for quad in mesh:
            f.write(struct.pack("i", quad["texture"]))

            for v in quad["vertices"]:
                f.write(struct.pack("fff", v[0], v[1], v[2]))

    print("Mesh BIN exportado")

def save_bin():
    path = filedialog.asksaveasfilename(defaultextension=".bin")
    if path:
        with open(path, "wb") as f:
            f.write(struct.pack("ii", GRID_W, GRID_H))
            for row in editor.grid:
                for tile in row:
                    f.write(struct.pack("bb", tile["id"], tile["h"]))
        print("BIN exportado (Dreamcast ready)")




def generate_mesh():
    mesh = []

    for y in range(GRID_H):
        for x in range(GRID_W):
            tile = editor.grid[y][x]

            if tile["id"] == 0:
                continue

            h = tile["h"]

            # posiciones base
            x0 = x
            x1 = x + 1
            z0 = y
            z1 = y + 1

            y0 = 0
            y1 = h

            tex = tile["id"]

            # --------- vecinos ----------
            def empty(nx, ny):
                if nx < 0 or ny < 0 or nx >= GRID_W or ny >= GRID_H:
                    return True
                return editor.grid[ny][nx]["id"] == 0

            # --------- PARED NORTE ----------
            if empty(x, y - 1):
                mesh.append({
                    "type": "quad",
                    "texture": tex,
                    "vertices": [
                        [x0, y0, z0],
                        [x1, y0, z0],
                        [x1, y1, z0],
                        [x0, y1, z0]
                    ]
                })

            # --------- SUR ----------
            if empty(x, y + 1):
                mesh.append({
                    "type": "quad",
                    "texture": tex,
                    "vertices": [
                        [x1, y0, z1],
                        [x0, y0, z1],
                        [x0, y1, z1],
                        [x1, y1, z1]
                    ]
                })

            # --------- OESTE ----------
            if empty(x - 1, y):
                mesh.append({
                    "type": "quad",
                    "texture": tex,
                    "vertices": [
                        [x0, y0, z1],
                        [x0, y0, z0],
                        [x0, y1, z0],
                        [x0, y1, z1]
                    ]
                })

            # --------- ESTE ----------
            if empty(x + 1, y):
                mesh.append({
                    "type": "quad",
                    "texture": tex,
                    "vertices": [
                        [x1, y0, z0],
                        [x1, y0, z1],
                        [x1, y1, z1],
                        [x1, y1, z0]
                    ]
                })

            # --------- TECHO ----------
            mesh.append({
                "type": "quad",
                "texture": tex,
                "vertices": [
                    [x0, y1, z0],
                    [x1, y1, z0],
                    [x1, y1, z1],
                    [x0, y1, z1]
                ]
            })

            # --------- PISO ----------
            mesh.append({
                "type": "quad",
                "texture": tex,
                "vertices": [
                    [x0, y0, z1],
                    [x1, y0, z1],
                    [x1, y0, z0],
                    [x0, y0, z0]
                ]
            })

    return mesh

def get_selected_prefab():
    if library_listbox is None:
        return None

    sel = library_listbox.curselection()
    if not sel:
        return None

    name = library_listbox.get(sel[0])
    return segment_library.get(name)

# ------------ TKINTER ------------------


def start_ui():
    root = tk.Tk()
    root.title("Editor Doom-like")
    from PIL import Image, ImageTk

    texture_preview_ref = None  # evitar GC

    texture_thumbs = {}
    texture_refs = []  # evitar GC
    selected_texture_id = [0]
    global library_listbox

    selected_prefab_name = [None]

    main_frame = tk.Frame(root)
    main_frame.pack(fill="both", expand=True)

    # configurar columnas
    main_frame.columnconfigure(0, weight=0)  # izquierda (fijo)
    main_frame.columnconfigure(1, weight=1)  # centro (flex)
    main_frame.columnconfigure(2, weight=1)  # derecha (flex)

    main_frame.rowconfigure(0, weight=1)

    left_frame = tk.Frame(main_frame)
    left_frame.grid(row=0, column=0, sticky="ns", padx=5, pady=5)

    center_frame = tk.Frame(main_frame)
    center_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

    map_frame = tk.Frame(main_frame)
    map_frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)

    bottom_frame = tk.Frame(root) 
    bottom_frame.pack(fill="x", padx=5, pady=5)

    #tk.Label(left_frame, text="Tiles").pack()

    #tk.Label(left_frame, text="Altura cámara").pack()

    cam_height_var = tk.IntVar(value=1)

    def update_cam_height(*args):
        editor.cam_height = cam_height_var.get()

    cam_height_var.trace("w", update_cam_height)

    #tk.Entry(left_frame, textvariable=cam_height_var).pack(fill="x")

    #tk.Label(left_frame, text="Angulo cámara").pack()

    cam_angle_var = tk.IntVar(value=0)

    def update_cam_angle(*args):
        editor.cam_angle = cam_angle_var.get()

    cam_angle_var.trace("w", update_cam_angle)

    #tk.Entry(left_frame, textvariable=cam_angle_var).pack(fill="x")

    #tk.Label(root, text="Altura tile").pack()

    #tile_height_var = tk.IntVar(value=2)

    #def update_tile_height(*args):
     #   editor.current_height = tile_height_var.get()

    #tile_height_var.trace("w", update_tile_height)

    #tk.Entry(root, textvariable=tile_height_var).pack(fill="x")

    #tk.Label(left_frame, text="Pitch (inclinación)").pack()

    pitch_var = tk.IntVar(value=0)

    def update_pitch(*args):
        editor.pitch = pitch_var.get()

    pitch_var.trace("w", update_pitch)

    #tk.Entry(left_frame, textvariable=pitch_var).pack(fill="x")

    def draw_texture_preview(texture_name):
        nonlocal texture_preview_ref

        base_path = os.path.dirname(__file__)
        tex_path = os.path.join(base_path, "textures")
        path = os.path.join(tex_path, texture_name)

        if not os.path.exists(path):
            return

        img = Image.open(path).convert("RGBA")

        # escalar al canvas
        img = img.resize((128, 128), Image.NEAREST)

        tk_img = ImageTk.PhotoImage(img)
        texture_preview_ref = tk_img

        texture_canvas.delete("all")
        texture_canvas.create_image(64, 64, image=tk_img)

    def update_texture_selection():
        for i, widget in enumerate(texture_frame.winfo_children()):
            tex_id = list(editor.texture_files.keys())[i]

            if tex_id == selected_texture_id[0]:
                widget.config(relief="solid", bd=3, bg="yellow")
            else:
                widget.config(relief="flat", bd=2, bg="black")

    def build_texture_grid():
        nonlocal texture_refs

        # limpiar
        for widget in texture_frame.winfo_children():
            widget.destroy()

        texture_refs = []

        base_path = os.path.dirname(__file__)
        tex_path = os.path.join(base_path, "textures")

        cols = 4  # cantidad de columnas
        size = 64  # tamaño preview

        for i, (tex_id, filename) in enumerate(editor.texture_files.items()):
            path = os.path.join(tex_path, filename)

            if not os.path.exists(path):
                continue

            img = Image.open(path).convert("RGBA")
            img = img.resize((size, size), Image.NEAREST)

            tk_img = ImageTk.PhotoImage(img)
            texture_refs.append(tk_img)

            btn = tk.Label(texture_frame, image=tk_img, bd=2, relief="flat")
            btn.grid(row=i // cols, column=i % cols, padx=2, pady=2)

            # click
            def on_click(e, tex_id=tex_id, widget=btn):
                editor.selected = tex_id
                selected_texture_id[0] = tex_id
                update_texture_selection()

                texture_name = editor.texture_files[tex_id]
                draw_texture_preview(texture_name)

            btn.bind("<Button-1>", on_click)

    tk.Label(left_frame, text="Preview textura").pack()

    texture_canvas = tk.Canvas(left_frame, width=128, height=128, bg="black")
    texture_canvas.pack(pady=5)

    tk.Label(left_frame, text="Textura").pack()

    texture_frame = tk.Frame(left_frame)
    texture_frame.pack()

    texture_var = tk.StringVar()

    def update_texture(*args):
        selected_name = texture_var.get()

        for k, name in editor.texture_files.items():
            if name == selected_name:
                editor.selected = k
                break

        draw_texture_preview(selected_name)  # 👈 CLAVE

    texture_var.trace("w", update_texture)

    # lista de nombres
    texture_names = list(editor.texture_files.values())

    if texture_names:
        texture_var.set(texture_names[0])

    #dropdown = tk.OptionMenu(left_frame, texture_var, *texture_names)
    #dropdown.pack(fill="x")
    if texture_names:
        texture_var.set(texture_names[0])
        draw_texture_preview(texture_names[0])

    build_texture_grid()
    update_texture_selection()

    
    z0_var = tk.IntVar()
    z1_var = tk.IntVar(value=1)
    solid_var = tk.BooleanVar(value=True)

    global segment_listbox
    segment_listbox = tk.Listbox(root)
    #segment_listbox.pack(fill="both", expand=True)
    
    tk.Label(left_frame, text="z0").pack()
    tk.Entry(left_frame, textvariable=z0_var).pack(fill="x")

    tk.Label(left_frame, text="z1").pack()
    tk.Entry(left_frame, textvariable=z1_var).pack(fill="x")

    def subir_nivel():
        z0 = z0_var.get()
        z1 = z1_var.get()

        z0 += 1
        z1 +=1

        z0_var.set(z0)
        z1_var.set(z1)

    #tk.Button(left_frame, text="Subir nivel", command=subir_nivel).pack(fill="x")

    tk.Label(left_frame, text="solid").pack()
    
    tk.Checkbutton(left_frame, text="Sólido", variable=solid_var).pack(fill="x")

    global current_segments_listbox

    tk.Label(center_frame, text="Segmentos en edición").pack()

    current_segments_listbox = tk.Listbox(center_frame)
    current_segments_listbox.pack(fill="both", expand=True)
    current_prefab_label = tk.Label(center_frame, text="Prefab: ninguno")
    current_prefab_label.pack()
    preview_canvas = tk.Canvas(center_frame, width=120, height=300, bg="black")
    preview_canvas.pack(pady=10)

    def refresh_current_segments():
        current_segments_listbox.delete(0, tk.END)

        for i, seg in enumerate(current_segments):
            current_segments_listbox.insert(
                tk.END,
                f"{i}: tex={seg['tex']} z0={seg['z0']} z1={seg['z1']} solid={seg['solid']}"
            )

    def draw_segment_preview(selected_index=None):
        preview_canvas.delete("all")
        preview_canvas.images = []  # 👈 limpiar referencias viejas
        base_path = os.path.dirname(__file__)
        tex_path = os.path.join(base_path, "textures")

        H = 300
        W = 120
        scale = 40  # píxeles por unidad Z

        # grilla de referencia
        for i in range(0, int(H / scale) + 2):
            y = H - i * scale
            preview_canvas.create_line(0, y, W, y, fill="#333")

        # línea base
        preview_canvas.create_line(0, H, W, H, fill="white")

        for i, seg in enumerate(current_segments):
            z0 = seg["z0"]
            z1 = seg["z1"]

            y0 = H - (z0 * scale)
            y1 = H - (z1 * scale)

            top = min(y0, y1)
            bottom = max(y0, y1)

            tex_id = seg["tex"]
            solid = seg.get("solid", 1)

            # color de debug según textura
            color = f"#{(tex_id * 53) % 255:02x}{(120 + tex_id * 29) % 255:02x}{(200 - tex_id * 17) % 255:02x}"

            if not solid:
                color = "#88ccff"

            img = Image.open(os.path.join(tex_path, editor.texture_files[tex_id]))
            img = img.resize((W-20, int(bottom-top)), Image.NEAREST)

            tk_img = ImageTk.PhotoImage(img)

            if not hasattr(preview_canvas, "images"):
                preview_canvas.images = []

            preview_canvas.images.append(tk_img)

            if i == selected_index:
                outline = "yellow"
                width = 3
            else:
                outline = "black"
                width = 1

            preview_canvas.create_image( W//2, (top + bottom)//2, image=tk_img )

    def add_segment():
        z0 = z0_var.get()
        z1 = z1_var.get()
        solid = solid_var.get()

        if z1 <= z0:
            print("z1 debe ser mayor que z0")
            return
        if solid > 1 or solid < 0:
            print("solid debe ser 1 o 0")
            return

        seg = {
            "tex": editor.selected,
            "z0": z0,
            "z1": z1,
            "solid": solid
        }

        current_segments.append(seg)

        print("Segmento agregado:", seg)

        refresh_current_segments()
        draw_segment_preview()
        subir_nivel()

    tk.Button(left_frame, text="Agregar segmento", command=add_segment).pack(fill="x")

    library_listbox = tk.Listbox(center_frame)
    library_listbox.pack(fill="both", expand=True)

    
    def on_segment_select(event):
        sel = current_segments_listbox.curselection()
        
        if not sel:
            return

        idx = sel[0]
        seg = current_segments[idx]

        # cargar valores en UI
        z0_var.set(seg["z0"])
        z1_var.set(seg["z1"])
        solid_var.set(seg["solid"])

        # seleccionar textura automáticamente
        selected_texture_id[0] = seg["tex"]
        editor.selected = seg["tex"]
        update_texture_selection()

        texture_name = editor.texture_files[seg["tex"]]
        draw_texture_preview(texture_name)

        # 👉 redraw preview destacando este segmento
        draw_segment_preview(selected_index=idx)

    current_segments_listbox.bind("<<ListboxSelect>>", on_segment_select)

    def on_prefab_select(event):
        sel = library_listbox.curselection()
        if not sel:
            return

        name = library_listbox.get(sel[0])

        selected_prefab_name[0] = name

        prefab = segment_library[name]

        current_prefab_label.config(text=f"Prefab: {name}")

        # 🔥 copiar al buffer editable
        current_segments.clear()
        current_segments.extend([seg.copy() for seg in prefab])

        # actualizar UI
        refresh_current_segments()
        draw_segment_preview()

    library_listbox.bind("<<ListboxSelect>>", on_prefab_select)

    def refresh_library_list():
        library_listbox.delete(0, tk.END)

        for name in segment_library.keys():
            library_listbox.insert(tk.END, name)
            
    def save_segment_library():
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if not path:
            return

        with open(path, "w") as f:
            json.dump(segment_library, f, indent=2)

        print("Librería guardada")

    def load_segment_library():
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return

        global segment_library

        with open(path, "r") as f:
            segment_library = json.load(f)

        refresh_library_list()
        print("Librería cargada")


    def apply_prefab_to_tile():
        x = selected_tile["x"]
        y = selected_tile["y"]

        if x is None:
            return

        sel = library_listbox.curselection()
        if not sel:
            return

        name = library_listbox.get(sel[0])

        prefab = segment_library[name]

        # copiar (MUY IMPORTANTE evitar referencias)
        editor.grid[y][x]["segments"] = [seg.copy() for seg in prefab]

        print("Prefab aplicado:", name)
        refresh_segments()

    def delete_segment():
        sel = current_segments_listbox.curselection()
        if not sel:
            return

        idx = sel[0]
        current_segments.pop(idx)

        refresh_current_segments()
        draw_segment_preview()

    def clear_current_segments():
        current_segments.clear()
        draw_segment_preview()
        refresh_current_segments()
        z0_var.set(0)
        z1_var.set(1)

    def ui_update_loop():
        global ui_needs_refresh

        if ui_needs_refresh:
            refresh_segments()
            ui_needs_refresh = False

        root.after(50, ui_update_loop)

    def save_buffer_as_prefab():
        if not current_segments:
            return

        name = simpledialog.askstring("Nombre", "Nombre del prefab:")
        if not name:
            return

        segment_library[name] = [seg.copy() for seg in current_segments]

        refresh_library_list()

    tk.Button(left_frame, text="Limpiar segmentos", command=clear_current_segments).pack(fill="x")
    
    def update_segment():
        sel = current_segments_listbox.curselection()
        if not sel:
            return

        idx = sel[0]

        z0 = z0_var.get()
        z1 = z1_var.get()
        solid = solid_var.get()

        if z1 <= z0:
            print("z1 debe ser mayor que z0")
            return

        current_segments[idx] = {
            "tex": editor.selected,
            "z0": z0,
            "z1": z1,
            "solid": solid
        }

        refresh_current_segments()
        draw_segment_preview(selected_index=idx)

    tk.Button(left_frame, text="Actualizar segmento", command=update_segment).pack(fill="x")

    #tk.Button(root, text="Guardar Prefab", command=save_current_tile_as_prefab).pack(fill="x")
    def update_prefab():
        name = selected_prefab_name[0]

        if not name:
            print("No hay prefab seleccionado")
            return

        segment_library[name] = [seg.copy() for seg in current_segments]

        print("Prefab actualizado:", name)


    tk.Button(left_frame, text="Actualizar Prefab", command=update_prefab).pack(fill="x")
    tk.Button(left_frame, text="Guardar Prefab)", command=save_buffer_as_prefab).pack(fill="x")
    #tk.Button(root, text="Guardar Prefab (tile)", command=save_current_tile_as_prefab).pack(fill="x")
    #tk.Button(root, text="Aplicar Prefab", command=apply_prefab_to_tile).pack(fill="x")

    def load_map():
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return

        with open(path, "r") as f:
            data = json.load(f)

        # --- VALIDACIÓN ---
        if "grid" not in data:
            print("Archivo inválido")
            return

        # --- CARGAR GRID ---
        editor.grid = data["grid"]

        # --- CARGAR CÁMARA ---
        cam = data.get("camera", {})
        editor.cam_x = cam.get("x", 3.5)
        editor.cam_y = cam.get("y", 3.5)
        editor.cam_angle = cam.get("angle", 0)
        editor.cam_height = cam.get("height", 1)
        editor.pitch = cam.get("pitch", 0)

        #redraw_map()
        for y in range(GRID_H):
            for x in range(GRID_W):
                update_tile_visual(x, y)

        print("Mapa cargado correctamente")


    def create_grid_editor(parent):
        canvas_frame = tk.Frame(parent)
        canvas_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(canvas_frame, bg="#111")

        h_scroll = tk.Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
        v_scroll = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)

        canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

        h_scroll.pack(side="bottom", fill="x")
        v_scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # tamaño total
        canvas.config(scrollregion=(0, 0, GRID_W * TILE_SIZE, GRID_H * TILE_SIZE))

        rects = {}

        for y in range(GRID_H):
            for x in range(GRID_W):
                x0 = x * TILE_SIZE
                y0 = y * TILE_SIZE
                x1 = x0 + TILE_SIZE
                y1 = y0 + TILE_SIZE

                rect = canvas.create_rectangle(
                    x0, y0, x1, y1,
                    fill="#222",
                    outline="#444"
                )

                rects[(x, y)] = rect
        def update_camera_marker():
            px = editor.cam_x * TILE_SIZE
            py = editor.cam_y * TILE_SIZE

            r = 5

            # círculo
            canvas.coords(
                cam_marker,
                px - r, py - r,
                px + r, py + r
            )

            # dirección
            dx = math.cos(editor.cam_angle)
            dy = math.sin(editor.cam_angle)

            length = 20

            canvas.coords(
                cam_dir_line,
                px, py,
                px + dx * length,
                py + dy * length
            )

            canvas.xview_moveto((px - 200) / (GRID_W * TILE_SIZE))
            canvas.yview_moveto((py - 150) / (GRID_H * TILE_SIZE))

            canvas.after(30, update_camera_marker)

        def update_tile_visual(x, y):
            tile = editor.grid[y][x]

            if tile.get("segments"):
                color = "yellow"
            elif tile["id"] == 0:
                color = "#222"
            else:
                color = "#555"

            canvas.itemconfig(rects[(x, y)], fill=color)

        def on_click(event):
            gx = int(canvas.canvasx(event.x) // TILE_SIZE)
            gy = int(canvas.canvasy(event.y) // TILE_SIZE)

            if not (0 <= gx < GRID_W and 0 <= gy < GRID_H):
                return

            selected_tile["x"] = gx
            selected_tile["y"] = gy

            prefab = get_selected_prefab()

            if prefab:
                editor.grid[gy][gx]["segments"] = [seg.copy() for seg in prefab]

            elif current_segments:
                editor.grid[gy][gx]["segments"] = [seg.copy() for seg in current_segments]

            update_tile_visual(gx, gy)
            refresh_segments()

        canvas.bind("<Button-1>", on_click)

        # marcador de cámara
        cam_marker = canvas.create_oval(0, 0, 0, 0, fill="yellow")
        cam_dir_line = canvas.create_line(0, 0, 0, 0, fill="yellow", width=2)

        update_camera_marker()

        return canvas, rects, update_tile_visual
    
    grid_canvas, grid_rects, update_tile_visual = create_grid_editor(map_frame)

    tk.Button(map_frame, text="Guardar Librería", command=save_segment_library).pack(fill="x")
    tk.Button(map_frame, text="Cargar Librería", command=load_segment_library).pack(fill="x")

    tk.Button(left_frame, text="Eliminar segmento", command=delete_segment).pack(fill="x")


    tk.Button(map_frame, text="Guardar mapa", command=save_map).pack(fill="x")
    tk.Button(map_frame, text="Cargar Mapa", command=load_map).pack(fill="x")
    tk.Button(map_frame, text="Exportar BIN", command=save_bin).pack(fill="x")
    tk.Button(map_frame, text="Exportar Mesh JSON", command=export_mesh_json).pack(fill="x")
    tk.Button(map_frame, text="Exportar Mesh BIN", command=export_mesh_bin).pack(fill="x")

    #def reload_textures():
        #texture_names = list(editor.texture_files.values())
        #menu = dropdown["menu"]
        #menu.delete(0, "end")

        #for name in texture_names:
            #menu.add_command(label=name,
                #command=lambda v=name: texture_var.set(v))

    #reload_textures()
    ui_update_loop()
    root.mainloop()

# ------------ THREAD -------------------
#textures, texture_files = load_textures()
#editor.texture_files = texture_files
editor.texture_files = load_texture_list()

t = threading.Thread(target=pygame_loop)
t.start()

start_ui()
editor.running = False
t.join()
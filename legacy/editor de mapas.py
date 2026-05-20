import pygame
import math
import sys
import os
import json
import struct

WIDTH, HEIGHT = 1000, 600
EDITOR_WIDTH = 400
VIEW_WIDTH = WIDTH - EDITOR_WIDTH
RENDER_SCALE = 2
R_WIDTH = VIEW_WIDTH // RENDER_SCALE
R_HEIGHT = HEIGHT // RENDER_SCALE
MAP_SCALE = 64
FOV = math.pi / 3
HALF_FOV = FOV / 2
NUM_RAYS = 120
DELTA_ANGLE = FOV / NUM_RAYS
DIST = NUM_RAYS / (2 * math.tan(HALF_FOV))
PROJ_COEFF = DIST * 50
TEXTURE_SIZE = 64
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEXTURE_FOLDER = os.path.join(BASE_DIR, "textures")
z_buffer = [float("inf")] * NUM_RAYS
object_h = 2.0

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
view_surface = pygame.Surface((R_WIDTH, R_HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 14)

textures = {}
objects = []
edit_layer = "wall"

editor_zoom = 8
MIN_ZOOM = 4
MAX_ZOOM = 32
current_height = 1

current_texture = 2
scroll_offset = 0

if not os.path.exists(TEXTURE_FOLDER):
    os.makedirs(TEXTURE_FOLDER)

def load_texture(path):
    try:
        return pygame.transform.scale(pygame.image.load(path).convert(), (TEXTURE_SIZE, TEXTURE_SIZE))
    except:
        surf = pygame.Surface((TEXTURE_SIZE, TEXTURE_SIZE))
        surf.fill((200,200,200))
        return surf

def load_all_textures():
    global textures
    textures = {}
    files = [f for f in os.listdir(TEXTURE_FOLDER) if f.endswith(".png")]
    for i, file in enumerate(files, start=1):
        textures[i] = load_texture(os.path.join(TEXTURE_FOLDER, file))

load_all_textures()

map_width, map_height = 32, 32
world_map = [[0 for _ in range(map_width)] for _ in range(map_height)]
height_map = [[1 for _ in range(map_width)] for _ in range(map_height)]
floor_map = [[1 for _ in range(map_width)] for _ in range(map_height)]
ceil_map = [[1 for _ in range(map_width)] for _ in range(map_height)]

player_pos = [300.0, 300.0]
player_angle = 0
speed = 6

sin_table = [math.sin(i * DELTA_ANGLE - HALF_FOV) for i in range(NUM_RAYS)]
cos_table = [math.cos(i * DELTA_ANGLE - HALF_FOV) for i in range(NUM_RAYS)]

z_buffer_bottom = [R_HEIGHT]*NUM_RAYS


def cast_rays():
    px, py = player_pos
    sin_pa = math.sin(player_angle)
    cos_pa = math.cos(player_angle)

    for i in range(NUM_RAYS):
        z_buffer[i] = float("inf")
    for ray in range(NUM_RAYS):
        sin_a = sin_pa * cos_table[ray] + cos_pa * sin_table[ray]
        cos_a = cos_pa * cos_table[ray] - sin_pa * sin_table[ray]

        map_x = int(px / MAP_SCALE)
        map_y = int(py / MAP_SCALE)

        delta_x = abs(MAP_SCALE / (cos_a if cos_a != 0 else 1e-6))
        delta_y = abs(MAP_SCALE / (sin_a if sin_a != 0 else 1e-6))

        if cos_a < 0:
            step_x = -1
            side_x = (px - map_x * MAP_SCALE) / (abs(cos_a) if cos_a != 0 else 1e-6)
        else:
            step_x = 1
            side_x = ((map_x + 1) * MAP_SCALE - px) / (abs(cos_a) if cos_a != 0 else 1e-6)

        if sin_a < 0:
            step_y = -1
            side_y = (py - map_y * MAP_SCALE) / (abs(sin_a) if sin_a != 0 else 1e-6)
        else:
            step_y = 1
            side_y = ((map_y + 1) * MAP_SCALE - py) / (abs(sin_a) if sin_a != 0 else 1e-6)

        hit = False
        side = 0

        for _ in range(64):
            if side_x < side_y:
                side_x += delta_x
                map_x += step_x
                side = 0
            else:
                side_y += delta_y
                map_y += step_y
                side = 1

            if 0 <= map_x < map_width and 0 <= map_y < map_height:
                if world_map[map_y][map_x] > 0:
                    hit = True
                    break
            else:
                break

        if not hit:
            z_buffer_bottom[ray] = 0
            continue

        if side == 0:
            depth = side_x - delta_x
            hit_coord = py + depth * sin_a
        else:
            depth = side_y - delta_y
            hit_coord = px + depth * cos_a

        depth *= cos_table[ray]
        z_buffer[ray] = depth

        h = height_map[map_y][map_x]
        proj_h = int((PROJ_COEFF * h) / (depth + 0.0001) / RENDER_SCALE)

        tex = textures.get(world_map[map_y][map_x])
        if not tex:
            continue

        tex_x = int((hit_coord % MAP_SCALE) / MAP_SCALE * TEXTURE_SIZE)
        if (side == 0 and cos_a > 0) or (side == 1 and sin_a < 0):
            tex_x = TEXTURE_SIZE - tex_x - 1

        column = tex.subsurface(tex_x,0,1,TEXTURE_SIZE)

        x1 = int(ray * R_WIDTH / NUM_RAYS)
        x2 = int((ray+1) * R_WIDTH / NUM_RAYS)
        col_w = max(1, x2-x1)

        column = pygame.transform.scale(column,(col_w,proj_h))

        floor_y = int(R_HEIGHT * 0.75)
        y = floor_y - proj_h
        z_buffer_bottom[ray] = floor_y

        view_surface.blit(column,(x1,y))


def draw_floor_and_ceiling():
    px, py = player_pos

    ray_dir_x0 = math.cos(player_angle - HALF_FOV)
    ray_dir_y0 = math.sin(player_angle - HALF_FOV)
    ray_dir_x1 = math.cos(player_angle + HALF_FOV)
    ray_dir_y1 = math.sin(player_angle + HALF_FOV)

    floor_y = int(R_HEIGHT * 0.75)
    half_h = floor_y

    for y in range(half_h, R_HEIGHT):
        p = y - half_h
        if p == 0:
            continue

        row_dist = (0.5 * R_HEIGHT * DIST) / p

        step_x = row_dist * (ray_dir_x1 - ray_dir_x0) / R_WIDTH
        step_y = row_dist * (ray_dir_y1 - ray_dir_y0) / R_WIDTH

        fx = px + row_dist * ray_dir_x0
        fy = py + row_dist * ray_dir_y0

        for x in range(R_WIDTH):
            ray_i = min(NUM_RAYS-1, int(x * NUM_RAYS / R_WIDTH))

            if y < z_buffer_bottom[ray_i]:
                fx += step_x
                fy += step_y
                continue

            cx = int(fx / MAP_SCALE)
            cy = int(fy / MAP_SCALE)

            if 0 <= cx < map_width and 0 <= cy < map_height:
                tx = int((fx % MAP_SCALE) / MAP_SCALE * TEXTURE_SIZE)
                ty = int((fy % MAP_SCALE) / MAP_SCALE * TEXTURE_SIZE)

                tex = textures.get(floor_map[cy][cx])
                if tex:
                    view_surface.set_at((x,y), tex.get_at((tx,ty)))

                texc = textures.get(ceil_map[cy][cx])
                if texc:
                    view_surface.set_at((x,R_HEIGHT-y-1), texc.get_at((tx,ty)))

            fx += step_x
            fy += step_y


def movement():
    global player_angle
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        player_pos[0] += speed * math.cos(player_angle)
        player_pos[1] += speed * math.sin(player_angle)
    if keys[pygame.K_s]:
        player_pos[0] -= speed * math.cos(player_angle)
        player_pos[1] -= speed * math.sin(player_angle)
    if keys[pygame.K_a]: player_angle -= 0.05
    if keys[pygame.K_d]: player_angle += 0.05


def draw_map():
    scale = editor_zoom
    for y in range(map_height):
        for x in range(map_width):
            rect = (x*scale, y*scale, scale, scale)
            if world_map[y][x] > 0:
                pygame.draw.rect(screen,(200,200,200),rect)
            else:
                pygame.draw.rect(screen,(50,50,50),rect,1)

    for o in objects:
        ox = int(o["x"] * scale)
        oy = int(o["y"] * scale)
        pygame.draw.circle(screen, (0,255,0), (ox, oy), 3)

    px = int(player_pos[0] / MAP_SCALE * scale)
    py = int(player_pos[1] / MAP_SCALE * scale)
    pygame.draw.circle(screen,(255,0,0),(px,py),4)


def editor(mouse_pos, l, r):
    global current_texture, current_height, objects

    mx, my = mouse_pos
    if mx >= EDITOR_WIDTH:
        return

    scale = editor_zoom
    mx //= scale
    my //= scale

    if not (0 <= mx < map_width and 0 <= my < map_height):
        return

    if edit_layer == "wall":
        if l:
            world_map[my][mx] = current_texture
            height_map[my][mx] = current_height
        if r:
            world_map[my][mx] = 0

    elif edit_layer == "object":
        if l:
            objects.append({
                "x": mx + 0.5,
                "y": my + 0.5,
                "tex": current_texture,
                "h": object_h
            })
        if r:
            objects = [
                o for o in objects
                if int(o["x"]) != mx or int(o["y"]) != my
            ]


def draw_texture_selector():
    global current_texture

    x = 10 - scroll_offset
    y = HEIGHT - 80
    size = 40

    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()[0]

    for tex_id, tex in textures.items():
        rect = pygame.Rect(x, y, size, size)
        preview = pygame.transform.scale(tex, (size, size))

        screen.blit(preview, rect.topleft)

        if tex_id == current_texture:
            pygame.draw.rect(screen, (255,255,0), rect, 2)
        else:
            pygame.draw.rect(screen, (100,100,100), rect, 1)

        if rect.collidepoint(mouse) and click:
            current_texture = tex_id

        x += size + 10


def draw_hud():
    pygame.draw.rect(screen,(20,20,20),(0,HEIGHT-100,EDITOR_WIDTH,100))

    draw_texture_selector()

    txt = font.render(f"TAB | 1:Wall 4:Object | Tex:{current_texture} H:{current_height} Zoom:{editor_zoom}",True,(255,255,255))
    screen.blit(txt,(10,HEIGHT-20))


edit_mode = True

SAVE_FILE = "map.json"
EXPORT_FILE = "map_dc.bin"

def save_map():
    data = {
        "w": map_width,
        "h": map_height,
        "world": world_map,
        "height": height_map,
        "floor": floor_map,
        "ceil": ceil_map,
        "player": player_pos,
        "angle": player_angle,
        "objects": objects
    }
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f)


def load_map():
    global world_map, height_map, floor_map, ceil_map, player_pos, player_angle, objects
    if not os.path.exists(SAVE_FILE):
        return
    with open(SAVE_FILE, "r") as f:
        data = json.load(f)
    world_map = data["world"]
    height_map = data["height"]
    floor_map = data["floor"]
    ceil_map = data["ceil"]
    player_pos = data["player"]
    player_angle = data["angle"]
    objects = data.get("objects", [])

def draw_objects():
    px, py = player_pos

    for obj in sorted(objects, key=lambda o: -((o["x"]*MAP_SCALE - px)**2 + (o["y"]*MAP_SCALE - py)**2)):

        dx = obj["x"] * MAP_SCALE - px
        dy = obj["y"] * MAP_SCALE - py

        dist = math.hypot(dx, dy)
        angle = math.atan2(dy, dx) - player_angle

        # normalizar ángulo
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi

        # fuera de FOV
        if abs(angle) > HALF_FOV:
            continue

        # posición en pantalla
        screen_x = (angle + HALF_FOV) / FOV * R_WIDTH

        # tamaño
        size = int((PROJ_COEFF / (dist + 0.0001)) * obj["h"] / RENDER_SCALE)

        # 🔥 z-buffer CORRECTO
        ray = int(screen_x / R_WIDTH * NUM_RAYS)
        if 0 <= ray < NUM_RAYS:
            if dist > z_buffer[ray]:
                continue

        tex = textures.get(obj["tex"])
        if not tex:
            continue

        sprite = pygame.transform.scale(tex, (size, size))

        x = int(screen_x - size // 2)
        y = int(z_buffer_bottom[ray] - size)

        view_surface.blit(sprite, (x, y))

def export_dreamcast():
    with open(EXPORT_FILE, "wb") as f:
        f.write(struct.pack("ii", map_width, map_height))
        for y in range(map_height):
            for x in range(map_width):
                f.write(struct.pack("BBBB",
                    world_map[y][x],
                    height_map[y][x],
                    floor_map[y][x],
                    ceil_map[y][x]
                ))
        f.write(struct.pack("ff", player_pos[0], player_pos[1]))
        f.write(struct.pack("f", player_angle))

while True:
    screen.fill((30,30,30))
    view_surface.fill((0,0,0))

    mouse_buttons = pygame.mouse.get_pressed()

    for e in pygame.event.get():
        if e.type==pygame.QUIT:
            pygame.quit();sys.exit()
        if e.type==pygame.KEYDOWN:
            if e.key==pygame.K_TAB:
                edit_mode = not edit_mode
            if e.key==pygame.K_q:
                current_height = max(1, current_height - 1)
            if e.key==pygame.K_e:
                current_height = min(6, current_height + 1)
            if e.key==pygame.K_EQUALS:
                editor_zoom = min(MAX_ZOOM, editor_zoom + 2)
            if e.key==pygame.K_MINUS:
                editor_zoom = max(MIN_ZOOM, editor_zoom - 2)
            if e.key==pygame.K_s:
                save_map()
            if e.key==pygame.K_l:
                load_map()
            if e.key==pygame.K_x:
                export_dreamcast()
            if e.key == pygame.K_1:
                edit_layer = "wall"

            if e.key == pygame.K_4:
                edit_layer = "object"

        if e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == 4:
                editor_zoom = min(MAX_ZOOM, editor_zoom + 2)
            if e.button == 5:
                editor_zoom = max(MIN_ZOOM, editor_zoom - 2)

    if not edit_mode:
        movement()

    editor(pygame.mouse.get_pos(), mouse_buttons[0], mouse_buttons[2])

    cast_rays()
    draw_floor_and_ceiling()
    draw_objects()

    screen.blit(pygame.transform.scale(view_surface,(VIEW_WIDTH,HEIGHT)),(EDITOR_WIDTH,0))

    draw_map()
    draw_hud()

    pygame.display.flip()
    clock.tick(60)

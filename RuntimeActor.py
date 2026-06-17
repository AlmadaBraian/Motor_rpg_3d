
import math

from EventManager import check_runtime_step_events, update_world_event
from config import GRID_H, GRID_W


class RuntimeActor:

    def __init__(self, toolkit):
        self.toolkit = toolkit

    def update_runtime_mantle(self, dt):
        m = self.toolkit.runtime_mantle
        pack = m["pack"]
        inst = pack["inst"]

        wx = pack["gx"] + 0.5 + inst.offx
        wy = inst.offz
        wz = pack["gy"] + 0.5 + inst.offy

        m["timer"] += dt

        # ==========================================
        # FASE 1 — alinearse al borde
        # ==========================================
        if m["phase"] == "align":

            vx = m["align_x"] - wx
            vz = m["align_y"] - wz
            dist = math.hypot(vx, vz)

            if dist > 0.02:
                speed = 4.0 * dt
                wx += (vx/dist) * speed
                wz += (vz/dist) * speed
            else:
                m["phase"] = "jump"
                m["timer"] = 0.0

        # ==========================================
        # FASE 2 — salto vertical corto
        # ==========================================
        elif m["phase"] == "jump":

            inst.offz += 2.0 * dt

            if m["timer"] >= 0.22:
                m["phase"] = "claw"
                m["timer"] = 0.0

                if inst.animator and "claw" in inst.animator.clips:
                    inst.animator.play("claw")

        # ==========================================
        # FASE 3 — arrastre arriba del bloque
        # ==========================================
        elif m["phase"] == "claw":

            vx = m["center_x"] - wx
            vz = m["center_y"] - wz
            dist = math.hypot(vx, vz)

            if dist > 0.03:
                speed = 2.2 * dt
                wx += (vx/dist) * speed
                wz += (vz/dist) * speed

            # subir verticalmente hacia top_z
            if inst.offz < m["top_z"]:
                inst.offz += 2.5 * dt

            if dist <= 0.03 and inst.offz >= m["top_z"] - 0.05:
                m["phase"] = "land"
                m["timer"] = 0.0

        # ==========================================
        # FASE 4 — aterrizaje
        # ==========================================
        elif m["phase"] == "land":

            inst.offz = m["top_z"]

            gx = int(wx)
            gy = int(wz)

            pack["gx"] = gx
            pack["gy"] = gy

            inst.offx = wx - (gx + 0.5)
            inst.offy = wz - (gy + 0.5)

            self.toolkit.runtime_mantle = None
            self.toolkit.world_event_locked = False

            if hasattr(self, "game_view") and self.toolkit.runtime_saved_yaw_game is not None:
                self.toolkit.game_view.camera.yaw = self.toolkit.runtime_saved_yaw_game

            self.toolkit.viewport.camera.yaw = self.toolkit.runtime_saved_yaw_view

            return

        # actualizar coords runtime mientras se mueve
        gx = int(wx)
        gy = int(wz)

        pack["gx"] = gx
        pack["gy"] = gy

        inst.offx = wx - (gx + 0.5)
        inst.offy = wz - (gy + 0.5)


    def update_runtime_actor(self, dt):

        if self.toolkit.runtime_event_cooldown > 0:
            self.toolkit.runtime_event_cooldown -= dt

        if not hasattr(self, "play_mode"):
            return

        if not self.toolkitplay_mode:
            return

        if not hasattr(self, "runtime_world"):
            return

        if self.toolkit.runtime_world is None:
            return

        if not self.toolkit.runtime_world.main_actor:
            return
        
        if self.toolkit.world_event_running:
            update_world_event(self,dt)

        if self.toolkit.battle_input_cooldown > 0:
            self.toolkit.battle_input_cooldown -= dt

        pack = self.toolkit.runtime_world.main_actor
        inst = pack["inst"]

        if pack["inst"].is_mantling:
            self.update_actor_mantle(pack, dt)

            if hasattr(self, "game_view"):
                self.toolkit.game_view.follow_runtime_camera()

            self.toolkit.viewport.follow_runtime_camera()
            return
        
        if getattr(inst, "is_falling", False):
            self.update_actor_fall(pack, dt)
            return

        move_speed = 1.5 * dt
        rot_speed = 40 * dt

        # =========================================
        # ROTACION DEL ACTOR + CAMARA ORBITAL
        # =========================================
        if inst.rot_l:
            self.toolkit.runtime_cam_orbit -= rot_speed


            if hasattr(self, "game_view"):
                self.toolkit.runtime_cam_orbit -= rot_speed

            self.toolkit.viewport.camera.yaw -= rot_speed

        if inst.rot_r:
            self.toolkit.runtime_cam_orbit += rot_speed

            if not getattr(self, "runtime_camera_locked", False):
                if hasattr(self, "game_view"):
                    self.toolkit.game_view.follow_runtime_camera()

                self.toolkit.viewport.follow_runtime_camera()

        # =========================================
        # CAMARA ACTIVA REAL
        # =========================================
        if self.toolkitplay_mode and hasattr(self, "game_view"):
            active_cam = self.toolkit.game_view.camera
        else:
            active_cam = self.toolkit.viewport.camera

        cam_ang = math.radians(active_cam.yaw)

        dx = 0
        dy = 0

        forward_x = math.sin(cam_ang)
        forward_y = math.cos(cam_ang)

        right_x = math.sin(cam_ang + math.pi/2)
        right_y = math.cos(cam_ang + math.pi/2)

        if inst.move_f:
            dx += forward_x * move_speed
            dy += forward_y * move_speed

        if inst.move_b:
            dx -= forward_x * move_speed
            dy -= forward_y * move_speed

        if inst.move_l:
            dx -= right_x * move_speed
            dy -= right_y * move_speed

        if inst.move_r:
            dx += right_x * move_speed
            dy += right_y * move_speed

        # =========================================
        # CHEQUEAR EVENTOS DE TILE
        # =========================================
        moved = self.try_move_runtime_actor(pack, dx, dy)

        if moved:
            check_runtime_step_events(self)

        # =========================================
        # FOLLOW CAMERA DESPUES DE MOVER
        # =========================================
        if not self.toolkit.battle_mode:

            if hasattr(self, "game_view"):
                self.toolkit.game_view.follow_runtime_camera()

            self.toolkit.viewport.follow_runtime_camera()

        # =========================================
        # ACTUALIZAR ANIM SEGUN CAMARA YA POSICIONADA
        # =========================================
        if getattr(inst, "is_battle_moving", False):
            return
        if inst.animator and not inst.is_mantling:
            if not inst.on_ground:
                pass
            else:
                if abs(dx) > 0.001 or abs(dy) > 0.001:
                    self.update_actor_walk_by_input(inst, dx, dy)
                else:
                    self.update_actor_idle_hybrid(inst, dt)

        if self.toolkit.runtime_message_timer > 0:
            self.toolkit.runtime_message_timer -= dt
            if self.toolkit.runtime_message_timer <= 0:
                self.toolkit.runtime_message = ""

        self.update_runtime_actor_vertical(pack, dt)

        if self.toolkit.world_event_locked:
            return

    def update_actor_fall(self, pack, dt):
        inst = pack["inst"]
        speed = 2.8
        inst.offz -= speed * dt

        if not inst.animator: return
        
        # 1. MIENTRAS CAE: Congelamos en el aire
        if not inst.fall_land_done:
            inst.animator.play("fall")
            inst.animator.frame = 0
            inst.animator.timer = 0
            #inst.animator.paused = True # Evita que el update global sume tiempo

        # 2. MOMENTO DEL IMPACTO: Detectamos suelo
        if inst.offz <= inst.fall_target_z:
            inst.offz = inst.fall_target_z
            inst.ground_z = inst.fall_target_z
            
            if not inst.fall_land_done:
                inst.fall_land_done = True
                inst.animator.paused = False
                inst.animator.timer = 0  # <--- RESETEA AQUÍ TAMBIÉN
                inst.animator.frame = 1

        # 3. ESPERAR A QUE TERMINE LA ANIMACIÓN (Lógica automática)
        if inst.fall_land_done:
            # Dejamos que Animator.update(dt) haga avanzar los frames solo.
            # Solo chequeamos si ya terminó el clip.
            if inst.animator.finished or inst.animator.frame >= len(inst.animator.clips["fall"].frames) - 1:
                inst.is_falling = False
                inst.on_ground = True
                inst.animator.play("idle")
        
    def mantle_camera_yaw_from_dir(self, dx, dy):
        if abs(dx) > abs(dy):
            if dx > 0:
                return 270   # cubo a la derecha, cam a izquierda
            else:
                return 90
        else:
            if dy > 0:
                return 180   # cubo abajo pantalla / actor va sur
            else:
                return 0
        

    def update_actor_idle_view_by_camera(self, inst, moving=False):
        if self.toolkit.play_mode and hasattr(self, "game_view"):
            cam = self.toolkit.game_view.camera
        else:
            cam = self.toolkit.viewport.camera

        cam_ang = cam.yaw % 360
        actor_ang = inst.rot % 360

        rel = (cam_ang - actor_ang) % 360

        # =========================================
        # PREFIJO SEGUN ESTADO
        # =========================================
        prefix = "walk" if moving else "rot"

        # =========================================
        # SUFIJO DIRECCIONAL
        # =========================================
        if rel >= 337 or rel < 22:
            suffix = "_espalda"
        elif rel >= 22 and rel < 67:
            suffix = "_espalda_dere"
        elif rel >= 67 and rel < 112:
            suffix = "_perfil_dere"
        elif rel >= 112 and rel < 157:
            suffix = "_frente_dere"
        elif rel >= 157 and rel < 202:
            suffix = "_frente"
        elif rel >= 202 and rel < 247:
            suffix = "_frente_izq"
        elif rel >= 247 and rel < 292:
            suffix = "_perfil_izq"
        else:
            suffix = "_espalda_izq"

        chosen = prefix + suffix

        # quieto atrás puede usar idle clásico
        if not moving and suffix == "_espalda":
            if "idle" in inst.animator.clips:
                chosen = "idle"
            if inst.guard_mode:
                if "idle_guard" in inst.animator.clips:
                        if inst.guard_mode:
                            chosen = "idle_guard"

        print("CHOSEN =", chosen)

        map_vis = {
            "_espalda": "espalda",
            "_espalda_izq": "espalda_izq",
            "_perfil_izq": "perfil_izq",
            "_frente_izq": "frente_izq",
            "_frente": "frente",
            "_frente_dere": "frente_dere",
            "_perfil_dere": "perfil_dere",
            "_espalda_dere": "espalda_dere"
        }

        inst.visual_facing = map_vis.get(suffix, "espalda")

        if inst.animator:
            if chosen in inst.animator.clips:
                inst.animator.play(chosen)
                return

            # =====================================
            # FALLBACK MIRROR
            # =====================================
            if "_perfil_dere" in chosen and prefix + "_perfil_izq" in inst.animator.clips:
                inst.animator.play(prefix + "_perfil_izq")
                return

            if "_frente_dere" in chosen and prefix + "_frente_izq" in inst.animator.clips:
                inst.animator.play(prefix + "_frente_izq")
                return

            if "_espalda_dere" in chosen and prefix + "_espalda_izq" in inst.animator.clips:
                inst.animator.play(prefix + "_espalda_izq")
                return

            if moving:
                if "walk_espalda" in inst.animator.clips:
                    inst.animator.play("walk_espalda")
                    return
            else:
                if "idle" in inst.animator.clips:
                    inst.animator.play("idle")
                    return
                
    def update_actor_idle_by_facing(self, inst):
        facing = getattr(inst, "facing", "espalda")

        if facing == "espalda":
            preferred = "idle"
        elif facing == "frente":
            preferred = "rot_frente"
        elif facing == "izq":
            preferred = "idle_izq"
        else:
            preferred = "idle_dere"

        if preferred in inst.animator.clips:
            inst.animator.play(preferred)
            return

        if "idle" in inst.animator.clips:
            inst.animator.play("idle")
                
    def update_actor_walk_by_input(self, inst, dx, dy):
        cam = self.toolkit.game_view.get_active_camera()

        cam_ang = math.radians(cam.yaw)

        forward_x = math.sin(cam_ang)
        forward_y = math.cos(cam_ang)

        right_x = math.sin(cam_ang + math.pi/2)
        right_y = math.cos(cam_ang + math.pi/2)

        fdot = dx * forward_x + dy * forward_y
        rdot = dx * right_x + dy * right_y

        chosen = "walk_espalda"
        face = "espalda"

        if abs(fdot) >= abs(rdot):
            if fdot >= 0:
                chosen = "walk_frente"
                face = "frente"
            else:
                
                chosen = "walk_espalda"
                face = "espalda"
        else:
            if rdot >= 0:
                chosen = "walk_perfil_dere"
                face = "dere"
            else:
                chosen = "walk_perfil_izq"
                face = "izq"

        inst.facing = face
        inst.visual_facing = face
        inst.inspect_timer = 0.0
        inst.last_cam_yaw = None

        if chosen in inst.animator.clips:
            if inst.animator.current != chosen:
                inst.animator.play(chosen)
            inst.inspect_timer = 0.0
            inst.last_cam_yaw = None
        elif "walk_espalda" in inst.animator.clips:
            if inst.animator.current != "walk_espalda":
                inst.animator.play("walk_espalda")

    def update_actor_idle_hybrid(self, inst, dt):
        cam = self.toolkit.game_view.camera if self.toolkit.play_mode and hasattr(self, "game_view") else self.toolkit.viewport.camera

        current_yaw = cam.yaw % 360

        if inst.last_cam_yaw is None:
            inst.last_cam_yaw = current_yaw

        diff = abs(current_yaw - inst.last_cam_yaw)

        if diff > 1.0:
            inst.inspect_timer += dt
            inst.last_cam_yaw = current_yaw

            self.update_actor_idle_view_by_camera(inst)
            return

        inst.last_cam_yaw = current_yaw

        # ==========================================
        # QUIETO SIN GIRAR -> conservar ultima pose
        # ==========================================
        vf = getattr(inst, "visual_facing", "espalda")

        if not inst.guard_mode:

            name_map = {
                "espalda": "idle",
                "frente": "idle_frente",
                "izq": "idle_izq",
                "dere": "idle_dere",
                "espalda_izq": "rot_espalda_izq",
                "perfil_izq": "rot_perfil_izq",
                "frente_izq": "rot_frente_izq",
                "frente_dere": "rot_frente_dere",
                "perfil_dere": "rot_perfil_dere",
                "espalda_dere": "rot_espalda_dere"
            }
            chosen = name_map.get(vf, "idle")
        else:
            name_map = {
                "espalda": "idle_guard",
                "frente": "idle_guard_frente",
                "izq": "idle_guard_izq",
                "dere": "idle_guard_dere",
                "espalda_izq": "rot_espalda_izq",
                "perfil_izq": "idle_guard_rot_perfil_izq",
                "frente_izq": "idle_guard_rot_frente_izq",
                "frente_dere": "idle_guard_rot_frente_dere",
                "perfil_dere": "idle_guard_rot_perfil_dere",
                "espalda_dere": "idle_guard_rot_espalda_dere"
            }

            chosen = name_map.get(vf, "idle_guard")

        if chosen in inst.animator.clips:
            inst.animator.play(chosen)
            return
        
        if inst.guard_mode == True:

            if "idle_guard" in inst.animator.clips:
                inst.animator.play("idle_guard")
                print("IDLE GUARD MODE TRUE")

        else:
            if "idle" in inst.animator.clips:
                inst.animator.play("idle")
            

    def runtime_collides(self, px, py, actor_z, radius=0.18):
        g = self.toolkit.runtime_world.grid

        gx = int(px)
        gy = int(py)

        if gy < 0 or gy >= len(g) or gx < 0 or gx >= len(g[0]):
            return True

        # Revisamos tiles vecinos porque el radio puede tocar paredes cercanas
        for ty in range(max(0, gy-1), min(len(g), gy+2)):
            for tx in range(max(0, gx-1), min(len(g[0]), gx+2)):

                t = g[ty][tx]

                lx = px - tx   # posicion local dentro del tile (0 a 1)
                ly = py - ty

                # -----------------------------------
                # WALL N  (borde norte y = 0)
                # -----------------------------------
                if t.wall_n:
                    if abs(ly - 0.0) < radius and 0 <= lx <= 1:
                        return True

                # -----------------------------------
                # WALL S (borde sur y = 1)
                # -----------------------------------
                if t.wall_s:
                    if abs(ly - 1.0) < radius and 0 <= lx <= 1:
                        return True

                # -----------------------------------
                # WALL W (borde oeste x = 0)
                # -----------------------------------
                if t.wall_w:
                    if abs(lx - 0.0) < radius and 0 <= ly <= 1:
                        return True

                # -----------------------------------
                # WALL E (borde este x = 1)
                # -----------------------------------
                if t.wall_e:
                    if abs(lx - 1.0) < radius and 0 <= ly <= 1:
                        return True

                # -----------------------------------
                # DIAGONAL NE  (de (0,0) a (1,1))
                # ecuacion: y = x
                # -----------------------------------
                if getattr(t, "wall_ne", False):
                    dist = abs(ly - lx) / 1.4142
                    if dist < radius and 0 <= lx <= 1 and 0 <= ly <= 1:
                        return True

                # -----------------------------------
                # DIAGONAL SW  (misma geometria que NE)
                # -----------------------------------
                if getattr(t, "wall_sw", False):
                    dist = abs(ly - lx) / 1.4142
                    if dist < radius and 0 <= lx <= 1 and 0 <= ly <= 1:
                        return True

                # -----------------------------------
                # DIAGONAL NW  (de (1,0) a (0,1))
                # ecuacion: y = 1-x
                # -----------------------------------
                if getattr(t, "wall_nw", False):
                    dist = abs((lx + ly) - 1.0) / 1.4142
                    if dist < radius and 0 <= lx <= 1 and 0 <= ly <= 1:
                        return True

                # -----------------------------------
                # DIAGONAL SE (misma geometria que NW)
                # -----------------------------------
                if getattr(t, "wall_se", False):
                    dist = abs((lx + ly) - 1.0) / 1.4142
                    if dist < radius and 0 <= lx <= 1 and 0 <= ly <= 1:
                        return True

                # -----------------------------------
                # OBJETOS BLOQUEANTES
                # -----------------------------------
                if t.objects:
                    if 0 <= lx <= 1 and 0 <= ly <= 1:
                        return True
                    
                if getattr(t, "is_block", False):
                    if actor_z < (t.block_top - 0.08):
                        if 0 <= lx <= 1 and 0 <= ly <= 1:
                            return True

        return False

    def try_move_runtime_actor(self, pack, dx, dy):

        if self.toolkit.player_input_locked:
            return
        inst = pack["inst"]

        old_gx = pack["gx"]
        old_gy = pack["gy"]

        # ---------------------------------------------
        # posicion mundial actual del actor
        # ---------------------------------------------
        world_x = old_gx + 0.5 + inst.offx
        world_y = old_gy + 0.5 + inst.offy

        # nueva posicion deseada
        new_world_x = world_x + dx
        new_world_y = world_y + dy

        # ---------------------------------------------
        # chequeo de colision geometrica REAL
        # ---------------------------------------------
        blocked = self.runtime_collides(new_world_x, new_world_y, inst.offz, radius=0.28)

        if blocked:
            if self.try_start_mantle(pack, dx, dy):
                return False
            return False

        # ---------------------------------------------
        # recalcular tile contenedor segun nueva posicion
        # ---------------------------------------------
        gx = int(new_world_x)
        gy = int(new_world_y)

        if gx < 0 or gy < 0 or gx >= GRID_W or gy >= GRID_H:
            return

        # ---------------------------------------------
        # recalcular offset local relativo al centro tile
        # ---------------------------------------------
        nx = new_world_x - (gx + 0.5)
        ny = new_world_y - (gy + 0.5)

        # ---------------------------------------------
        # si cambió de tile mover pack de celda runtime
        # ---------------------------------------------
        if gx != old_gx or gy != old_gy:

            old_tile = self.toolkit.runtime_world.grid[old_gy][old_gx]
            new_tile = self.toolkit.runtime_world.grid[gy][gx]

            if pack in old_tile.actors:
                old_tile.actors.remove(pack)

            if pack not in new_tile.actors:
                new_tile.actors.append(pack)

        # ---------------------------------------------
        # guardar nueva posicion
        # ---------------------------------------------
        pack["gx"] = gx
        pack["gy"] = gy

        inst.offx = nx
        inst.offy = ny

        self.check_runtime_fall(pack)

    def check_runtime_fall(self, pack):
        inst = pack["inst"]

        if inst.is_mantling:
            return

        if getattr(inst, "is_falling", False):
            return

        world_x = pack["gx"] + 0.5 + inst.offx
        world_y = pack["gy"] + 0.5 + inst.offy

        gx = int(world_x)
        gy = int(world_y)

        if gx < 0 or gy < 0 or gx >= GRID_W or gy >= GRID_H:
            return

        t = self.toolkit.runtime_world.grid[gy][gx]

        floor_z = t.floor_height

        if getattr(t, "is_block", False):
            floor_z = max(floor_z, t.block_top)

        # si el actor esta mas alto que el suelo actual -> cae
        if inst.ground_z > floor_z + 0.05:
            inst.is_falling = True
            inst.fall_target_z = floor_z
            inst.fall_land_done = False

            if inst.animator and "fall" in inst.animator.clips:
                inst.animator.play("fall")
                inst.animator.frame = 0

    def update_actor_mantle(self, pack, dt):
        inst = pack["inst"]
        print(inst.animator.current, inst.animator.frame, inst.animator.finished)
        # ==========================================
        # PHASE 0 - GIRAR CAMARA
        # ==========================================
        if inst.mantle_phase == 0:
            diff = (inst.target_cam_yaw - self.toolkit.runtime_cam_orbit + 540) % 360 - 180
            self.toolkit.runtime_cam_orbit += diff * min(1, dt * 6)

            if abs(diff) < 3:
                self.toolkit.runtime_cam_orbit = inst.target_cam_yaw
                inst.mantle_timer = 0.0

                if inst.mantle_low:
                    inst.mantle_phase = 3
                else:
                    inst.mantle_phase = 1
            return

        # ==========================================
        # PHASE 1 - JUMP CONTROLADO POR TIMELINE
        # ==========================================
        if inst.mantle_phase == 1:
            speed = 2.8
            inst.mantle_timer += dt # Usa un timer independiente para el movimiento
            if inst.animator.current != "prepare_to_jump":
                inst.animator.play("prepare_to_jump")
            # Dejamos que Animator.update(dt) haga avanzar los frames solo.
            # Solo chequeamos si ya terminó el clip.
            if inst.animator.finished or inst.animator.frame >= len(inst.animator.clips["prepare_to_jump"].frames) - 1:
                inst.animator.play("jump")
                inst.mantle_phase = 2
                inst.mantle_timer = 0.0
                print("prepare to jump -> jump")

            return

        # ==========================================
        # PHASE 2 - SALTO (SUAVIZADO)
        # ==========================================
        if inst.mantle_phase == 2:
            # 1. Definimos una duración deseada para la subida (ej: 0.5 segundos)
            duration = 0.6 
            inst.mantle_timer += dt
            
            # 2. Calculamos el progreso (t va de 0.0 a 1.0)
            t = min(1.0, inst.mantle_timer / duration)
            
            # 3. Aplicamos una función de suavizado (Ease Out) 
            # Esto hace que empiece rápido y termine lento.
            smooth_t = 1 - (1 - t) * (1 - t) 
            
            # 4. Interpolamos entre la altura inicial y la final
            # (Necesitarás guardar inst.start_z al iniciar la Phase 2)
            if not hasattr(inst, 'mantle_start_z'):
                inst.mantle_start_z = inst.offz

            final_salto = inst.mantle_end_z - 1
            print("inst.offz " + str(inst.offz))
            print("final_salto " + str(final_salto))
            if (inst.offz <= final_salto):
                print("subiendo")
                inst.offz = inst.mantle_start_z + (inst.mantle_end_z - inst.mantle_start_z) * smooth_t
            
            # 5. Transición a la siguiente fase cuando el tiempo se agota
            if t >= 1.0:
                inst.offz = inst.mantle_end_z # Aseguramos posición final
                del inst.mantle_start_z       # Limpiamos variable temporal
                inst.mantle_phase = 3
                inst.mantle_timer = 0.0
            return
        # ==========================================
        # PHASE 3 - SUBIR (CLAW + MOVIMIENTO)
        # ==========================================
        if inst.mantle_phase == 3:
            if not getattr(inst, "_claw_started", False):
                inst._claw_started = True
                inst.animator.play("claw")
                if "claw" in inst.animator.clips:
                    inst.animator.play("claw")
                else:
                    inst.mantle_phase = 5 # Si no hay clip, salta al final
                    inst.mantle_timer = 0.0
                    del inst._claw_started
                    return

            inst.mantle_timer += dt
            clip = inst.animator.clips.get("claw")
            fps = getattr(clip, "fps", 6)
            duration = len(clip.frames) / fps
            
            # Progreso normalizado (0.0 a 1.0)
            t = min(1.0, inst.mantle_timer / duration)
            
            # MOVIMIENTO VISUAL (Sin Phase 4, lo hacemos todo aquí)
            wx = inst.mantle_edge_x + (inst.mantle_end_x - inst.mantle_edge_x) * t
            wy = inst.mantle_edge_y + (inst.mantle_end_y - inst.mantle_edge_y) * t
            wz = inst.mantle_hang_z + (inst.mantle_end_z - inst.mantle_hang_z) * t

            inst.offx = wx - (inst.mantle_base_gx + 0.5)
            inst.offy = wy - (inst.mantle_base_gy + 0.5)
            inst.offz = wz

            # Si terminó el tiempo o la animación, saltar directo al ajuste de grilla
            if inst.animator.finished or inst.animator.frame >= len(inst.animator.clips["claw"].frames) - 1:
                inst.mantle_phase = 5 # <--- Directo a Phase 5
                inst.mantle_timer = 0.0
                return

        # ==========================================
        # PHASE 5 - SNAP FINAL (SIN DESLIZAMIENTOS)
        # ==========================================
        if inst.mantle_phase == 5:
            old_gx = pack["gx"]
            old_gy = pack["gy"]

            oldtile = self.toolkit.runtime_world.grid[
                old_gy
            ][
                old_gx
            ]

            if pack in oldtile.actors:
                oldtile.actors.remove(pack)
            # Actualizamos la posición lógica del actor a la celda final
            inst.mantle_base_gx = int(inst.mantle_end_x)
            inst.mantle_base_gy = int(inst.mantle_end_y)
            pack["gx"] = inst.mantle_base_gx
            pack["gy"] = inst.mantle_base_gy

            newtile = self.toolkit.runtime_world.grid[
                pack["gy"]
            ][
                pack["gx"]
            ]

            if pack not in newtile.actors:
                newtile.actors.append(pack)
            
            # Ponemos los offsets en 0 inmediatamente para evitar el deslizamiento de la Phase 6
            inst.offx = 0
            inst.offy = 0
            inst.offz = inst.mantle_end_z
            
            if "walk_espalda" in inst.animator.clips:
                inst.animator.play("walk_espalda")
                
            inst.mantle_phase = 7 # <--- Saltamos la Phase 6 (la del lerp/deslizamiento)
            return

        if inst.mantle_phase == 7:

            inst.is_mantling = False

            inst.ground_z = inst.mantle_end_z
            inst.on_ground = True
            inst.vspeed = 0

            self.toolkit.runtime_camera_locked = False
            self.toolkit.runtime_camera_catchup = True

            inst._claw_started = False
            del inst._claw_started

            if "idle" in inst.animator.clips:
                inst.animator.play("idle")

            return

    def try_start_mantle(self, pack, dx, dy):
        self.toolkit.runtime_camera_locked = True
        inst = pack["inst"]

        if inst.is_mantling:
            return False

        cur_x = pack["gx"] + 0.5 + inst.offx
        cur_y = pack["gy"] + 0.5 + inst.offy

        l = math.sqrt(dx*dx + dy*dy)
        if l == 0:
            return False

        dir_x = dx / l
        dir_y = dy / l

        front_x = cur_x + dir_x * 0.7
        front_y = cur_y + dir_y * 0.7

        tgx = int(front_x)
        tgy = int(front_y)

        if tgx < 0 or tgy < 0 or tgx >= GRID_W or tgy >= GRID_H:
            return False

        t = self.toolkit.runtime_world.grid[tgy][tgx]

        if not getattr(t, "is_block", False):
            return False
        
        current_h = inst.ground_z

        climb_h = t.block_top - current_h

        print(
            "CURRENT H",
            current_h,
            "TARGET TOP",
            t.block_top,
            "CLIMB",
            climb_h
        )


        if climb_h <= 1.2:
            inst.mantle_low = True
        else:
            inst.mantle_low = False

        inst.is_mantling = True
        inst.mantle_phase = 0
        inst.mantle_timer = 0.0

        inst.mantle_base_gx = pack["gx"]
        inst.mantle_base_gy = pack["gy"]

        inst.mantle_start_x = cur_x
        inst.mantle_start_y = cur_y
        inst.mantle_start_z = inst.offz

        inst.mantle_edge_x = tgx + 0.5 - dir_x * 0.78
        inst.mantle_edge_y = tgy + 0.5 - dir_y * 0.78

        inst.mantle_hang_z = t.block_top - 0.15

        inst.mantle_end_x = tgx + 0.5 - dir_x * 0.3
        inst.mantle_end_y = tgy + 0.5 - dir_y * 0.3
        inst.mantle_end_z = t.block_top

        inst.target_cam_yaw = self.mantle_camera_yaw_from_dir(dir_x, dir_y)

        return True
    
    def runtime_get_ground_height(self, world_x, world_y):
        gx = int(world_x)
        gy = int(world_y)

        if gx < 0 or gy < 0 or gx >= GRID_W or gy >= GRID_H:
            return 0.0

        t = self.toolkit.runtime_world.grid[gy][gx]

        best = t.floor_height

        # si hay bloque y el actor está sobre la superficie superior
        if getattr(t, "is_block", False):
            if t.block_top > best:
                best = t.block_top

        return best
    
    def update_runtime_actor_vertical(self, pack, dt):
        inst = pack["inst"]

        if inst.is_mantling:
            return

        wx = pack["gx"] + 0.5 + inst.offx
        wy = pack["gy"] + 0.5 + inst.offy

        inst.ground_z = self.runtime_get_ground_height(wx, wy)

        gravity = 7.0

        inst.was_on_ground = inst.on_ground

        if inst.offz > inst.ground_z + 0.02:
            inst.vspeed -= gravity * dt
            inst.offz += inst.vspeed * dt
            inst.on_ground = False

            if not inst.was_on_ground:
                pass
            else:
                if inst.animator and "fall" in inst.animator.clips:
                    inst.animator.play("fall")

            if inst.offz <= inst.ground_z:
                inst.offz = inst.ground_z
                inst.vspeed = 0
                inst.on_ground = True

        else:
            inst.offz = inst.ground_z
            inst.vspeed = 0
            inst.on_ground = True

    def runtime_can_climb_column(self, gx, gy):
        if gx < 0 or gy < 0 or gx >= GRID_W or gy >= GRID_H:
            return None

        t = self.toolkit.runtime_world.grid[gy][gx]

        if not getattr(t, "is_column", False):
            return None

        h = max(t.wall_n_height, t.wall_s_height, t.wall_e_height, t.wall_w_height)

        if h > 2.05:
            return None

        return {
            "height": h,
            "top_z": t.block_top
        }
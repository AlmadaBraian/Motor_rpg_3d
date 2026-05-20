import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from SpriteManager import *
import config

class SpriteAnimatorEditor:
    def __init__(self, toolkit, sprite_asset):
        self.toolkit = toolkit
        self.sprite = sprite_asset
        self.crop_mode = False

        self.selected_frames = []
        self.selected_key = None

        self.preview_frame = 0
        self.preview_playing = True
        self.preview_tick = 0
        self.after_id = None

        self.grid_overlays = []

        self.crop_rect_id = None
        self.crop_dragging = False
        self.crop_start_x = 0
        self.crop_start_y = 0

        self.project_dir = config.base_path

        self.prop_cropx = tk.IntVar(value=0)
        self.prop_cropy = tk.IntVar(value=0)
        self.prop_cropw = tk.IntVar(value=self.sprite.frame_w)
        self.prop_croph = tk.IntVar(value=self.sprite.frame_h)

        self.prop_flipx = tk.BooleanVar(value=False)
        self.prop_rot = tk.IntVar(value=0)

        self.win = tk.Toplevel()
        self.win.title("Sprite Animator PRO V2")
        self.win.protocol("WM_DELETE_WINDOW", self.on_close)

        # ---------------- LAYOUT ----------------

        top = tk.Frame(self.win)
        top.pack(fill='both', expand=True)

        bottom = tk.LabelFrame(self.win, text="Keyframe Properties")
        bottom.pack(fill='x', padx=5, pady=5)

        left = tk.Frame(top)
        left.pack(side='left', padx=5)

        center = tk.Frame(top)
        center.pack(side='left', padx=10)

        right = tk.Frame(top)
        right.pack(side='right', fill='y', padx=5)

        # ---------------- SPRITESHEET ----------------

        full_img_path = os.path.join(self.project_dir, sprite_asset.image_path.lstrip("/"))
        full_img_path = os.path.normpath(full_img_path)

        self.sheet_img = Image.open(full_img_path).convert("RGBA")
        self.tkimg = ImageTk.PhotoImage(self.sheet_img)

        self.canvas = tk.Canvas(left, width=self.sheet_img.width, height=self.sheet_img.height)
        self.canvas.pack()
        self.canvas.create_image(0,0,image=self.tkimg,anchor='nw')
        self.canvas.bind("<Button-1>", self.sheet_mouse_down)
        self.canvas.bind("<B1-Motion>", self.sheet_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.sheet_mouse_up)

        self.draw_grid()

        # ---------------- PREVIEW ----------------

        tk.Label(center, text="Animation Preview").pack()
        self.preview_canvas = tk.Canvas(center, width=300, height=300, bg='black')
        self.preview_canvas.pack()

        # ---------------- RIGHT PANEL ----------------

        tk.Label(right, text='Clip Name').pack()
        self.clip_name = tk.Entry(right)
        self.clip_name.insert(0,"")
        self.clip_name.pack(fill='x')

        self.crop_btn = tk.Button(bottom, text="Crop Mode OFF", command=self.toggle_crop_mode)
        self.crop_btn.pack(pady=4)

        tk.Label(right, text='FPS').pack()
        self.fps_var = tk.IntVar(value=6)
        tk.Spinbox(right, from_=1, to=30, textvariable=self.fps_var).pack(fill='x')

        self.loop_var = tk.BooleanVar(value=True)
        tk.Checkbutton(right, text='Loop', variable=self.loop_var).pack()

        tk.Button(right,text='Play',command=self.play_preview).pack(fill='x')
        tk.Button(right,text='Stop',command=self.stop_preview).pack(fill='x')

        tk.Button(right,text='Save Clip',command=self.save_clip).pack(fill='x')
        tk.Button(right,text='Load Clip',command=self.load_clip).pack(fill='x')
        tk.Button(right,text='Delete Clip',command=self.delete_clip).pack(fill='x')

        tk.Button(right, text='Refresh Sprites In Map', command=self.refresh_world_animators).pack(fill='x')
        

        tk.Label(right,text='Saved Clips').pack()
        self.clip_list = tk.Listbox(right,height=6)
        self.clip_list.pack(fill='x')

        tk.Label(right,text='Timeline').pack()
        self.keyframe_list = tk.Listbox(right,height=10)
        self.keyframe_list.pack(fill='x')
        self.keyframe_list.bind("<<ListboxSelect>>", self.select_keyframe)

        tk.Button(right,text='Move Up',command=self.move_key_up).pack(fill='x')
        tk.Button(right,text='Move Down',command=self.move_key_down).pack(fill='x')
        tk.Button(right,text='Delete Keyframe',command=self.delete_keyframe).pack(fill='x')
        tk.Button(right,text='Clear All',command=self.clear_frames).pack(fill='x')

        # ---------------- KEYFRAME PROPERTY EDITOR ----------------

        self.prop_w = tk.IntVar(value=self.sprite.frame_w)
        self.prop_h = tk.IntVar(value=self.sprite.frame_h)
        self.prop_ox = tk.IntVar(value=0)
        self.prop_oy = tk.IntVar(value=0)
        self.prop_dur = tk.IntVar(value=1)
        self.prop_cropx = tk.IntVar(value=0)
        self.prop_cropy = tk.IntVar(value=0)
        self.prop_cropw = tk.IntVar(value=self.sprite.frame_w)
        self.prop_croph = tk.IntVar(value=self.sprite.frame_h)

        row1 = tk.Frame(bottom); row1.pack(fill='x')
        row2 = tk.Frame(bottom); row2.pack(fill='x')
        row3 = tk.Frame(bottom); row3.pack(fill='x')

        row4 = tk.Frame(bottom); row4.pack(fill='x')

        tk.Checkbutton(row4, text="Flip Horizontal", variable=self.prop_flipx).pack(side='left')

        tk.Label(row4, text="Rotation").pack(side='left', padx=(10,0))

        self.rot_slider = tk.Scale(
            row4,
            from_=-360,
            to=360,
            orient='horizontal',
            variable=self.prop_rot,
            length=140
        )
        self.rot_slider.pack(side='left')

        tk.Button(row4, text="-90", command=lambda:self.nudge_rotation(-90)).pack(side='left')
        tk.Button(row4, text="+90", command=lambda:self.nudge_rotation(90)).pack(side='left')

        tk.Label(row1,text="Width").pack(side='left')
        tk.Entry(row1,textvariable=self.prop_w,width=6).pack(side='left')

        tk.Label(row1,text="Height").pack(side='left')
        tk.Entry(row1,textvariable=self.prop_h,width=6).pack(side='left')

        tk.Label(row1,text="Offset X").pack(side='left')
        tk.Entry(row1,textvariable=self.prop_ox,width=6).pack(side='left')

        tk.Label(row1,text="Offset Y").pack(side='left')
        tk.Entry(row1,textvariable=self.prop_oy,width=6).pack(side='left')

        tk.Label(row2,text="Crop X").pack(side='left')
        tk.Entry(row2,textvariable=self.prop_cropx,width=6).pack(side='left')

        tk.Label(row2,text="Crop Y").pack(side='left')
        tk.Entry(row2,textvariable=self.prop_cropy,width=6).pack(side='left')

        tk.Label(row2,text="Crop W").pack(side='left')
        tk.Entry(row2,textvariable=self.prop_cropw,width=6).pack(side='left')

        tk.Label(row2,text="Crop H").pack(side='left')
        tk.Entry(row2,textvariable=self.prop_croph,width=6).pack(side='left')

        tk.Label(row3,text="Duration").pack(side='left')
        tk.Entry(row3,textvariable=self.prop_dur,width=6).pack(side='left')

        tk.Button(row3,text="Apply To Selected Keyframe",command=self.apply_keyframe_changes).pack(side='left', padx=10)

        self.refresh_clip_list()
        self.animate_preview()

    def refresh_world_animators(self):
        updated = 0

        for y in range(len(self.toolkit.grid)):
            for x in range(len(self.toolkit.grid[y])):
                t = self.toolkit.grid[y][x]

                if not hasattr(t, "sprites"):
                    continue

                for inst in t.sprites:
                    if inst.asset != self.sprite.name:
                        continue

                    if not hasattr(inst, "animator") or inst.animator is None:
                        inst.animator = Animator(self.sprite.base_clips)
                    else:
                        current_anim = inst.animator.current
                        current_frame = inst.animator.frame
                        current_timer = inst.animator.timer

                        inst.animator = Animator(self.sprite.base_clips)

                        if current_anim in inst.animator.clips:
                            inst.animator.current = current_anim
                            inst.animator.frame = min(current_frame, len(inst.animator.clips[current_anim].frames)-1)
                            inst.animator.timer = current_timer
                        elif self.sprite.base_clips:
                            inst.animator.play(self.sprite.base_clips[0].name)

                    updated += 1

        print("UPDATED WORLD SPRITES:", updated)

    def nudge_rotation(self, amount):
        val = (self.prop_rot.get() + amount) % 360
        self.prop_rot.set(val)

    def toggle_crop_mode(self):
        self.crop_mode = not self.crop_mode

        if self.crop_mode:
            self.crop_btn.config(text="Crop Mode ON", bg="orange")
        else:
            self.crop_btn.config(text="Crop Mode OFF", bg="SystemButtonFace")

    # =========================================================
    # SHEET MOUSE INTERACTION
    # =========================================================

    def sheet_mouse_down(self, event):
        if not self.crop_mode:
            self.pick_frame(event)
            return

        if self.selected_key is None:
            return

        meta = self.selected_frames[self.selected_key]

        cols = max(1, self.sprite.sheet_cols)
        cw = self.sheet_img.width // cols
        ch = self.sheet_img.height // max(1, self.sprite.sheet_rows)

        frame = meta["frame"]
        fx = frame % cols
        fy = frame // cols

        base_x = fx * cw
        base_y = fy * ch

        local_x = event.x - base_x
        local_y = event.y - base_y

        if 0 <= local_x < cw and 0 <= local_y < ch:
            self.crop_dragging = True
            self.crop_start_x = max(0, local_x)
            self.crop_start_y = max(0, local_y)

    def sheet_mouse_drag(self, event):
        if not self.crop_dragging:
            return

        if self.selected_key is None:
            return

        meta = self.selected_frames[self.selected_key]

        cols = max(1, self.sprite.sheet_cols)
        cw = self.sheet_img.width // cols
        ch = self.sheet_img.height // max(1, self.sprite.sheet_rows)

        frame = meta["frame"]
        fx = frame % cols
        fy = frame // cols

        base_x = fx * cw
        base_y = fy * ch

        local_x = max(0, min(cw, event.x - base_x))
        local_y = max(0, min(ch, event.y - base_y))

        x0 = min(self.crop_start_x, local_x)
        y0 = min(self.crop_start_y, local_y)
        x1 = max(self.crop_start_x, local_x)
        y1 = max(self.crop_start_y, local_y)

        meta["crop_x"] = int(x0)
        meta["crop_y"] = int(y0)
        meta["crop_w"] = max(1, int(x1 - x0))
        meta["crop_h"] = max(1, int(y1 - y0))

        self.load_keyframe_properties()
        self.redraw_selection_overlay()

    def sheet_mouse_up(self, event):
        self.crop_dragging = False
    
    # =========================================================
    # BASIC CONTROL
    # =========================================================

    def on_close(self):
        if self.after_id:
            self.win.after_cancel(self.after_id)
        self.win.destroy()

    def safe_get_fps(self):
        try:
            return max(1, int(self.fps_var.get()))
        except:
            return 1

    def play_preview(self):
        self.preview_playing = True

    def stop_preview(self):
        self.preview_playing = False

    # =========================================================
    # GRID DRAW
    # =========================================================

    def draw_grid(self):
        cols = max(1, self.sprite.sheet_cols)
        rows = max(1, self.sprite.sheet_rows)

        cw = self.sheet_img.width // cols
        ch = self.sheet_img.height // rows

        for x in range(cols + 1):
            self.canvas.create_line(x*cw, 0, x*cw, self.sheet_img.height, fill='red')

        for y in range(rows + 1):
            self.canvas.create_line(0, y*ch, self.sheet_img.width, y*ch, fill='red')

    def redraw_selection_overlay(self):
        for item in self.grid_overlays:
            self.canvas.delete(item)
        self.grid_overlays.clear()

        cols = max(1, self.sprite.sheet_cols)
        rows = max(1, self.sprite.sheet_rows)

        cw = self.sheet_img.width // cols
        ch = self.sheet_img.height // rows

        for i, meta in enumerate(self.selected_frames):
            frame = meta["frame"]
            fx = frame % cols
            fy = frame // cols

            color = "yellow" if i == self.preview_frame else "lime"
            if self.selected_key == i:
                color = "cyan"

            rect = self.canvas.create_rectangle(
                fx*cw, fy*ch,
                fx*cw+cw, fy*ch+ch,
                outline=color,
                width=3
            )
            self.grid_overlays.append(rect)

        if self.selected_key is not None and self.selected_key < len(self.selected_frames):
            meta = self.selected_frames[self.selected_key]

            frame = meta["frame"]
            fx = frame % cols
            fy = frame // cols

            cx = fx*cw + meta.get("crop_x",0)
            cy = fy*ch + meta.get("crop_y",0)
            cw2 = meta.get("crop_w",cw)
            ch2 = meta.get("crop_h",ch)

            crop_rect = self.canvas.create_rectangle(
                cx, cy,
                cx+cw2, cy+ch2,
                outline="orange",
                width=2
            )
            self.grid_overlays.append(crop_rect)

    # =========================================================
    # PICK FRAME -> CREATE KEYFRAME
    # =========================================================

    def pick_frame(self, event):
        cols = max(1, self.sprite.sheet_cols)
        rows = max(1, self.sprite.sheet_rows)

        cw = self.sheet_img.width // cols
        ch = self.sheet_img.height // rows

        gx = event.x // cw
        gy = event.y // ch

        if gx < 0 or gy < 0 or gx >= cols or gy >= rows:
            return

        frame = gy * cols + gx

        key = {
            "frame": frame,

            "crop_x": 0,
            "crop_y": 0,
            "crop_w": self.sprite.frame_w,
            "crop_h": self.sprite.frame_h,

            "w": self.sprite.frame_w,
            "h": self.sprite.frame_h,

            "ox": 0,
            "oy": 0,
            "dur": 1,
            "flip_x": False,
            "rot": 0
        }

        self.selected_frames.append(key)
        self.selected_key = len(self.selected_frames) - 1

        self.refresh_keyframe_list()
        self.load_keyframe_properties()
        self.redraw_selection_overlay()

    # =========================================================
    # TIMELINE LIST
    # =========================================================

    def refresh_keyframe_list(self):
        self.keyframe_list.delete(0, 'end')

        for i, meta in enumerate(self.selected_frames):
            txt = f"{i}: frame {meta['frame']} | {meta['w']}x{meta['h']} | ox:{meta['ox']} oy:{meta['oy']} | dur:{meta['dur']}"
            self.keyframe_list.insert('end', txt)

        if self.selected_key is not None and self.selected_key < len(self.selected_frames):
            self.keyframe_list.selection_set(self.selected_key)

    def select_keyframe(self, event=None):
        sel = self.keyframe_list.curselection()
        if not sel:
            return

        self.selected_key = sel[0]
        self.load_keyframe_properties()
        self.redraw_selection_overlay()

    def load_keyframe_properties(self):
        if self.selected_key is None:
            return
        if self.selected_key >= len(self.selected_frames):
            return

        meta = self.selected_frames[self.selected_key]

        self.prop_w.set(meta["w"])
        self.prop_h.set(meta["h"])
        self.prop_ox.set(meta["ox"])
        self.prop_oy.set(meta["oy"])
        self.prop_dur.set(meta["dur"])

        self.prop_cropx.set(meta.get("crop_x",0))
        self.prop_cropy.set(meta.get("crop_y",0))
        self.prop_cropw.set(meta.get("crop_w",self.sprite.frame_w))
        self.prop_croph.set(meta.get("crop_h",self.sprite.frame_h))
        self.prop_flipx.set(meta.get("flip_x", False))
        self.prop_rot.set(meta.get("rot", 0))

    def apply_keyframe_changes(self):
        if self.selected_key is None:
            return
        if self.selected_key >= len(self.selected_frames):
            return

        meta = self.selected_frames[self.selected_key]

        try:
            meta["w"] = max(1, int(self.prop_w.get()))
            meta["h"] = max(1, int(self.prop_h.get()))
            meta["ox"] = int(self.prop_ox.get())
            meta["oy"] = int(self.prop_oy.get())
            meta["dur"] = max(1, int(self.prop_dur.get()))

            meta["crop_x"] = max(0, int(self.prop_cropx.get()))
            meta["crop_y"] = max(0, int(self.prop_cropy.get()))
            meta["crop_w"] = max(1, int(self.prop_cropw.get()))
            meta["crop_h"] = max(1, int(self.prop_croph.get()))
            meta["flip_x"] = self.prop_flipx.get()
            meta["rot"] = int(self.prop_rot.get())

        except:
            messagebox.showerror("Error", "Invalid keyframe values.")
            return

        self.refresh_keyframe_list()
        self.redraw_selection_overlay()
        self.crop_mode = False
        self.crop_btn.config(text="Crop Mode OFF", bg="SystemButtonFace")

    # =========================================================
    # KEYFRAME ORDER
    # =========================================================

    def move_key_up(self):
        if self.selected_key is None or self.selected_key <= 0:
            return

        i = self.selected_key
        self.selected_frames[i], self.selected_frames[i-1] = self.selected_frames[i-1], self.selected_frames[i]
        self.selected_key -= 1

        self.refresh_keyframe_list()
        self.redraw_selection_overlay()

    def move_key_down(self):
        if self.selected_key is None:
            return
        if self.selected_key >= len(self.selected_frames)-1:
            return

        i = self.selected_key
        self.selected_frames[i], self.selected_frames[i+1] = self.selected_frames[i+1], self.selected_frames[i]
        self.selected_key += 1

        self.refresh_keyframe_list()
        self.redraw_selection_overlay()

    def delete_keyframe(self):
        if self.selected_key is None:
            return

        if self.selected_key < len(self.selected_frames):
            del self.selected_frames[self.selected_key]

        if not self.selected_frames:
            self.selected_key = None
        else:
            self.selected_key = min(self.selected_key, len(self.selected_frames)-1)

        self.refresh_keyframe_list()
        self.redraw_selection_overlay()

    def clear_frames(self):
        self.selected_frames.clear()
        self.selected_key = None
        self.preview_frame = 0

        self.refresh_keyframe_list()
        self.redraw_selection_overlay()

    # =========================================================
    # CLIP SAVE/LOAD
    # =========================================================

    def save_clip(self):
        name = self.clip_name.get().strip()

        if not name:
            messagebox.showwarning("Warning", "Clip needs a name.")
            return

        if not self.selected_frames:
            messagebox.showwarning("Warning", "No keyframes.")
            return

        clip = AnimationClip(
            name,
            [dict(x) for x in self.selected_frames],
            fps=self.safe_get_fps(),
            loop=self.loop_var.get()
        )

        replaced = False
        for i, c in enumerate(self.sprite.base_clips):
            if c.name == name:
                self.sprite.base_clips[i] = clip
                replaced = True
                break

        if not replaced:
            self.sprite.base_clips.append(clip)

        self.refresh_clip_list()
        self.toolkit.save_sprite_library()
        self.refresh_world_animators()

    def refresh_world_animators(self):
        updated = 0

        for y in range(len(self.toolkit.grid)):
            for x in range(len(self.toolkit.grid[y])):
                t = self.toolkit.grid[y][x]

                if not hasattr(t, "sprites"):
                    continue

                for inst in t.sprites:
                    if inst.asset != self.sprite.name:
                        continue

                    old_anim = None
                    old_frame = 0
                    old_timer = 0

                    if hasattr(inst, "animator") and inst.animator:
                        old_anim = inst.animator.current
                        old_frame = inst.animator.frame
                        old_timer = inst.animator.timer

                    inst.animator = Animator(self.sprite.base_clips)

                    if old_anim and old_anim in inst.animator.clips:
                        inst.animator.current = old_anim

                        if inst.animator.clips[old_anim].frames:
                            inst.animator.frame = min(
                                old_frame,
                                len(inst.animator.clips[old_anim].frames)-1
                            )
                        else:
                            inst.animator.frame = 0

                        inst.animator.timer = old_timer

                    elif self.sprite.base_clips:
                        inst.animator.play(self.sprite.base_clips[0].name)

                    updated += 1

        # ============================================
        # refrescar sprite seleccionado en panel
        # ============================================

        if hasattr(self.toolkit, "selected_sprite") and self.toolkit.selected_sprite:
            if self.toolkit.selected_sprite.asset == self.sprite.name:
                self.toolkit.load_sprite_into_panel(
                    self.toolkit.selected_sprite,
                    self.toolkit.selected_sprite_gx,
                    self.toolkit.selected_sprite_gy
                )

        print("FULL WORLD SPRITE REFRESH:", updated)

    def load_clip(self):
        sel = self.clip_list.curselection()
        if not sel:
            return

        clip = self.sprite.base_clips[sel[0]]

        self.clip_name.delete(0, 'end')
        self.clip_name.insert(0, clip.name)

        self.fps_var.set(max(1, clip.fps))
        self.loop_var.set(clip.loop)

        self.selected_frames = [dict(x) for x in clip.frames]
        self.selected_key = 0 if self.selected_frames else None

        self.preview_frame = 0
        self.preview_tick = 0
        self.preview_playing = True

        self.refresh_keyframe_list()
        self.load_keyframe_properties()
        self.redraw_selection_overlay()

    def delete_clip(self):
        sel = self.clip_list.curselection()
        if not sel:
            return

        del self.sprite.base_clips[sel[0]]
        self.refresh_clip_list()
        self.toolkit.save_sprite_library()

    def refresh_clip_list(self):
        self.clip_list.delete(0, 'end')
        for c in self.sprite.base_clips:
            self.clip_list.insert('end', c.name)

    # =========================================================
    # PREVIEW ENGINE
    # =========================================================

    def animate_preview(self):
        if not self.win.winfo_exists():
            return

        self.preview_canvas.delete("all")

        # suelo de referencia
        self.preview_canvas.create_line(0, 240, 300, 240, fill="gray")

        if self.selected_frames:
            self.preview_frame = min(self.preview_frame, len(self.selected_frames)-1)

            meta = self.selected_frames[self.preview_frame]

            frame = meta["frame"]
            draw_w = meta["w"]
            draw_h = meta["h"]
            ox = meta["ox"]
            oy = meta["oy"]
            dur = meta["dur"]

            cols = max(1, self.sprite.sheet_cols)

            cw = self.sheet_img.width // cols
            ch = self.sheet_img.height // max(1, self.sprite.sheet_rows)

            fx = frame % cols
            fy = frame // cols

            crop_x = meta.get("crop_x",0)
            crop_y = meta.get("crop_y",0)
            crop_w = meta.get("crop_w",cw)
            crop_h = meta.get("crop_h",ch)

            crop = self.sheet_img.crop((
                fx*cw + crop_x,
                fy*ch + crop_y,
                fx*cw + crop_x + crop_w,
                fy*ch + crop_y + crop_h
            ))

            if meta.get("flip_x", False):
                crop = crop.transpose(Image.FLIP_LEFT_RIGHT)

            rot = meta.get("rot", 0)
            if rot != 0:
                crop = crop.rotate(-rot, expand=True)

            crop = crop.resize((draw_w*2, draw_h*2), Image.NEAREST)
            self.prev_imgtk = ImageTk.PhotoImage(crop)

            base_x = 150 + ox
            base_y = 240 + oy - (draw_h)

            self.preview_canvas.create_image(base_x, base_y, image=self.prev_imgtk)

            self.redraw_selection_overlay()

            if self.preview_playing:
                self.preview_tick += 1

                if self.preview_tick >= dur:
                    self.preview_tick = 0
                    self.preview_frame += 1

                    if self.preview_frame >= len(self.selected_frames):
                        if self.loop_var.get():
                            self.preview_frame = 0
                        else:
                            self.preview_frame = len(self.selected_frames)-1

        delay = int(1000 / self.safe_get_fps())
        self.after_id = self.win.after(delay, self.animate_preview)
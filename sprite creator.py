import os
import json
import math

try:
    from PIL import Image, ImageDraw
except ImportError:
    import sys
    print("ERROR: Pillow no está instalado.")
    print(f"Usá: {sys.executable} -m pip install pillow")
    exit(1)

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    TK_AVAILABLE = True
except ImportError:
    TK_AVAILABLE = False

# =========================
# HELPERS
# =========================

def next_power_of_two(n):
    return 1 if n == 0 else 2 ** math.ceil(math.log2(n))


def clamp_power_of_two(n, max_size=1080):
    return min(next_power_of_two(n), max_size)


class SpriteSheetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sprite Sheet Generator PRO")

        self.images = []
        self.preview_frames = []
        self.all_frames = []
        self.sequence_indices = []  # orden personalizado

        self.current_frame = 0
        self.playing = False
        self.fps = 10
        self.selected_row = 0
        self.cols = 4
        self.rows = 0
        self.cell_w = 0
        self.cell_h = 0

        self.drag_start_y = None

        ctrl = tk.Frame(root)
        ctrl.pack()

        tk.Button(ctrl, text="Cargar Frames", command=self.load_images).grid(row=0, column=0)
        tk.Button(ctrl, text="Cargar Sheet", command=self.load_sheet).grid(row=0, column=1)
        tk.Button(ctrl, text="Generar", command=self.generate_sheet).grid(row=0, column=2)
        tk.Button(ctrl, text="Guardar PNG", command=self.save_sheet).grid(row=0, column=3)
        tk.Button(ctrl, text="Play", command=self.toggle_animation).grid(row=0, column=4)

        tk.Label(ctrl, text="FPS").grid(row=1, column=0)
        self.fps_input = tk.Entry(ctrl, width=5)
        self.fps_input.insert(0, "10")
        self.fps_input.grid(row=1, column=1)

        tk.Label(ctrl, text="Cols").grid(row=1, column=2)
        self.cols_input = tk.Entry(ctrl, width=5)
        self.cols_input.insert(0, "4")
        self.cols_input.grid(row=1, column=3)

        tk.Label(ctrl, text="Rows").grid(row=1, column=4)
        self.rows_input = tk.Entry(ctrl, width=5)
        self.rows_input.insert(0, "1")
        self.rows_input.grid(row=1, column=5)

        tk.Label(ctrl, text="Fila").grid(row=1, column=6)
        self.row_var = tk.IntVar(value=0)
        self.row_menu = tk.OptionMenu(ctrl, self.row_var, 0)
        self.row_menu.grid(row=1, column=7)
        self.row_var.trace_add("write", lambda *args: self.on_row_change())

        tk.Label(ctrl, text="Row H").grid(row=2, column=0)
        self.row_height_input = tk.Entry(ctrl, width=5)
        self.row_height_input.insert(0, "0")
        self.row_height_input.grid(row=2, column=1)

        tk.Label(ctrl, text="Row W").grid(row=2, column=2)
        self.row_widht_input = tk.Entry(ctrl, width=5)
        self.row_widht_input.insert(0, "0")
        self.row_widht_input.grid(row=2, column=3)

        container = tk.Frame(root)
        container.pack()

        self.canvas_sheet = tk.Canvas(container, width=512, height=512, bg="black")
        self.canvas_sheet.grid(row=0, column=0)

        self.canvas_anim = tk.Canvas(container, width=512, height=512, bg="gray20")
        self.canvas_anim.grid(row=0, column=1)

        # Panel de secuencia (derecha extra)
        seq_panel = tk.Frame(container)
        seq_panel.grid(row=0, column=2, sticky="ns")

        tk.Label(seq_panel, text="Secuencia").pack()
        self.sequence_list = tk.Listbox(seq_panel, height=20)
        self.sequence_list.pack()

        tk.Button(seq_panel, text="↑", command=self.move_up).pack(fill="x")
        tk.Button(seq_panel, text="↓", command=self.move_down).pack(fill="x")
        tk.Button(seq_panel, text="Eliminar", command=self.remove_selected).pack(fill="x")
        tk.Button(seq_panel, text="Limpiar", command=self.clear_sequence).pack(fill="x")

        self.canvas_sheet.bind("<Button-1>", self.on_click_sheet)
        self.canvas_sheet.bind("<B1-Motion>", self.on_drag)
        self.canvas_sheet.bind("<ButtonRelease-1>", self.on_release)

        self.sheet = None
        self.tk_refs = []

    # =========================
    # LOADERS
    # =========================

    def load_images(self):
        paths = filedialog.askopenfilenames(filetypes=[("Images", "*.png;*.jpg")])
        if not paths:
            return
        self.images = [Image.open(p).convert("RGBA") for p in paths]
        messagebox.showinfo("OK", f"{len(self.images)} frames cargados")

    def load_sheet(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg")])
        if not path:
            return

        self.sheet = Image.open(path).convert("RGBA")

        try:
            self.cols = int(self.cols_input.get())
            self.rows = int(self.rows_input.get())
        except:
            messagebox.showerror("Error", "Cols/Rows inválidos")
            return

        self.slice_sheet()
        self.update_row_menu()
        self.apply_row_filter()
        self.display_sheet()
        self.display_first_frame()

    def slice_sheet(self):
        self.all_frames = []
        w, h = self.sheet.size
        #self.cell_w = w // self.cols

        try:
            manual_h = int(self.row_height_input.get())
        except:
            manual_h = 0

        self.cell_h = manual_h if manual_h > 0 else h // self.rows

        try:
            manual_w = int(self.row_widht_input.get())
        except:
            manual_w = 0

        self.cell_w = manual_w if manual_w > 0 else w // self.cols

        for r in range(self.rows):
            y = r * self.cell_h
            if y >= h:
                break
            for c in range(self.cols):
                x = c * self.cell_w
                frame = self.sheet.crop((x, y, x + self.cell_w, y + self.cell_h))
                self.all_frames.append(frame)

    def save_sheet(self):
        if not self.sheet:
            messagebox.showerror("Error", "No hay sprite sheet")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png")
        if path:
            self.sheet.save(path)

    # =========================
    # GENERATE
    # =========================

    def generate_sheet(self):
        if not self.images:
            return

        self.all_frames = []
        self.preview_frames = []

        max_w = max(img.width for img in self.images)
        max_h = max(img.height for img in self.images)
        self.cell_w, self.cell_h = max_w, max_h

        self.cols = 4
        self.rows = (len(self.images) + self.cols - 1) // self.cols

        sheet_w = clamp_power_of_two(self.cols * max_w)
        sheet_h = clamp_power_of_two(self.rows * max_h)

        self.sheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(self.sheet)

        for i, img in enumerate(self.images):
            x = (i % self.cols) * max_w
            y = (i // self.cols) * max_h

            if x + max_w > sheet_w or y + max_h > sheet_h:
                continue

            self.sheet.paste(img, (x, y))
            draw.rectangle([x, y, x + max_w, y + max_h], outline="red")
            self.all_frames.append(img)

        self.update_row_menu()
        self.apply_row_filter()
        self.display_sheet()
        self.display_first_frame()

    # =========================
    # INTERACCIÓN
    # =========================

    def on_click_sheet(self, event):
        if not self.sheet or self.cell_h == 0:
            return

        canvas_h = int(self.canvas_sheet["height"])
        canvas_w = int(self.canvas_sheet["width"])

        scale_y = self.sheet.height / canvas_h
        scale_x = self.sheet.width / canvas_w

        y = int(event.y * scale_y)
        x = int(event.x * scale_x)

        row = y // self.cell_h
        col = x // self.cell_w

        index = row * self.cols + col

        if 0 <= index < len(self.all_frames):
            self.sequence_indices.append(index)
            self.sequence_list.insert(tk.END, f"Frame {index}")

        self.row_var.set(row)
        self.drag_start_y = y

    def on_drag(self, event):
        if self.drag_start_y is None or not self.sheet:
            return

        canvas_h = int(self.canvas_sheet["height"])
        scale = self.sheet.height / canvas_h
        y = int(event.y * scale)

        height = abs(y - self.drag_start_y)
        if height > 5:
            self.row_height_input.delete(0, tk.END)
            self.row_height_input.insert(0, str(height))

    def on_release(self, event):
        self.drag_start_y = None

    # =========================
    # SECUENCIA
    # =========================

    def move_up(self):
        i = self.sequence_list.curselection()
        if not i:
            return
        i = i[0]
        if i == 0:
            return
        self.sequence_indices[i], self.sequence_indices[i-1] = self.sequence_indices[i-1], self.sequence_indices[i]
        self.refresh_sequence()

    def move_down(self):
        i = self.sequence_list.curselection()
        if not i:
            return
        i = i[0]
        if i >= len(self.sequence_indices)-1:
            return
        self.sequence_indices[i], self.sequence_indices[i+1] = self.sequence_indices[i+1], self.sequence_indices[i]
        self.refresh_sequence()

    def remove_selected(self):
        i = self.sequence_list.curselection()
        if not i:
            return
        i = i[0]
        self.sequence_indices.pop(i)
        self.refresh_sequence()

    def clear_sequence(self):
        self.sequence_indices = []
        self.refresh_sequence()

    def refresh_sequence(self):
        self.sequence_list.delete(0, tk.END)
        for idx in self.sequence_indices:
            self.sequence_list.insert(tk.END, f"Frame {idx}")

    # =========================
    # UI
    # =========================

    def update_row_menu(self):
        menu = self.row_menu["menu"]
        menu.delete(0, "end")

        for i in range(self.rows):
            menu.add_command(label=str(i), command=lambda v=i: self.row_var.set(v))

        self.row_var.set(0)

    def on_row_change(self):
        self.apply_row_filter()
        self.display_sheet()
        self.display_first_frame()

    def apply_row_filter(self):
        self.selected_row = self.row_var.get()
        start = self.selected_row * self.cols
        end = start + self.cols
        self.preview_frames = self.all_frames[start:end]

    # =========================
    # RENDER
    # =========================

    def display_sheet(self):
        if not self.sheet:
            return

        img = self.sheet.copy()
        draw = ImageDraw.Draw(img)

        y1 = self.selected_row * self.cell_h
        y2 = (self.selected_row + 1) * self.cell_h - 1

        if y2 > img.height:
            y2 = img.height - 1

        draw.rectangle([0, y1, img.width, y2], outline="yellow", width=3)

        self._draw(img, self.canvas_sheet)

    def display_first_frame(self):
        if not self.preview_frames:
            return
        self._draw(self.preview_frames[0], self.canvas_anim)

    def _draw(self, img, canvas):
        from PIL import ImageTk

        canvas_w = int(canvas["width"])
        canvas_h = int(canvas["height"])

        scale = min(canvas_w / img.width, canvas_h / img.height)
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.NEAREST)

        tk_img = ImageTk.PhotoImage(img)
        self.tk_refs.append(tk_img)

        canvas.delete("all")
        canvas.create_image(canvas_w // 2, canvas_h // 2, image=tk_img)

    # =========================
    # ANIMACIÓN
    # =========================

    def toggle_animation(self):
        if self.sequence_indices:
            frames = [self.all_frames[i] for i in self.sequence_indices]
        else:
            frames = self.preview_frames

        if not frames:
            return

        try:
            self.fps = int(self.fps_input.get())
        except:
            self.fps = 10

        self.anim_frames = frames
        self.current_frame = 0
        self.playing = not self.playing
        if self.playing:
            self.animate()

    def animate(self):
        if not self.playing:
            return

        frame = self.anim_frames[self.current_frame]
        self._draw(frame, self.canvas_anim)

        self.current_frame = (self.current_frame + 1) % len(self.anim_frames)
        self.root.after(int(1000 / max(1, self.fps)), self.animate)


if __name__ == "__main__":
    import sys
    print("Python:", sys.executable)

    if not TK_AVAILABLE:
        print("tkinter no disponible")
        exit(1)

    root = tk.Tk()
    app = SpriteSheetApp(root)
    root.mainloop()

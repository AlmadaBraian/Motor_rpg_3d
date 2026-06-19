import math
import os
from dataclasses import dataclass
import random


from RuntimeText import RuntimeText
from config import SCREEN_H, SCREEN_W, base_path


@dataclass
class VisualNovelSprite:
    name: str
    image: str
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    alpha: float = 1.0
    visible: bool = True
    z: int = 0

    target_x: float = 0.0
    target_y: float = 0.0
    speed_x: float = 0.0
    speed_y: float = 0.0
    animating: bool = False

    fading_in: bool = False
    fading_out: bool = False
    alpha_speed: float = 0.0
    hide_on_finish: bool = False

    def __post_init__(self):
        self.target_x = self.x
        self.target_y = self.y


class VisualNovelSceneState:
    """Runtime 2D scene state for narrative / visual-novel scenes.

    A "sprite" in this subsystem is any 2D layer: full-screen backgrounds,
    character portraits, foreground overlays, CGs, etc.
    """

    def __init__(self):
        self.active = False
        self.sprites = {}
        self.texts = {}
        self.screen_width = SCREEN_W
        self.screen_height = SCREEN_H

    def reset(self):
        self.active = False
        self.sprites.clear()

    def load_from_scene_data(self, scene_data):
        self.reset()

        config = get_visual_novel_config(scene_data)
        if not config.get("enabled", False):
            return

        self.active = True
        self.screen_width = int(config.get("width", scene_data.get("width", SCREEN_W)))
        self.screen_height = int(config.get("height", scene_data.get("height", SCREEN_H)))

        for sprite_data in config.get("sprites", scene_data.get("sprites", [])):
            self.add_sprite(sprite_data)

        texts = config.get(
            "texts",
            scene_data.get("texts", [])
        )

        if isinstance(texts, dict):
            texts = [texts]

        for text_data in texts:
            self.add_text(text_data)

    def add_text(self, data):

        text = RuntimeText()

        text.name = data.get("name", "")

        text.text = data.get("text", "")

        text.x = float(data.get("x", 0))
        text.y = float(data.get("y", 0))

        text.visible = bool(
            data.get("visible", True)
        )

        text.scale = float(
            data.get("scale", 1)
        )

        text.z = int(
            data.get("z", 0)
        )

        self.texts[text.name] = text

        return text

    def resolve_image_path(self, image_path):
        if not image_path:
            return ""

        if os.path.isabs(image_path):
            return image_path

        candidates = [
            os.path.join(base_path, image_path),
            os.path.join(base_path, "textures", image_path),
            os.path.join(base_path, "sprites", image_path),
        ]

        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate

        return os.path.join(base_path, image_path)

    def read_image_size(self, image_path):
        resolved = self.resolve_image_path(image_path)

        if not resolved or not os.path.exists(resolved):
            return 0, 0

        from PIL import Image

        with Image.open(resolved) as img:
            return img.size

    def add_sprite(self, data):
        if not isinstance(data, dict):
            return None

        name = data.get("name", data.get("id", ""))
        fondo = data.get("fondo", data.get("id", False))
        image = data.get("image", data.get("path", data.get("texture", "")))

        if not name or not image:
            print("VN SPRITE INVALID:", data)
            return None

        image_w, image_h = self.read_image_size(image)

        if not fondo:
            width = float(data.get("w", data.get("width", image_w or SCREEN_W)))
            height = float(data.get("h", data.get("height", image_h or SCREEN_H)))

        else:
            width = SCREEN_W
            height = SCREEN_H

        sprite = VisualNovelSprite(
            name=name,
            image=image,
            x=float(data.get("x", 0)),
            y=float(data.get("y", 0)),
            width=width,
            height=height,
            alpha=float(data.get("alpha", 1.0)),
            visible=bool(data.get("visible", True)),
            z=int(data.get("z", data.get("layer", 0))),
        )

        self.sprites[name] = sprite
        return sprite

    def set_sprite(self, data):
        name = data.get("sprite", data.get("name", data.get("id", "")))
        sprite = self.sprites.get(name)

        if sprite is None:
            return self.add_sprite(data)

        if data.get("image") or data.get("path") or data.get("texture"):
            sprite.image = data.get("image", data.get("path", data.get("texture")))
            image_w, image_h = self.read_image_size(sprite.image)
            if "w" not in data and "width" not in data:
                sprite.width = image_w or sprite.width
            if "h" not in data and "height" not in data:
                sprite.height = image_h or sprite.height

        if "x" in data:
            sprite.x = float(data["x"])
        if "y" in data:
            sprite.y = float(data["y"])
        if "w" in data or "width" in data:
            sprite.width = float(data.get("w", data.get("width")))
        if "h" in data or "height" in data:
            sprite.height = float(data.get("h", data.get("height")))
        if "alpha" in data:
            sprite.alpha = float(data["alpha"])
        if "visible" in data:
            sprite.visible = bool(data["visible"])
        if "z" in data or "layer" in data:
            sprite.z = int(data.get("z", data.get("layer")))

        sprite.target_x = sprite.x
        sprite.target_y = sprite.y
        return sprite

    def hide_sprite(self, name):
        sprite = self.sprites.get(name)
        if sprite:
            sprite.visible = False
            sprite.animating = False
            sprite.fading_in = False
            sprite.fading_out = False

    def clear(self):
        self.sprites.clear()

    def start_animation(
        self,
        sprite_name,
        anim_name,
        text_name="",
        final_x=0,
        final_y=0,
        delta_ms=16,
        speed=300,
        duration=None,
    ):

        sprite = self.sprites.get(sprite_name)
        text = self.texts.get(text_name)

        target = sprite or text

        if target is None:
            print(
                "VN TARGET NOT FOUND:",
                sprite_name,
                text_name
            )
            return False

        final_x = float(final_x)
        final_y = float(final_y)

        speed = abs(float(speed))

        duration = self._resolve_duration(
            duration,
            delta_ms
        )

        # ==================================================
        # SPRITES
        # ==================================================

        if sprite is not None:

            sprite.animating = False
            sprite.fading_in = False
            sprite.fading_out = False
            sprite.speed_x = 0.0
            sprite.speed_y = 0.0

            if anim_name in ("caminar_derecha", "walk_right"):
                self._start_move(
                    sprite,
                    sprite.x + 100,
                    sprite.y,
                    speed
                )

            elif anim_name in ("caminar_izquierda", "walk_left"):
                self._start_move(
                    sprite,
                    sprite.x - 100,
                    sprite.y,
                    speed
                )

            elif anim_name in ("entrar_izquierda", "enter_left"):
                sprite.x = -sprite.width
                sprite.y = final_y
                sprite.visible = True
                sprite.alpha = 1.0

                self._start_move(
                    sprite,
                    final_x,
                    final_y,
                    speed
                )

            elif anim_name in ("entrar_derecha", "enter_right"):

                sprite.x = self.screen_width
                sprite.y = final_y
                sprite.visible = True
                sprite.alpha = 1.0

                self._start_move(
                    sprite,
                    final_x,
                    final_y,
                    speed
                )

            elif anim_name in ("salir_izquierda", "exit_left"):

                sprite.hide_on_finish = True

                self._start_move(
                    sprite,
                    -sprite.width,
                    sprite.y,
                    speed
                )

            elif anim_name in ("salir_derecha", "exit_right"):

                sprite.hide_on_finish = True

                self._start_move(
                    sprite,
                    self.screen_width,
                    sprite.y,
                    speed
                )

            elif anim_name == "traveling_x":

                sprite.visible = True
                sprite.alpha = max(sprite.alpha, 1.0)

                self._start_move(
                    sprite,
                    final_x,
                    final_y,
                    speed,
                    axis="x"
                )

            elif anim_name == "traveling_y":

                sprite.visible = True
                sprite.alpha = max(sprite.alpha, 1.0)

                self._start_move(
                    sprite,
                    final_x,
                    final_y,
                    speed,
                    axis="y"
                )

            elif anim_name in ("subir", "up"):

                self._start_move(
                    sprite,
                    sprite.x,
                    sprite.y - 50,
                    speed,
                    axis="y"
                )

            elif anim_name in ("bajar", "down"):

                self._start_move(
                    sprite,
                    sprite.x,
                    sprite.y + 50,
                    speed,
                    axis="y"
                )

            elif anim_name in ("quedarse", "stay"):

                sprite.target_x = sprite.x
                sprite.target_y = sprite.y

            elif anim_name == "fade_out":

                sprite.fading_out = True
                sprite.hide_on_finish = True

                sprite.alpha_speed = (
                    sprite.alpha /
                    max(0.01, duration)
                )

            elif anim_name == "fade_in":

                sprite.x = final_x
                sprite.y = final_y

                sprite.alpha = 0.0
                sprite.alpha_speed = (
                    1.0 /
                    max(0.01, duration)
                )

                sprite.visible = True
                sprite.fading_in = True

            else:
                print("VN SPRITE ANIMATION UNKNOWN:", anim_name)
                return False

            return True

        # ==================================================
        # TEXTOS
        # ==================================================

        text.visible = True

        text.elapsed = 0
        text.duration = duration
        progress = min(
            text.elapsed / duration,
            1.0
        )

        # permite múltiples animaciones
        if anim_name not in text.animations:
            text.animations.append(anim_name)

        if anim_name == "float_up":
            text.distance = 100

        elif anim_name == "shake":
            text.strength = 8

        elif anim_name == "pulse":
            text.speed = 8
            text.amount = 0.15

        elif anim_name == "typewriter":
            text.speed = 0.04

        elif anim_name == "fade_in":
            r, g, b, a = text.color
            text.color = (r, g, b, 0)

        elif anim_name == "fade_out":
            pass

        elif anim_name == "popup":
            pass

        elif anim_name == "ghost":
            pass

        elif anim_name == "glow":
            pass

        elif anim_name == "damage":
            pass

        elif anim_name == "none":
            pass

        else:
            print("VN TEXT ANIMATION UNKNOWN:", anim_name)
            return False

        return True

    def _resolve_duration(self, duration, delta_ms):
        if duration is not None:
            return float(duration)
        if delta_ms and float(delta_ms) > 16:
            return float(delta_ms) / 1000.0
        return 2.0

    def _start_move(self, sprite, target_x, target_y, speed, axis=None):
        sprite.target_x = float(target_x)
        sprite.target_y = float(target_y)
        sprite.animating = True
        sprite.visible = True

        if axis != "y":
            sprite.speed_x = speed
        if axis != "x":
            sprite.speed_y = speed

    def update(self, dt):

        for sprite in self.sprites.values():

            self._update_move(sprite, dt)
            self._update_fade(sprite, dt)

        for text in self.texts.values():

            if not text.visible:
                continue

            text.elapsed += dt

    def _update_move(self, sprite, dt):
        if not sprite.animating:
            return

        done_x = self._approach_axis(sprite, "x", "target_x", "speed_x", dt)
        done_y = self._approach_axis(sprite, "y", "target_y", "speed_y", dt)

        if done_x and done_y:
            sprite.animating = False
            if sprite.hide_on_finish:
                sprite.visible = False
                sprite.hide_on_finish = False

    def _approach_axis(self, sprite, value_attr, target_attr, speed_attr, dt):
        value = getattr(sprite, value_attr)
        target = getattr(sprite, target_attr)
        speed = getattr(sprite, speed_attr)

        if abs(value - target) <= 0.001 or speed <= 0:
            setattr(sprite, value_attr, target)
            return True

        step = speed * dt

        if value < target:
            value = min(target, value + step)
        else:
            value = max(target, value - step)

        setattr(sprite, value_attr, value)
        return abs(value - target) <= 0.001

    def _update_fade(self, sprite, dt):
        if sprite.fading_in:
            sprite.alpha += sprite.alpha_speed * dt
            if sprite.alpha >= 1.0:
                sprite.alpha = 1.0
                sprite.fading_in = False

        if sprite.fading_out:
            sprite.alpha -= sprite.alpha_speed * dt
            if sprite.alpha <= 0.0:
                sprite.alpha = 0.0
                sprite.fading_out = False
                sprite.visible = False

    def has_running_animations(self):
        for sprite in self.sprites.values():
            if sprite.animating or sprite.fading_in or sprite.fading_out:
                return True
        return False

    def sorted_sprites(self):
        return sorted(self.sprites.values(), key=lambda sprite: sprite.z)


def get_visual_novel_config(scene_data):
    if not isinstance(scene_data, dict):
        return {}

    config = scene_data.get("visual_novel", scene_data.get("vn", {}))

    if isinstance(config, dict):
        return config

    if config is True:
        return {"enabled": True}

    return {}


def has_visual_novel_layer(scene_data):
    if not isinstance(scene_data, dict):
        return False

    config = get_visual_novel_config(scene_data)
    return bool(config.get("enabled", False))


def is_visual_novel_scene(scene_data):
    if not isinstance(scene_data, dict):
        return False

    mode = str(scene_data.get("mode", scene_data.get("type", ""))).lower()
    if mode in ("visual_novel", "vn", "narrative", "narrativa"):
        return True

    if scene_data.get("no_3d") or scene_data.get("without_3d"):
        return True

    return False

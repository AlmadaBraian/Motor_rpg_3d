# FontRenderer.py

from PIL import Image, ImageDraw, ImageFont
from OpenGL.GL import *

class FontRenderer:

    def __init__(self, font_path="fonts/Helvetica.ttf", size=24):
        self.font = ImageFont.truetype(font_path, size)
        self.cache = {}

    def make_texture(self, text, color=(255,255,255,255)):
        key = (text, color)

        if key in self.cache:
            return self.cache[key]

        # medir texto
        bbox = self.font.getbbox(text)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        img = Image.new("RGBA", (w + 8, h + 8), (0,0,0,0))
        draw = ImageDraw.Draw(img)

        draw.text((4,4), text, font=self.font, fill=color)

        img_data = img.tobytes()

        texid = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texid)

        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            img.width,
            img.height,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            img_data
        )

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        self.cache[key] = (texid, img.width, img.height)

        return self.cache[key]

    def draw_text(
        self,
        text,
        x,
        y,
        color=(1,1,1,1)
    ):

        texid, w, h = self.make_texture(
        text,
        (
            int(color[0] * 255),
            int(color[1] * 255),
            int(color[2] * 255),
            int(color[3] * 255)
        )
    )

        glEnable(GL_TEXTURE_2D)

        glBindTexture(GL_TEXTURE_2D, texid)

        glColor4f(*color)

        glBegin(GL_QUADS)

        glTexCoord2f(0,0)
        glVertex2f(x, y)

        glTexCoord2f(1,0)
        glVertex2f(x + w, y)

        glTexCoord2f(1,1)
        glVertex2f(x + w, y + h)

        glTexCoord2f(0,1)
        glVertex2f(x, y + h)

        glEnd()

        glDisable(GL_TEXTURE_2D)
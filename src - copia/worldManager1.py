import pygame
from pygame.locals import *
import math
from functools import cmp_to_key
import os


texWidth =64
texHeight =64


class Bloque(pygame.sprite.Sprite):
    def __init__(self,imagen,cuadros):
        self.rotar = [128,128]
        pygame.sprite.Sprite.__init__(self)

        self.Estado = 0

        self.defectoImagen =[]
        base_path = os.path.dirname(__file__)
        pics_path = os.path.join(base_path, "pics")
        for i in range(cuadros):
            try:
                self.defectoImagen.append(pygame.image.load(pics_path + "/items/"+imagen+str(i+1)+".png" ))#.convert())
            except:
                pass
        self.fps=[0,cuadros]
        if self.defectoImagen:
            self.image = self.defectoImagen[0]
        else:
            self.image = pygame.Surface((64, 64))  # fallback
            self.image.fill((255, 0, 255))  # color debug

        self.rect = self.image.get_rect()
        self.spriteHeight = 0
        self.transformX=0
        self.transformY=0
        self.spriteX =0
        self.spriteY =0
        self.spriteZ =1
        self.invDet=0
        self.spritesurfaceX=0
        self.spriteHeight=0
        self.drawStartX=0
        self.drawEndX=0
        self.drawStartY=0
        self.drawEndY=0
        self.depth = self.rect.midbottom[1]


    def animar(self):
        if self.fps[0] <= self.fps[1]:
            self.fps[0] += 1
        else:
            self.fps[0]= 1
        #print self.fps





    def update(self,camera,planex,diry,dirx,planey,h,w,surface):
            #self.animar()


            #translate sprite position to relative to camera
            spriteX = self.rect[0] - camera[0];
            spriteY = self.rect[1] - camera[1];
            spriteZ = self.spriteZ

            invDet = 1.0 / (planex * diry - dirx * planey) #required for correct matrix multiplication

            transformX = invDet * (diry * spriteX - dirx * spriteY)
            transformY = invDet * (-planey * spriteX + planex * spriteY) #this is actually the depth inside the surface, that what Z is in 3D

            spritesurfaceX = int((w / 2) * (1 + transformX / transformY))

            #calculate height of the sprite on surface
            spriteHeight = abs(int(h / (transformY))) #using "transformY" instead of the real distance prevents fisheye
            #calculate lowest and highest pixel to fill in current stripe

            #drawStartY = -(spriteHeight) / 2 + (h / 2)
            drawStartY = (-spriteHeight *spriteZ)   / 2 + h / 2
            #drawEndY = spriteHeight / 2 + (h+12) / 2


            #calculate width of the sprite
            spriteWidth = abs( int (h / (transformY)))
            drawStartX = -spriteWidth / 2 + spritesurfaceX
            drawEndX = spriteWidth / 2 + spritesurfaceX
          



            if spriteHeight < 1000:

                for strife in range(int(drawStartX), int(drawEndX)):
                    self.strife = strife

                ##1) it's in front of camera plane so you don't see things behind you
                    ##2) it's on the surface (left)
                    ##3) it's on the surface (right)
                    ##4) ZBuffer, with perpendicular distance

                if (transformY >0 and self.strife >+128 and self.strife < w +128):
                    #try:
                        #segOrig = self.defectoImagen.get_rect()

                        segRot = pygame.transform.scale(self.image, (spriteWidth, spriteHeight ))
                        # = smoothscale(segRot, (w2, int(h2*self._perspective)))


                        #rot_rect = segOrig.copy()


                        #self.BotonViaje.rect[2],self.BotonViaje.rect[3] = (spriteWidth , spriteHeight )
                        imageFinal = segRot
                        surface.blit(imageFinal, ((drawStartX) ,(drawStartY+8)))


                    #except:
                        #pass


class WorldManager(object):

    def __init__(self,worldMap,sprite_positions,x,y,dirx,diry,planex,planey):

        #self.grupoSprite = pygame.sprite.Group()



        self.BotonViaje = Bloque("barrel_0",1)
        self.BotonViaje.rect.x = (0.2)
        self.BotonViaje.rect.y = (2.0)
        self.BotonViaje.spriteZ = 1.5
        #self.grupoSprite.add(self.BotonViaje)

        self.BotonViaje1 = Bloque("pillar1_0",1)
        self.BotonViaje1.rect.x = (1.0)
        self.BotonViaje1.rect.y = (2.0)
        self.BotonViaje1.spriteZ = 4
        #self.grupoSprite.add(self.BotonViaje1)

        self.BotonViaje2 = Bloque("gordo_0",1)
        self.BotonViaje2.rect.x = (1.0)
        self.BotonViaje2.rect.y = (3.0)
        #self.grupoSprite.add(self.BotonViaje2)

        self.BotonViaje3 = Bloque("gordo_0",1)
        self.BotonViaje3.rect.x = (1.0)
        self.BotonViaje3.rect.y = (3.5)
        #self.grupoSprite.add(self.BotonViaje3)

        self.BotonViaje4 = Bloque("test1_0",6)
        self.BotonViaje4.rect.x = (3.5)
        self.BotonViaje4.rect.y = (3.8)
        #self.grupoSprite.add(self.BotonViaje4)

        self.BotonViaje5 = Bloque("pillar_0",1)
        self.BotonViaje5.rect.x = (1.5)
        self.BotonViaje5.rect.y = (4.8)
        #self.grupoSprite.add(self.BotonViaje5)


        self.grupoSprite = [

              self.BotonViaje5,
              self.BotonViaje3,

              self.BotonViaje4,
              self.BotonViaje,
              self.BotonViaje1,
              self.BotonViaje2,
        ]




        self.background = None

        base_path = os.path.dirname(__file__)
        pics_path = os.path.join(base_path, "pics")
        self.images = [

              load_image(pygame.image.load(pics_path +"/walls/redbrick.png"), False,64, colorKey = (0,0,0)),



              load_image(pygame.image.load(pics_path+"/walls/colorstone.png"), True,64, colorKey = (0,0,255)),

              ]
        self.camera = Camera(x,y,dirx,diry,planex,planey)
        self.worldMap = worldMap
        self.sprite_positions = sprite_positions
    def draw(self, surface):
        w = surface.get_width()
        h = surface.get_height()
        #draw background
        base_path = os.path.dirname(__file__)
        pics_path = os.path.join(base_path, "pics")
        if self.background is None:
            self.background = pygame.transform.scale(pygame.image.load(pics_path+"/fondo.png"), (w,h))
        surface.blit(self.background, (0,0))
        zBuffer = []
        for x in range(w):
            #calculate ray position and direction
            cameraX = float(2 * x / float(w) - 1) #x-coordinate in camera space
            rayPosX = self.camera.x
            rayPosY = self.camera.y
            rayDirX = self.camera.dirx + self.camera.planex * cameraX
            rayDirY = self.camera.diry + self.camera.planey * cameraX
            #which box of the map we're in
            mapX = int(rayPosX)
            mapY = int(rayPosY)

            #length of ray from current position to next x or y-side
            sideDistX = 0.
            sideDistY = 0.

            #length of ray from one x or y-side to next x or y-side
            deltaDistX = math.sqrt(1 + (rayDirY * rayDirY) / (rayDirX * rayDirX))
            if rayDirY == 0: rayDirY = 0.00001
            deltaDistY = math.sqrt(1 + (rayDirX * rayDirX) / (rayDirY * rayDirY))
            perpWallDist = 0.

            #what direction to step in x or y-direction (either +1 or -1)
            stepX = 0
            stepY = 0

            hit = 0 #was there a wall hit?
            side = 0 # was a NS or a EW wall hit?

            # calculate step and initial sideDist
            if rayDirX < 0:
                stepX = - 1
                sideDistX = (rayPosX - mapX) * deltaDistX
            else:
                stepX = 1
                sideDistX = (mapX + 1.0 - rayPosX) * deltaDistX

            if rayDirY < 0:
                stepY = - 1
                sideDistY = (rayPosY - mapY) * deltaDistY
            else:
                stepY = 1
                sideDistY = (mapY + 1.0 - rayPosY) * deltaDistY

            # perform DDA
            while hit == 0:
                # jump to next map square, OR in x - direction, OR in y - direction
                if sideDistX < sideDistY:

                    sideDistX += deltaDistX
                    mapX += stepX
                    side = 0
                else:
                    sideDistY += deltaDistY
                    mapY += stepY
                    side = 1

                # Check if ray has hit a wall
                if (self.worldMap[mapX][mapY] > 0):
                    hit = 1
            # Calculate distance projected on camera direction (oblique distance will give fisheye effect !)
            if (side == 0):
                #perpWallDist = fabs((mapX - rayPosX + (1 - stepX) / 2) / rayDirX)
                perpWallDist = (abs((mapX - rayPosX + (1 - stepX) / 2) / rayDirX))
            else:
                perpWallDist = (abs((mapY - rayPosY + (1 - stepY) / 2) / rayDirY))

            # Calculate height of line to draw on surface
            if perpWallDist == 0:perpWallDist = 0.000001
            lineHeight = abs(int(h / perpWallDist))

            # calculate lowest and highest pixel to fill in current stripe
            drawStart = - lineHeight / 2 + h / 2
            drawEnd = lineHeight / 2 + h / 2

            #texturing calculations
            texNum = self.worldMap[mapX][mapY] - 1; #1 subtracted from it so that texture 0 can be used!

            #calculate value of wallX
            wallX = 0 #where exactly the wall was hit
            if (side == 1):
                wallX = rayPosX + ((mapY - rayPosY + (1 - stepY) / 2) / rayDirY) * rayDirX
            else:
                wallX = rayPosY + ((mapX - rayPosX + (1 - stepX) / 2) / rayDirX) * rayDirY;
            wallX -= math.floor((wallX));

            #x coordinate on the texture
            texX = int(wallX * float(texWidth))
            if(side == 0 and rayDirX > 0):
                texX = texWidth - texX - 1;
            if(side == 1 and rayDirY < 0):
                texX = texWidth - texX - 1;

            if(side == 1):
                texNum #+=8
            if lineHeight > 10000:
                lineHeight=10000
                drawStart = -10000 /2 + h/2
            surface.blit(pygame.transform.scale(self.images[texNum][texX], (1, lineHeight)), (x, drawStart))
            zBuffer.append(perpWallDist)





        #function to sort sprites
        def sprite_compare(s1, s2):

            import math
            s1Dist = math.sqrt((s1.rect[0] -self.camera.x) ** 2 + (s1.rect[1] -self.camera.y) ** 2)
            s2Dist = math.sqrt((s2.rect[0] -self.camera.x) ** 2 + (s2.rect[1] -self.camera.y) ** 2)
            #print s1,"aaaaa",s2,"bbb", s1Dist,s2Dist
            if s1Dist>s2Dist:
                return -1
            elif s1Dist==s2Dist:
                return 0
            else:
                return 1



##        self.grupoSprite.sort(sprite_compare)

            self.grupoSprite.sort(key=cmp_to_key(sprite_compare))

##        for chota in range(0,len(self.grupoSprite)):
        for sprite in self.grupoSprite:
            sprite.update([self.camera.x, self.camera.y], self.camera.planex, 
                  self.camera.diry, self.camera.dirx, 
                  self.camera.planey, h, w, surface)


##            self.grupoSprite[chota].update([self.camera.x,self.camera.y],self.camera.planex,self.camera.diry,self.camera.dirx, self.camera.planey,h,w,surface)


class Camera(object):
    def __init__(self,x,y,dirx,diry,planex,planey):
        self.x = float(x)
        self.y = float(y)
        self.dirx = float(dirx)
        self.diry = float(diry)
        self.planex = float(planex)
        self.planey = float(planey)


def load_image(image, darken, puto, colorKey = None):
    ret = []
    if colorKey is not None:
        image.set_colorkey(colorKey)
    if darken:
        image.set_alpha(127)
    for i in range(image.get_width()):
        s = pygame.Surface((1, puto))#.convert()
        #s = pygame.Surface((64, 64))
##        caca = pygame.Rect(0,0,64,64)
        #s.fill((0,0,0))

        s.blit(image, (- i, 0))
       # s.blit(image,(- i, 0),caca)

        if colorKey is not None:
            s.set_colorkey(colorKey)
        ret.append(s)

    return ret

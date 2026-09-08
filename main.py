import math
from pathlib import Path

import pygame as py
from pygame import Vector2 as vect
from pygame.constants import *

py.font.init()
PATH = Path.cwd()
FONT = py.font.Font('arial.ttf', 10)


class Controller:

    def __init__(self):
        pass

    def getJoystick(self, param):
        pass


CONTROLLER = Controller()


class Group(py.sprite.Group):

    def __init__(self):
        super().__init__()
        self.offset = vect()
        self.halfScreenSize = [i // 2 for i in py.display.get_window_size()]
        self.bg = None
        self.char = None

    def addBg(self, group):
        self.bg = group

    def camera(self, target):
        self.offset = vect(target.rect.center) - self.halfScreenSize
        self.offset.x = round(self.offset.x)
        self.offset.y = round(self.offset.y)

    def cDraw(self, win, target):
        self.camera(target)
        for bg in self.bg:
            win.blit(bg.image, bg.rect.topleft - self.offset)

        for spr in sorted(self.sprites(), key=lambda sprite: sprite.ySort):
            if spr == target:
                win.blit(spr.image, spr.centerScreenRect)
            else:
                win.blit(spr.image, spr.updateScreenPos(self.offset))
        target.lineOfSight(win)


class Tile(py.sprite.Sprite):

    def __init__(self, pos, image, *groups, **extra):
        super().__init__(*groups)
        self.ogImage = image.copy()
        self.image = image
        self.properties = extra.setdefault('properties', None)
        self.rect = self.image.get_frect(topleft=pos)
        self.hitbox = self.rect.copy()
        self.ySort = self.rect.centery - extra.setdefault('overlapOffset', 0)
        self.onScreenPos = self.image.get_frect(topleft=pos)

    def updateScreenPos(self, offset):
        self.onScreenPos.topleft = self.rect.topleft - offset
        return self.onScreenPos


class CollisionTile(Tile):

    def __init__(self, pos, image, *groups, **extra):
        super().__init__(pos, image, *groups, **extra)
        xhitBox = extra.setdefault('xHitBox', 0)
        yhitBox = extra.setdefault('yHitBox', 0)

        self.hitbox = self.rect


class BackgroundBlur:

    def __init__(self):
        self.circleBlurOG = py.image.load(PATH / 'unseeable.png').convert_alpha()
        self.circleBlurOG.set_alpha(200)

    def update(self, win):
        mousePos = py.mouse.get_pos()
        angle = math.degrees(math.atan2(-(mousePos[1] - 360), mousePos[0] - 640)) - 45
        blur = py.transform.rotate(self.circleBlurOG, angle)
        blurRect = blur.get_frect(center=(640, 360))
        win.blit(blur, blurRect)


class PlayerSprite(py.sprite.Sprite):

    def __init__(self, walls, seeables, unseeables, *groups):
        super().__init__(*groups)

        pos = 0, 0
        self.drawSurface = py.Surface((1280, 720), py.SRCALPHA)

        # directory = base_path / 'Character'
        #
        # self.images = {'front': dict(), 'left': dict(), 'right': dict(), 'back': dict()}
        # for file, type, i in zip(listdir(directory), cycle((1, 'idle', 2)), range(12)):
        #     self.images[tuple(self.images.keys())[i // 3]].update(
        #         {type: py.transform.scale_by(py.image.load(f'{directory}/{file}').convert_alpha(), 2)})

        self.facing = 'front'

        # self.animationCount = 0
        # self.image = self.images[self.facing]['idle']

        self.image = py.Surface((64, 64))
        self.image.fill('blue')

        self.rect: py.FRect = self.image.get_frect(center=pos)
        self.hitBox = self.rect
        self.centerScreenRect = self.image.get_frect(center=(640, 360))

        self.direction = vect((0, 0))
        self.walls = walls
        self.unseeables = unseeables
        self.seeables = seeables
        self.cooldown = 0
        self.dt = None
        self.ySort = self.rect.centery

        # self.audioMixer = audioMixer

    def collisionCheck(self, axis):
        for wall in py.sprite.spritecollide(self, self.walls, False):
            if wall.hitbox.colliderect(self.hitBox):
                if axis == 'x':
                    if self.direction.x > 0:
                        self.hitBox.right = wall.hitbox.left
                    elif self.direction.x < 0:
                        self.hitBox.left = wall.hitbox.right
                    self.rect.centerx = self.hitBox.centerx
                elif axis == 'y':
                    if self.direction.y > 0:
                        self.hitBox.bottom = wall.hitbox.top
                    elif self.direction.y < 0:
                        self.hitBox.top = wall.hitbox.bottom
                    self.rect.centery = self.hitBox.centery

    @staticmethod
    def cornerCheckOrder(wall):
        wallPos = wall.onScreenPos
        corners = None
        if wallPos.topleft[0] >= 640 and wallPos.topleft[1] >= 360:
            corners = wallPos.topright, wallPos.bottomright, wallPos.bottomleft
        elif wallPos.topright[0] <= 640 and wallPos.topright[1] >= 360:
            corners = wallPos.topleft, wallPos.bottomleft, wallPos.bottomright
        elif wallPos.bottomleft[0] >= 640 and wallPos.bottomleft[1] <= 360:
            corners = wallPos.topleft, wallPos.topright, wallPos.bottomright
        elif wallPos.bottomright[0] <= 640 and wallPos.bottomright[1] <= 360:
            corners = wallPos.topright, wallPos.topleft, wallPos.bottomleft
        elif wallPos.top >= 360:
            corners = wallPos.topright, wallPos.bottomright, wallPos.bottomleft, wallPos.topleft
        elif wallPos.right <= 640:
            corners = wallPos.topright, wallPos.topleft, wallPos.bottomleft, wallPos.bottomright
        elif wallPos.bottom <= 360:
            corners = wallPos.bottomleft, wallPos.topleft, wallPos.topright, wallPos.bottomright
        elif wallPos.left >= 640:
            corners = wallPos.topleft, wallPos.topright, wallPos.bottomright, wallPos.bottomleft
        return corners

    @staticmethod
    def onScreen(corners):
        valid = []
        for corner in corners:
            if 1280 >= corner[0] >= 0 and 720 >= corner[1] >= 0:
                valid.append(True)
            else:
                valid.append(False)
        return any(valid)

    def blockUnseeables(self, linePairs):
        for tile in self.unseeables:
            tile.image = tile.ogImage.copy()
            for lines in linePairs:
                for i, line in enumerate(lines):
                    clippedLine = tile.onScreenPos.clipline(line)
                    if clippedLine:
                        points = [vect(clippedLine[0]) - vect(tile.onScreenPos.topleft),
                                  (vect(clippedLine[1]) - vect(tile.onScreenPos.topleft))]

                        gradient = (points[0][1]-points[1][1])/(points[0][0]-points[1][0])
                        if (not i and gradient > 0) or (i and gradient < 0):
                            points.insert(1, vect(tile.onScreenPos.w, tile.onScreenPos.h))
                            points.insert(1, vect(0, tile.onScreenPos.h))
                            if not points[0][1]:
                                points.insert(1,vect(0,0))
                            if gradient < 0:
                                points.reverse()

                        else:
                            if points[-1][1] == tile.onScreenPos.h:
                                points.insert(1,vect(tile.onScreenPos.w,tile.onScreenPos.h))
                            points.insert(1,vect(tile.onScreenPos.w,0))
                            points.insert(1,vect(0,0))


                        self.polygon = py.draw.polygon(tile.image, (0, 0, 0, 0), points)

    def lineOfSight(self, win):
        self.drawSurface.fill(py.Color('#00000000'))

        pos = (640, 360)
        lines = []
        for wall in self.seeables:
            corners = self.cornerCheckOrder(wall)
            validCorners = []
            validCornersVect = []
            shadowCorner = []
            if self.onScreen(corners):
                for corner in corners:
                    cornerVect = (vect(corner) - pos).normalize()
                    if not wall.onScreenPos.collidepoint(
                            vect(corner) - cornerVect) or cornerVect.y == 0 or cornerVect.x == 0:
                        cornerVect.scale_to_length(2000)
                        validCornersVect.insert(0, cornerVect + pos)
                        shadowCorner.append(vect(corner))
                    validCorners.append(corner)
            validCorners += validCornersVect

            if len(validCorners) > 2:
                py.draw.polygon(self.drawSurface, py.Color(0, 0, 0, 100), validCorners)

            for i, corner in enumerate(validCorners, 1):
                py.draw.circle(self.drawSurface, 'White', corner, 10)
                self.drawSurface.blit(FONT.render(str(i), True, 'Black'), corner - vect(5, 5))

            lines.append(zip(shadowCorner, reversed(validCornersVect)))
        self.blockUnseeables(lines)

        win.blit(self.drawSurface, (0, 0))

    def input(self):
        keys = py.key.get_pressed()
        inputDir = vect()
        if keys[K_w] or CONTROLLER.getJoystick('Up'):
            inputDir.y = -1
            self.facing = 'back'
        if keys[K_s] or CONTROLLER.getJoystick('Down'):
            inputDir.y = 1
            self.facing = 'front'
        if keys[K_a] or CONTROLLER.getJoystick('Left'):
            inputDir.x = -1
            self.facing = 'left'
        if keys[K_d] or CONTROLLER.getJoystick('Right'):
            inputDir.x = 1
            self.facing = 'right'
        if inputDir:
            inputDir.normalize_ip()
            # if not py.mixer.get_busy():
            #     self.audioMixer.playSound('footsteps')
        self.direction = inputDir

    def walk(self):
        speed = 300  # 300
        self.input()
        self.rect.centerx += self.direction.x * speed * self.dt
        self.hitBox.centerx = self.rect.centerx
        self.collisionCheck('x')
        self.rect.centery += self.direction.y * speed * self.dt
        self.hitBox.centery = self.rect.centery
        self.collisionCheck('y')

    def animate(self):
        if self.direction:
            self.animationCount += 8 * self.dt
            order = (1, 'idle', 2, 'idle')
            if self.animationCount >= 3:
                self.animationCount = 0

            self.image = self.images[self.facing][order[round(self.animationCount)]]

        else:
            self.animationCount = 0
            self.image = self.images[self.facing]['idle']

    def resetWalls(self, walls):
        self.walls = walls

    def update(self, dt):
        self.dt = dt
        self.ySort = self.rect.centery
        self.walk()
        # self.animate()


def main():
    win = py.display.set_mode((1280, 720))
    rr = py.time.Clock()
    running = True

    wall = py.Surface((64, 128), SRCALPHA)
    wall2 = py.Surface((128, 64), SRCALPHA)
    x = wall.copy()
    x.fill('blue')
    wall.fill('red')
    wall2.fill('red')
    walls = py.sprite.Group()
    seeables = py.sprite.Group()
    unseeables = py.sprite.Group()
    CollisionTile((-64, 32), wall2, walls, seeables)
    # CollisionTile((100, -73), wall, walls, seeables)
    CollisionTile((200, 125), x, walls, unseeables)
    # CollisionTile((324, 89), wall2, walls)
    # CollisionTile((89, 320), wall, walls)
    # CollisionTile((200, 320), wall, walls)

    allSprites = Group()
    charcter = PlayerSprite(walls, seeables, unseeables)

    allSprites.add(charcter, walls)
    allSprites.addBg(py.sprite.Group())

    blur = BackgroundBlur()

    while running:
        dt = rr.tick(120) / 1000
        win.fill((86, 86, 86))
        for event in py.event.get():
            if event.type == py.QUIT:
                running = False
        allSprites.update(dt)
        allSprites.cDraw(win, charcter)

        # blur.update(win)

        py.display.update()


if __name__ == '__main__':
    py.init()
    main()

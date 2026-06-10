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

    def __init__(self, pos, image, group, properties=None, overlapOffset=0):
        super().__init__(group)
        self.image = image
        self.properties = properties
        self.rect = self.image.get_frect(topleft=pos)
        self.hitbox = self.rect.copy()
        self.ySort = self.rect.centery - overlapOffset
        self.onScreenPos = self.image.get_frect(topleft=pos)

    def updateScreenPos(self, offset):
        self.onScreenPos.topleft = self.rect.topleft - offset
        return self.onScreenPos


class CollisionTile(Tile):

    def __init__(self, pos, image, group, properties, overlapOffset=0, xhitBox=1, yhitBox=1):
        super().__init__(pos, image, group, properties, overlapOffset)
        self.drawSurfaceOG = py.image.load('images.jpg').convert_alpha()
        self.drawSurface = self.drawSurfaceOG.copy()
        self.hitbox = self.rect

    def cornerCheckOrder(self):
        wallPos = self.onScreenPos
        corners = None
        if wallPos.topleft[0] >= 640 and wallPos.topleft[1] >= 360:
            corners = wallPos.topright, wallPos.bottomright, wallPos.bottomleft
        elif wallPos.topright[0] <= 640 and wallPos.topright[1] >= 360:
            corners = wallPos.bottomright, wallPos.bottomleft, wallPos.topleft
        elif wallPos.bottomleft[0] >= 640 and wallPos.bottomleft[1] <= 360:
            corners = wallPos.topleft, wallPos.topright, wallPos.bottomright
        elif wallPos.bottomright[0] <= 640 and wallPos.bottomright[1] <= 360:
            corners = wallPos.bottomleft, wallPos.topleft, wallPos.topright
        elif wallPos.top >= 360:
            corners = wallPos.topright, wallPos.bottomright, wallPos.bottomleft, wallPos.topleft
        elif wallPos.right <= 640:
            # corners = wallPos.topright, wallPos.topleft, wallPos.bottomleft, wallPos.bottomright
            corners = wallPos.bottomright, wallPos.bottomleft, wallPos.topleft, wallPos.topright
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

    @staticmethod
    def getCornersOfScreen(validCorners):
        screenCorners = [(0, 0), (1280, 0), (1280, 720), (0, 720)]
        bestDistance = 100000000
        for corner in screenCorners:
            distance = vect(validCorners[0]).distance_squared_to(corner)
            if distance < bestDistance:
                bestDistance = distance
                firstCorner = corner

        retScreenCorners = screenCorners[screenCorners.index(firstCorner):] + screenCorners[
            :screenCorners.index(firstCorner)]

        return retScreenCorners

    def lineOfSight(self, win):
        pos = (640, 360)
        self.drawSurface = self.drawSurfaceOG.copy()

        corners = self.cornerCheckOrder()
        validCorners = []
        validCornersVect = []
        if self.onScreen(corners):
            for corner in corners:
                cornerVect = (vect(corner) - pos).normalize()
                if not self.onScreenPos.collidepoint(
                        vect(corner) - cornerVect) or cornerVect.y == 0 or cornerVect.x == 0:
                    cornerVect.scale_to_length(2000)
                    validCornersVect.insert(0, cornerVect + pos)
                validCorners.append(corner)

        if len(validCorners) > 2:
            validCorners += [validCornersVect[0]] + self.getCornersOfScreen(validCornersVect) + [
                validCornersVect[1]]
            py.draw.polygon(self.drawSurface, py.Color(0, 0, 0, 0), validCorners)

            for i, corner in enumerate(validCorners, 1):
                # print(f'wall {x}    corner {i}')
                py.draw.circle(self.drawSurface, 'White', corner, 10)
                self.drawSurface.blit(FONT.render(str(i), True, 'Black'), corner - vect(5, 5))

            win.blit(self.drawSurface, (0, 0))


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

    def __init__(self, walls, *groups):
        super().__init__(*groups)
        pos = 0, 0
        # self.drawSurface = py.Surface((1280, 720), py.SRCALPHA)

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

    def lineOfSight(self, win):
        # self.drawSurface.fill(py.Color('#00000000'))
        for wall in self.walls:
            wall.lineOfSight(win)

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

    wall = py.Surface((64, 128))
    wall.fill('red')
    walls = py.sprite.Group()
    CollisionTile((-64, 32), wall, walls, None)
    # CollisionTile((100, -73), wall, walls, None)
    # CollisionTile((200, -312), wall, walls, None)
    # CollisionTile((324, 89), wall, walls, None)
    # CollisionTile((89, 320), wall, walls, None)
    # CollisionTile((200, 320), wall, walls, None)


    allSprites = Group()
    charcter = PlayerSprite(walls)

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
        py.display.set_caption(f'{rr.get_fps():2f}')

if __name__ == '__main__':
    py.init()
    main()

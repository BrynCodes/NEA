import math
from pathlib import Path

import pygame as py
from pygame import Vector2 as vect
from pygame.constants import *

SCREENSIZE = (1280, 720)
CENTER = tuple(map(lambda x: x // 2, SCREENSIZE))

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
        self.centerScreenRect = self.image.get_frect(center=CENTER)

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
            corners = wallPos.topleft, wallPos.bottomleft, wallPos.bottomright, wallPos.topright
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

    @staticmethod
    def pointCheck(rect, *vects):
        points = (rect.topleft, rect.topright, rect.bottomleft, rect.bottomright)
        pointsRel = (vect(0, 0), vect(rect.w, 0), vect(0, rect.h), vect(rect.w, rect.h))
        between = []

        d3 = vects[0].cross(vects[1])

        for point in points:
            point = vect(point) - vect(CENTER)
            d1 = vects[0].cross(point)
            d2 = point.cross(vects[1])
            if d3 > 0:
                between.append(d1 > 0 and d2 > 0)
            else:
                between.append(d1 < 0 and d2 < 0)

        return [pointsRel[i] for i in range(len(between)) if between[i]]

    @staticmethod
    def arrangePoints(points):

        sortedPoints = points.copy()
        sortedPoints.sort(key=lambda x: x.y)


        firstTwo = sortedPoints[:2]
        rest = sortedPoints[2:]

        firstTwo.sort(key=lambda x:x.x)
        rest.sort(key=lambda x:x.x)
        arrrangedPoints = [firstTwo[0]]
        arrrangedPoints += rest
        arrrangedPoints.append(firstTwo[1])


        # pointNum = len(points)
        # distanceFromOrigin = list(map(lambda x: x.length_squared(), points))
        #
        # miniDist = distanceFromOrigin.index(min(distanceFromOrigin))
        # distanceFromOrigin.pop(miniDist)
        # maxiDist = distanceFromOrigin.index(max(distanceFromOrigin))
        # distanceFromOrigin.pop(maxiDist)
        #
        # arrrangedPoints.append(points.pop(miniDist))
        # arrrangedPoints.append(points.pop(maxiDist))
        # arrrangedPoints.insert(1, points.pop())
        #
        # for i in range(pointNum - 3):
        #     arrrangedPoints.append(points.pop())

        return arrrangedPoints

    def blockUnseeables(self, linePairs):
        for tile in self.unseeables:
            tile.image = tile.ogImage.copy()
            if self.onScreen((tile.onScreenPos.topleft, tile.onScreenPos.topright, tile.onScreenPos.bottomleft,
                              tile.onScreenPos.bottomright)):
                for lines in linePairs:
                    vects = []
                    points = []
                    clippedPoints = []
                    for line in lines:
                        vects.append(line[1] - line[0])

                        clippedLine = tile.onScreenPos.clipline(line)

                        if clippedLine and clippedLine[0] != clippedLine[1]:
                            clippedPoints += [vect(clippedLine[0]) - vect(tile.onScreenPos.topleft),
                                              (vect(clippedLine[1]) - vect(tile.onScreenPos.topleft))]

                    points += clippedPoints
                    points += self.pointCheck(tile.onScreenPos, *vects)

                    if len(points) > 1:
                        arrangedPoints = self.arrangePoints(points.copy())
                        py.draw.polygon(tile.image, (0, 0, 0, 0), arrangedPoints)

                        for i, corner in enumerate(arrangedPoints, 1):
                            corner += tile.onScreenPos.topleft
                            py.draw.circle(self.drawSurface, 'White', corner, 10)
                            self.drawSurface.blit(FONT.render(str(i), True, 'Black'), corner - vect(5, 5))

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
                    cornerVect = (vect(
                        corner) - pos).normalize()  # the vector from the middle of screen(Character) to the corner. Normalised

                    if not wall.onScreenPos.collidepoint(
                            vect(
                                corner) - cornerVect) or cornerVect.y == 0 or cornerVect.x == 0:  # Checks if the corner is an outer corner.
                        cornerVect.scale_to_length(2000)
                        validCornersVect.insert(0, cornerVect + pos)
                        shadowCorner.append(vect(corner))
                    validCorners.append(corner)
                validCorners += validCornersVect

                if len(validCorners) > 2:
                    py.draw.polygon(self.drawSurface, py.Color(0, 0, 0, 100), validCorners)  # 200

                # for i, corner in enumerate(validCorners, 1):
                #     py.draw.circle(self.drawSurface, 'White', corner, 10)
                #     self.drawSurface.blit(FONT.render(str(i), True, 'Black'), corner - vect(5, 5))

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
        speed = 200  # 300
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
    win = py.display.set_mode(SCREENSIZE)
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
    CollisionTile((-64, 128), wall2, walls, seeables)
    CollisionTile((100, -73), wall, walls, seeables)
    CollisionTile((-200, 125), x, walls, unseeables)
    # CollisionTile((324, 89), wall2, walls)
    # CollisionTile((89, 320), wall, walls)
    # CollisionTile((200, 320), wall, walls)

    allSprites = Group()
    charcter = PlayerSprite(walls, seeables, unseeables)

    allSprites.add(charcter, walls)
    allSprites.addBg(py.sprite.Group())

    while running:
        dt = rr.tick(120) / 1000
        win.fill((86, 86, 86))
        for event in py.event.get():
            if event.type == py.QUIT:
                running = False
        allSprites.update(dt)
        allSprites.cDraw(win, charcter)

        py.display.update()


if __name__ == '__main__':
    py.init()
    main()

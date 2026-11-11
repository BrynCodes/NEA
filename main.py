import re
from math import atan2, degrees
from os import listdir
from pathlib import Path

import pygame as py
from pygame import Vector2 as vect
from pygame.constants import *
from pytmx.util_pygame import load_pygame

SCREENSIZE = (1280, 720)
CENTER = tuple(map(lambda x: x // 2, SCREENSIZE))

py.font.init()
ASSETSPATH = Path('Assets')
FONT = py.font.Font(ASSETSPATH / 'arial.ttf', 10)


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
        self.halfScreenSize = CENTER
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
                win.blit(spr.image, spr.onScreenPos)

            elif spr.properties == 'CollisionRectangles':
                spr.updateScreenPos(self.offset)

            else:
                win.blit(spr.image, spr.updateScreenPos(self.offset))
        target.lineOfSight.update(win)


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


class LineOfSight:

    def __init__(self, seeables, unseeables):
        self.seeables = seeables
        self.unseeables = unseeables
        self.drawSurface = py.Surface((1280, 720), py.SRCALPHA)

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
    def pointCheck(rect, clippedLine, *vects):
        if clippedLine:
            let = 0
        else:
            let = 1500
        points = (rect.topleft, rect.topright, rect.bottomleft, rect.bottomright)
        pointsRel = (vect(0, 0), vect(rect.w, 0), vect(0, rect.h), vect(rect.w, rect.h))
        between = []

        d3 = vects[0].cross(vects[1])

        for point in points:
            point = vect(point) - vect(CENTER)
            d1 = vects[0].cross(point)
            d2 = point.cross(vects[1])
            if d3 > 0:
                between.append(d1 >= -let and d2 >= -let)
            else:
                between.append(d1 <= let and d2 <= let)

        return [pointsRel[i] for i in range(len(between)) if between[i]]

    @staticmethod
    def arrangePoints(points):

        points.sort(key=lambda x: x.y)

        firstTwo = points[:2]
        rest = points[2:]

        firstTwo.sort(key=lambda x: x.x)
        rest.sort(key=lambda x: x.x)
        arrrangedPoints = [firstTwo[0]]

        if len(rest) == 3:
            if rest[1].x == rest[2].x:
                arrrangedPoints.append(rest.pop(0))
                arrrangedPoints.append(rest.pop(1))

        arrrangedPoints += rest
        arrrangedPoints.append(firstTwo[1])

        return arrrangedPoints

    @staticmethod
    def clippedLineCalculation(tile, line):
        clippedPoints = []
        clippedLine = tile.onScreenPos.clipline(line)

        if clippedLine and clippedLine[0] != clippedLine[1]:
            clippedPoints += [vect(clippedLine[0]) - vect(tile.onScreenPos.topleft),
                              (vect(clippedLine[1]) - vect(tile.onScreenPos.topleft))]

            for i in clippedPoints:
                if i.x == tile.rect.w - 1:
                    i.x = tile.rect.w
                if i.y == tile.rect.h - 1:
                    i.y = tile.rect.h

        return clippedPoints

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
                        clippedPoint = self.clippedLineCalculation(tile, line)
                        clippedPoints.append(clippedPoint)
                        points += clippedPoint

                    points += self.pointCheck(tile.onScreenPos, any(clippedPoints), *vects)

                    if len(points) > 2:
                        arrangedPoints = self.arrangePoints(points.copy())
                        py.draw.polygon(tile.image, (0, 0, 0, 0), arrangedPoints)

    @staticmethod
    def cornerCheckOrder(wall):
        wallPos = wall.onScreenPos
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
        else:
            corners = wallPos.topright, wallPos.bottomright, wallPos.bottomleft
        return corners

    @staticmethod
    def vectorCalulation(corner, wall):
        pos = (640, 360)
        cornerVect = (vect(
            corner) - pos).normalize()  # the vector from the middle of screen(Character) to the corner. Normalised

        if (not wall.onScreenPos.collidepoint(vect(corner) - cornerVect)
                or cornerVect.y == 0 or cornerVect.x == 0):  # Checks if the corner is an outer corner.
            cornerVect.scale_to_length(2000)
            return cornerVect + pos
        return False

    def wallShadowCast(self, wall, corners):
        endOfShadowPoints = []
        startOfShadowPoints = []
        allCorners = list(corners)

        for corner in corners:
            endOfShadowPoint = self.vectorCalulation(corner, wall)
            if endOfShadowPoint:
                endOfShadowPoints.insert(0, endOfShadowPoint)
                startOfShadowPoints.append(vect(corner))

        allCorners += endOfShadowPoints

        if len(allCorners) > 2:
            py.draw.polygon(self.drawSurface, py.Color(0, 0, 0, 200), allCorners)  # 200

        return zip(startOfShadowPoints, reversed(endOfShadowPoints))

    def update(self, win):
        self.drawSurface.fill(py.Color('#00000000'))

        lines = []
        for wall in self.seeables:
            corners = self.cornerCheckOrder(wall)
            if self.onScreen(corners):
                lines.append(self.wallShadowCast(wall, corners))

        self.blockUnseeables(lines)

        win.blit(self.drawSurface, (0, 0))


class Bullet(py.sprite.Sprite):

    def __init__(self, direction, pos, angle, dt, *groups):
        super().__init__(*groups)

        self.dt = dt
        self.direction = direction
        self.pos = pos

        self.image = py.Surface((8, 4)).convert_alpha()
        self.image.fill('orange')
        self.rect = self.image.get_frect(center=self.pos)
        self.onScreenPos = self.image.get_frect(center=self.pos)
        self.ySort = self.rect.centery
        self.properties = []
        self.image = py.transform.rotate(self.image, -angle)

    def updateScreenPos(self, offset):
        speed = 1000
        self.onScreenPos.center += self.direction * self.dt * speed
        return self.onScreenPos

    def update(self, dt):
        self.dt = dt



class Gun(py.sprite.Sprite):

    def __init__(self, character, allSprites, *groups):
        super().__init__(allSprites, *groups)

        self.angle = 0
        self.allSprites = allSprites
        self.character = character
        self.dt = None
        self.image = py.Surface((32, 16)).convert_alpha()
        self.image.fill('Brown')
        self.OGimage = self.image.copy()
        self.pos = self.character.onScreenPos.center + vect(60, 0)
        self.rect = self.image.get_frect(center=self.pos)
        self.onScreenPos = self.image.get_frect(center=self.pos)

        self.ySort = self.rect.centery
        self.properties = []
        self.direction = vect(60, 0)

    def updateScreenPos(self, offset):
        self.onScreenPos.center = self.character.onScreenPos.center + self.direction
        return self.onScreenPos

    def rotateToTarget(self, target):
        self.direction = vect()
        tempVect = vect(target) - vect(self.character.onScreenPos.center)
        self.angle = degrees(atan2(tempVect.y, tempVect.x))
        self.direction.from_polar((60, self.angle))
        self.image = py.transform.rotate(self.OGimage, -self.angle)

    def fire(self):
        tempVect = vect()
        tempVect.from_polar((76, self.angle))
        Bullet(self.direction.normalize(), tempVect + self.character.onScreenPos.center, self.angle, self.dt,
               self.allSprites)




    def update(self, dt):
        self.dt = dt


class Character(py.sprite.Sprite):

    def __init__(self, walls, player, dirName='', pos=(0, 0), *groups):
        super().__init__(*groups)

        self.facing = 'N'

        if dirName:
            self.idleImages = {'N': [], 'S': [], 'E': [], 'W': []}
            self.walkingImages = {'N': [], 'S': [], 'E': [], 'W': []}
            path = ASSETSPATH / f'Characters/{dirName}'

            for file in listdir(path):
                if re.search('IDLE', file):
                    self.imageGet(path, file, self.idleImages)
                elif re.search('WALKING', file):
                    self.imageGet(path, file, self.walkingImages)

            self.animationCount = 0
            self.image = self.idleImages[self.facing][0]
            self.animation = True
        else:

            self.image = py.Surface((64, 64))
            self.image.fill('light blue')
            self.animation = False

        self.rect: py.FRect = self.image.get_frect(center=pos)
        self.onScreenPos = self.image.get_frect(center=pos)

        self.hitBox = self.rect

        self.direction = vect((0, 0))
        self.walls = walls
        self.dt = None
        self.ySort = self.rect.centery
        self.properties = []
        self.player = Player
        self.gun = Gun(self, *groups)

    @staticmethod
    def imageGet(path, file, imageDict):
        for direction, array in imageDict.items():
            if re.search(f'_{direction}_', file):
                array.append(py.image.load(f'{path}/{file}').convert_alpha())

    def input(self):
        self.gun.rotateToTarget(CENTER)

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

    def walk(self):
        speed = 200  # 300
        self.rect.centerx += self.direction.x * speed * self.dt
        self.hitBox.centerx = self.rect.centerx
        self.collisionCheck('x')
        self.rect.centery += self.direction.y * speed * self.dt
        self.hitBox.centery = self.rect.centery
        self.collisionCheck('y')

    def animate(self):
        if self.direction:
            self.animationCount += 8 * self.dt

            if self.animationCount >= 3.5:
                self.animationCount = 0

            self.image = self.walkingImages[self.facing][round(self.animationCount)]

        else:
            self.animationCount += 3 * self.dt

            if self.animationCount >= 1.5:
                self.animationCount = 0

            self.image = self.idleImages[self.facing][round(self.animationCount)]

    def updateScreenPos(self, offset):
        self.onScreenPos.topleft = self.rect.topleft - offset
        return self.onScreenPos

    def resetWalls(self, walls):
        self.walls = walls

    def update(self, dt):
        self.dt = dt
        self.input()
        self.walk()
        if self.animation:
            self.animate()


class Player(Character):

    def __init__(self, walls, seeables, unseeables, *groups):
        super().__init__(walls, None, 'Player', (613, 1207), *groups)

        self.lineOfSight = LineOfSight(seeables, unseeables)
        self.onScreenPos.center = CENTER
        self.walls = walls
        self.seeables = seeables
        # self.audioMixer = audioMixer

    def gunControls(self):
        self.gun.rotateToTarget(py.mouse.get_pos())
        if py.mouse.get_just_pressed()[0]:
            self.gun.fire()


    def input(self):
        self.gunControls()
        keys = py.key.get_pressed()
        inputDir = vect()
        if keys[K_w] or CONTROLLER.getJoystick('Up'):
            inputDir.y = -1
            self.facing = 'N'
        if keys[K_s] or CONTROLLER.getJoystick('Down'):
            inputDir.y = 1
            self.facing = 'S'
        if keys[K_a] or CONTROLLER.getJoystick('Left'):
            inputDir.x = -1
            self.facing = 'W'
        if keys[K_d] or CONTROLLER.getJoystick('Right'):
            inputDir.x = 1
            self.facing = 'E'
        if inputDir:
            inputDir.normalize_ip()
            # if not py.mixer.get_busy():
            #     self.audioMixer.playSound('footsteps')
        self.direction = inputDir

    def update(self, dt):
        super().update(dt)
        self.ySort = self.rect.centery


def tileMapSetup(allSprites, walls, unseeables, seeables):
    path = ASSETSPATH / 'Tilemaps'
    map = load_pygame(path / 'untitled.tmx')
    bgGroup = py.sprite.Group()

    for layer in map.layers:

        if layer.id < 3:
            for x, y, surface in layer.tiles():
                Tile((x * 64, y * 64), surface, bgGroup)
    for object in map.objects:
        if object.properties['Seeable']:
            Tile((object.x, object.y), py.Surface((object.width, object.height)), seeables,
                 properties='CollisionRectangles')
        else:
            Tile((object.x, object.y), py.Surface((object.width, object.height)), walls,
                 properties='CollisionRectangles')

    allSprites.addBg(bgGroup)


def debugMapSetup(allSprites, walls, unseeables, seeables):
    wall = py.Surface((64, 128), SRCALPHA)
    wall2 = py.Surface((128, 64), SRCALPHA)
    x = py.Surface((256, 64), SRCALPHA)
    x.fill('blue')
    wall.fill('red')
    wall2.fill('red')

    CollisionTile((677, 1585), wall2, walls, seeables)
    CollisionTile((813, 1380), wall, walls, seeables)
    CollisionTile((913, 1532), x, walls, unseeables)
    # CollisionTile((324, 89), wall2, walls)
    # CollisionTile((89, 320), wall, walls)
    # CollisionTile((200, 320), wall, walls)
    allSprites.addBg(py.sprite.Group())


def main():
    win = py.display.set_mode(SCREENSIZE)
    rr = py.time.Clock()
    running = True
    allSprites = Group()
    walls = py.sprite.Group()
    seeables = py.sprite.Group()
    unseeables = py.sprite.Group()

    debugMapSetup(allSprites, walls, unseeables, seeables)

    player = Player(walls, seeables, unseeables, allSprites)

    character = Character(walls, player, '', (900, 1200), allSprites)

    allSprites.add(walls, seeables, character)

    while running:
        dt = rr.tick(120) / 1000
        win.fill((86, 86, 86))
        for event in py.event.get():
            if event.type == py.QUIT:
                running = False
        allSprites.update(dt)
        allSprites.cDraw(win, player)

        py.display.set_caption(f"FPS: {str(round(rr.get_fps()))}")

        py.display.update()


if __name__ == '__main__':
    py.init()
    main()

from NEA_Constants import *

FILEPATH = ASSETSPATH / 'HUD'
py.font.init()
FONT = py.font.Font(ASSETSPATH / 'arial.ttf', 10)


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
            let = 0
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
            tile.hidden = False
            cut = False

            if self.onScreen((tile.onScreenPos.topleft, tile.onScreenPos.topright, tile.onScreenPos.bottomleft,
                              tile.onScreenPos.bottomright)):
                for lines in linePairs:
                    s0, s1 = vect(lines[0][0]), vect(lines[1][0])
                    edge = s1 - s0
                    playerSide = edge.cross(vect(CENTER) - s0)

                    vects = []
                    points = []
                    clippedPoints = []

                    for line in lines:
                        vects.append(line[1] - line[0])
                        clippedPoint = self.clippedLineCalculation(tile, line)
                        clippedPoints.append(clippedPoint)
                        points += clippedPoint

                    points += self.pointCheck(tile.onScreenPos, any(clippedPoints), *vects)

                    tileSide = edge.cross(vect(tile.onScreenPos.center) - s0)
                    if len(points) > 2 and playerSide * tileSide < 0:
                        arrangedPoints = self.arrangePoints(points.copy())
                        py.draw.polygon(tile.image, (0, 0, 0, 0), arrangedPoints)
                        cut = True

            if cut:
                tile.hidden = py.mask.from_surface(tile.image).count() == 0

    @staticmethod
    def cornerCheckOrder(wall):
        wallPos = wall.onScreenPos
        if wallPos.topleft[0] >= CENTER[0] and wallPos.topleft[1] >= CENTER[1]:
            corners = wallPos.topright, wallPos.bottomright, wallPos.bottomleft
        elif wallPos.topright[0] <= CENTER[0] and wallPos.topright[1] >= CENTER[1]:
            corners = wallPos.topleft, wallPos.bottomleft, wallPos.bottomright
        elif wallPos.bottomleft[0] >= CENTER[0] and wallPos.bottomleft[1] <= CENTER[1]:
            corners = wallPos.topleft, wallPos.topright, wallPos.bottomright
        elif wallPos.bottomright[0] <= CENTER[0] and wallPos.bottomright[1] <= CENTER[1]:
            corners = wallPos.topright, wallPos.topleft, wallPos.bottomleft
        elif wallPos.top >= CENTER[1]:
            corners = wallPos.topleft, wallPos.bottomleft, wallPos.bottomright, wallPos.topright
        elif wallPos.right <= CENTER[0]:
            corners = wallPos.topright, wallPos.topleft, wallPos.bottomleft, wallPos.bottomright
        elif wallPos.bottom <= CENTER[1]:
            corners = wallPos.bottomleft, wallPos.topleft, wallPos.topright, wallPos.bottomright
        elif wallPos.left >= CENTER[0]:
            corners = wallPos.topleft, wallPos.topright, wallPos.bottomright, wallPos.bottomleft
        else:
            corners = wallPos.topright, wallPos.bottomright, wallPos.bottomleft
        return corners

    @staticmethod
    def vectorCalulation(corner, wall):
        cornerVect = (vect(
            corner) - CENTER).normalize()  # the vector from the middle of screen(Character) to the corner. Normalised

        if (not wall.onScreenPos.collidepoint(vect(corner) - cornerVect)
                or cornerVect.y == 0 or cornerVect.x == 0):  # Checks if the corner is an outer corner.

            cornerVect.scale_to_length(2000)
            return cornerVect + CENTER
        return False

    def findShadowScreenCorners(self, shadowPoints):

        screenRect = py.Rect(0,0, *SCREENSIZE)
        newShadowPoints = []
        screenCorners = self.pointCheck(
            screenRect, True, *(vect(p) - vect(CENTER) for p in shadowPoints)
        )

        newShadowPoints.append(screenRect.clipline(CENTER, shadowPoints[0])[1])
        newShadowPoints += reversed(screenCorners)
        newShadowPoints.append(screenRect.clipline(CENTER, shadowPoints[1])[1])

        return newShadowPoints

    def wallShadowCast(self, wall, corners):
        endOfShadowPoints = []
        startOfShadowPoints = []
        allCorners = list(corners)

        for corner in corners:
            endOfShadowPoint = self.vectorCalulation(corner, wall)
            if endOfShadowPoint:
                endOfShadowPoints.insert(0, endOfShadowPoint)
                startOfShadowPoints.append(vect(corner))

        shadowCorners = self.findShadowScreenCorners(endOfShadowPoints)

        allCorners += shadowCorners

        if len(allCorners) > 2:
            py.draw.polygon(self.drawSurface, py.Color(0, 0, 0, 100), allCorners)  # 200

            # for i, corner in enumerate(allCorners, 1):
            #     py.draw.circle(self.drawSurface, 'white', corner, 10)
            #     self.drawSurface.blit(FONT.render(str(i), True, 'Black'), corner - vect(5, 5))


        return list(zip(startOfShadowPoints, reversed(endOfShadowPoints)))

    def update(self, win):
        self.drawSurface.fill(py.Color('#00000000'))

        lines = []
        for wall in self.seeables:
            corners = self.cornerCheckOrder(wall)
            # if self.onScreen(corners):
            lines.append(self.wallShadowCast(wall, corners))

        self.blockUnseeables(lines)

        win.blit(self.drawSurface, (0, 0))


class HealthBar(py.sprite.Sprite):

    def __init__(self, character, *groups):
        super().__init__(*groups)

        self.ogImage = py.Surface((64, 8)).convert_alpha()
        self.image = self.ogImage.copy()
        self.image.fill('#848484')
        self.dt = None
        self.ySort = 1000
        self.properties = []
        self.character = character
        self.rect = self.image.get_frect(center=character.onScreenPos.midtop + vect(0, -12))
        self.onScreenPos = self.rect.copy()
        self.displayedHealth = self.character.getHealth('percent')
        self.hidden = False
        self.blank = py.Surface((64, 8), py.SRCALPHA)
        self.showHealth()

    def showHealth(self):
        self.image = self.ogImage.copy()
        py.draw.rect(self.image, '#00000000', (2, 2, 60, 4))
        py.draw.rect(self.image, 'red', (2, 2, 60 * self.displayedHealth, 4))

    def applyVisibility(self):
        if self.character.hidden:
            self.image = self.blank
        else:
            self.showHealth()

    def updateScreenPos(self, offset):
        self.onScreenPos.center = self.character.onScreenPos.midtop + vect(0, -12)
        self.applyVisibility()
        return self.onScreenPos

    def update(self, dt):
        self.dt = dt
        targetHealth = self.character.getHealth('percent')
        if targetHealth > self.displayedHealth:
            self.displayedHealth = min(targetHealth, self.displayedHealth + dt * 2)
        elif targetHealth < self.displayedHealth:
            self.displayedHealth = max(targetHealth, self.displayedHealth - dt * 2)


class HUD:

    def __init__(self, player):
        self.sprites = py.sprite.Group()
        self.dt = None
        self.healthOutline = py.image.load(FILEPATH / 'HealthBarOutline.png').convert_alpha()
        self.healthOutlineRect = self.healthOutline.get_frect(bottomleft=(112, 704))
        self.portrait = py.image.load(FILEPATH / 'portrait.png').convert_alpha()
        self.portraitRect = self.portrait.get_frect(bottomleft=(16, 704))
        HUDHealthBar(player, self.sprites)

    def update(self, dt, win):
        self.dt = dt
        self.sprites.update(dt)
        self.sprites.draw(win)

        win.blit(self.healthOutline, self.healthOutlineRect)
        win.blit(self.portrait, self.portraitRect)


class HUDHealthBar(py.sprite.Sprite):

    def __init__(self, player, *groups):
        super().__init__(*groups)

        self.images = {}
        imagePath = FILEPATH / 'HealthBars'

        for file in imagePath.glob('HealthBar*.png'):
            self.images[int(file.stem[9:])] = py.image.load(file).convert_alpha()

        self.player = player
        self.displayedHealth = 100

        self.image = self.images[100]
        self.rect = self.image.get_frect(bottomleft=(124, 692))

    @staticmethod
    def roundToNearestPercent(percent):
        return round(round(percent / 100 * 38) / 38 * 100)

    def update(self, dt):
        self.dt = dt
        targetHealth = self.player.getHealth('percent') * 100

        if targetHealth > self.displayedHealth:
            self.displayedHealth = min(targetHealth, self.displayedHealth + dt * 200)
        elif targetHealth < self.displayedHealth:
            self.displayedHealth = max(targetHealth, self.displayedHealth - dt * 200)

        self.image = self.images[self.roundToNearestPercent(self.displayedHealth)]

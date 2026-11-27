from NEA_Constants import *


class Group(py.sprite.Group):

    def __init__(self):
        super().__init__()
        self.offset = vect()
        self.halfScreenSize = CENTER
        self.bg = None
        self.char = None
        self.specialGroup = py.sprite.Group()

    def addBg(self, group):
        self.bg = group

    def addSpecial(self, sprite):
        self.specialGroup.add(sprite)

    def camera(self, target):
        self.offset = vect(target.rect.center) - self.halfScreenSize
        self.offset.x = round(self.offset.x)
        self.offset.y = round(self.offset.y)

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        for specialObject in self.specialGroup:
            specialObject.update(*args, **kwargs)

    def cDraw(self, win, target, dt):
        self.update(dt)
        self.camera(target)
        for bg in self.bg:
            win.blit(bg.image, bg.rect.topleft - self.offset)

        for spr in sorted(self.sprites(), key=lambda sprite: sprite.ySort):
            if spr == target:
                win.blit(spr.image, spr.onScreenPos)

            elif spr.properties == 'Invisible':
                spr.updateScreenPos(self.offset)

            else:
                win.blit(spr.image, spr.updateScreenPos(self.offset))
        target.lineOfSight.update(win)
        for specialObject in self.specialGroup:
            win.blit(specialObject.image, specialObject.updateScreenPos(self.offset))


class Bullet(py.sprite.Sprite):

    def __init__(self, direction, pos, angle, dt, walls, frames, *groups):
        super().__init__(*groups)

        self.dt = dt
        self.direction = direction
        self.pos = pos
        self.frames = [py.transform.rotate(f, -angle) for f in frames]
        self.image = self.frames[0]
        self.rect = self.image.get_frect(center=self.pos)
        self.onScreenPos = self.image.get_frect(center=self.pos)
        self.ySort = self.rect.centery
        self.properties = []
        self.walls = walls
        self.hidden = False
        self.animationCount = 0

    def updateScreenPos(self, offset):
        speed = 2000
        self.rect.center += self.direction * self.dt * speed
        self.onScreenPos.topleft = self.rect.topleft - offset
        return self.onScreenPos

    def offScreen(self):
        if self.onScreenPos.left < 0 or self.onScreenPos.right > SCREENSIZE[
            0] or self.onScreenPos.top < 0 or self.onScreenPos.bottom > SCREENSIZE[1]:
            return True
        return False

    def animate(self):
        self.animationCount += 8 * self.dt
        if self.animationCount >= 3.5:
            self.animationCount = 0
        self.image = self.frames[int(self.animationCount)]

    def update(self, dt):
        self.dt = dt
        self.animate()
        if py.sprite.spritecollideany(self, self.walls) or self.offScreen():
            self.kill()


class Gun(py.sprite.Sprite):

    def __init__(self, character, allSprites, *groups):
        super().__init__(*groups)

        imagePath = ASSETSPATH / 'Gun'
        self.angle = 0
        self.allSprites = allSprites
        self.character = character
        self.dt = None
        self.image = py.image.load(imagePath / 'M16.png').convert_alpha()
        self.unrotatedImage = self.image.copy()
        self.ogImage = self.image.copy()
        self.pos = self.character.onScreenPos.center + vect(60, 0)
        self.rect = self.image.get_frect(center=self.pos)
        self.onScreenPos = self.image.get_frect(center=self.pos)
        self.bulletFrames = [py.image.load(imagePath / 'Bullet' / f'Bullet_{i}.png').convert_alpha() for i in range(4)]

        self.ySort = 10000
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
        self.ogImage = py.transform.rotate(self.unrotatedImage, -self.angle)
        self.image = self.ogImage.copy()
        self.rect.size = self.ogImage.get_size()
        self.onScreenPos.size = self.ogImage.get_size()

    def fire(self, walls, seeables):
        tempVect = vect()
        tempVect.from_polar((76, self.angle))
        Bullet(self.direction.normalize(), tempVect + self.character.rect.center, self.angle, self.dt,
               walls, self.bulletFrames, self.allSprites)

    def update(self, dt):
        self.dt = dt


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
        self.hidden = False

    def updateScreenPos(self, offset):
        self.onScreenPos.topleft = self.rect.topleft - offset
        return self.onScreenPos


class CollisionTile(Tile):

    def __init__(self, pos, image, *groups, **extra):
        super().__init__(pos, image, *groups, **extra)
        xhitBox = extra.setdefault('xHitBox', 0)
        yhitBox = extra.setdefault('yHitBox', 0)

        self.hitbox = self.rect

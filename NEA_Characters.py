from functools import lru_cache

from NEA_Constants import *
from NEA_Sprites import Gun
from NEA_UI import HealthBar, LineOfSight


@lru_cache(maxsize=None)
def loadFrames(dirName):
    idleImages = {'N': [], 'S': [], 'E': [], 'W': []}
    walkingImages = {'N': [], 'S': [], 'E': [], 'W': []}
    path = ASSETSPATH / 'Characters' / dirName
    for file in sorted(listdir(path)):
        if 'IDLE' in file:
            imageDict = idleImages
        elif 'WALKING' in file:
            imageDict = walkingImages
        for direction, array in imageDict.items():
            if f'_{direction}_' in file:
                array.append(py.transform.scale_by(py.image.load(f'{path}/{file}').convert_alpha(), 1.2))
    return idleImages, walkingImages


class GroupData:

    def __init__(self, allSprites, walls, seeables, unseeables):
        self.allSprites = allSprites
        self.walls = walls
        self.seeables = seeables
        self.unseeables = unseeables
        self.player = None


class Character(py.sprite.Sprite):

    def __init__(self, groupData, pos, *, dirName='', health=100, groups=()):
        super().__init__(groupData.allSprites, *groups)
        self.groupData = groupData
        self.facing = 'N'
        self.facingVect = vect(0, -1)
        self.animationCount = 0

        if dirName:
            self.idleImages, self.walkingImages = loadFrames(dirName)
            self.image = self.idleImages[self.facing][0]
            self.animation = True
        else:
            self.image = py.Surface((64, 64), SRCALPHA)
            self.image.fill('light blue')
            self.animation = False

        self.ogImage = self.image.copy()
        self.rect: py.FRect = self.image.get_frect(center=pos)
        self.onScreenPos = self.image.get_frect(center=pos)
        self.hitBox = self.rect.inflate(-40, -40)
        self.direction = vect()
        self.dt = None
        self.ySort = self.rect.centery
        self.properties = []
        self.fullHealth = health
        self.health = health
        self.hidden = False

        self.gun = Gun(self, groupData.allSprites, *groups)
        groupData.allSprites.addSpecial(self.gun)

    def getHealth(self, healthType):
        if healthType == 'percent':
            return self.health / self.fullHealth
        elif healthType == 'full':
            return self.fullHealth
        return self.health

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
        frames, rate = ((self.walkingImages[self.facing], 8) if self.direction else (self.idleImages[self.facing], 3))
        self.animationCount = (self.animationCount + rate * self.dt) % len(frames)
        self.ogImage = frames[int(self.animationCount)]

    def input(self):
        pass

    def updateScreenPos(self, offset):
        self.onScreenPos.topleft = self.rect.topleft - offset
        return self.onScreenPos

    @property
    def walls(self):
        return self.groupData.walls

    def update(self, dt):
        self.dt = dt
        if py.key.get_just_pressed()[K_k]:
            self.health = max(0, self.health - 5)

        self.input()
        self.walk()
        if self.animation:
            self.animate()
        self.ySort = self.rect.centery


class Enemy(Character):

    def __init__(self, groupData, pos, *, dirName='Enemy', health=100, groups=()):
        super().__init__(groupData, pos, dirName=dirName, health=health, groups=(groupData.unseeables, *groups))
        self.playerAngle = None
        self.healthBar = HealthBar(self)
        groupData.allSprites.addSpecial(self.healthBar)
        self.vision = py.FRect()
        self.playerVect = vect(CENTER) - self.onScreenPos.center

    def input(self):
        self.playerVect = vect(CENTER) - self.onScreenPos.center
        self.playerAngle = self.facingVect.angle_to(self.playerVect)
        if 80 > self.playerAngle > -80 and self.playerVect.magnitude_squared() < 100000:
            self.gun.rotateToTarget(CENTER)

    def addPos(self, pos):
        pass


class Player(Character):

    def __init__(self, groupData, pos=(315, 315)):
        super().__init__(groupData, pos, dirName='Player')

        groupData.player = self
        self.lineOfSight = LineOfSight(groupData.seeables, groupData.unseeables)
        self.onScreenPos.center = CENTER
        # self.audioMixer = audioMixer

    def gunControls(self):
        self.gun.rotateToTarget(py.mouse.get_pos())
        if py.mouse.get_just_pressed()[0]:
            self.gun.fire(self.groupData.walls, self.groupData.seeables)

    def animate(self):
        super().animate()
        self.image = self.ogImage

    def input(self):
        self.gunControls()
        keys = py.key.get_pressed()
        inputDir = vect()
        if keys[K_w]:
            inputDir.y = -1
            self.facing = 'N'
        if keys[K_s]:
            inputDir.y = 1
            self.facing = 'S'
        if keys[K_a]:
            inputDir.x = -1
            self.facing = 'W'
        if keys[K_d]:
            inputDir.x = 1
            self.facing = 'E'
        if inputDir:
            inputDir.normalize_ip()
            # if not py.mixer.get_busy():
            #     self.audioMixer.playSound('footsteps')
        self.direction = inputDir

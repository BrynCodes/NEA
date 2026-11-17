from NEA_Constants import *
from NEA_UI import LineOfSight, HealthBar


class Controller:

    def __init__(self):
        pass

    def getJoystick(self, param):
        pass


CONTROLLER = Controller()


class Bullet(py.sprite.Sprite):

    def __init__(self, direction, pos, angle, dt, walls, *groups):
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
        self.walls = walls

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

    def update(self, dt):
        self.dt = dt
        if py.sprite.spritecollideany(self, self.walls) or self.offScreen():
            self.kill()


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
        self.image = py.transform.rotate(self.OGimage, -self.angle)

    def fire(self, walls, seeables):
        tempVect = vect()
        tempVect.from_polar((76, self.angle))
        Bullet(self.direction.normalize(), tempVect + self.character.rect.center, self.angle, self.dt,
               walls, self.allSprites)

    def update(self, dt):
        self.dt = dt


class Character(py.sprite.Sprite):

    def __init__(self, walls, player, dirName, pos, health, *groups):
        super().__init__(*groups)

        self.facing = 'N'
        self.facingVect = vect(0, -1)

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
        self.player = player
        self.gun = Gun(self, *groups)
        self.fullHealth = health
        self.health = health

    @staticmethod
    def imageGet(path, file, imageDict):
        for direction, array in imageDict.items():
            if re.search(f'_{direction}_', file):
                array.append(py.image.load(f'{path}/{file}').convert_alpha())

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


class Enemy(Character):

    def __init__(self, walls, player, allSprites, dirName='', pos=(0, 0), health=100, *groups):
        super().__init__(walls, player, dirName, pos, health, allSprites, *groups)
        self.playerAngle = None
        self.healthBar = HealthBar(self, allSprites)
        self.vision = py.FRect()
        self.playerVect = vect(CENTER) - self.onScreenPos.center

    def input(self):
        self.playerVect = vect(CENTER) - self.onScreenPos.center
        self.playerAngle = self.facingVect.angle_to(self.playerVect)
        if 80 > self.playerAngle > -80:
            self.gun.rotateToTarget(CENTER)


class Player(Character):

    def __init__(self, walls, seeables, unseeables, *groups):
        super().__init__(walls, None, 'Player', (613, 1207), 100, *groups)

        self.lineOfSight = LineOfSight(seeables, unseeables)
        self.onScreenPos.center = CENTER
        self.walls = walls
        self.seeables = seeables
        # self.audioMixer = audioMixer

    def gunControls(self):
        self.gun.rotateToTarget(py.mouse.get_pos())
        if py.mouse.get_just_pressed()[0]:
            self.gun.fire(self.walls, self.seeables)

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

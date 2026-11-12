from NEA_Sprites import Player, Character
from NEA_Tiles import Tile, CollisionTile
from NEA_UI import *

py.font.init()


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

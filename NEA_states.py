from pytmx import TiledTileLayer, TiledObjectGroup

from NEA_Characters import Player, Enemy, GroupData
from NEA_Constants import *
from NEA_Sprites import Group, Tile
from NEA_UI import HUD


class State:

    def __init__(self, *states):
        self.states = states

    def update(self, win, dt):
        for state in self.states:
            state.update(win, dt)


class StateManager:

    def __init__(self, state):
        self.prevState = None
        self.state = state
        self.setState(state)
        self.states = None

    def getState(self, category='class'):
        if category == 'class':
            if type(self.state) == tuple:
                return State(*[self.states[i] for i in self.state])
            else:
                return State(self.states[self.state])
        else:
            if type(self.state) == tuple:
                return self.state[1]
            return self.state

    def setState(self, state, *args):
        self.prevState = self.state[-1] if type(self.state) == tuple else self.state
        self.state = state

    def setAllStates(self, states: dict):
        self.states = states


class GameState:

    def __init__(self):
        self.allSprites = Group()
        self.walls = py.sprite.Group()
        self.seeables = py.sprite.Group()
        self.unseeables = py.sprite.Group()
        self.groupData = GroupData(self.allSprites, self.walls, self.seeables, self.unseeables)
        self.player = Player(self.groupData)
        self.hud = HUD(self.player)

        self.tileMapSetup()

    def tileMapSetup(self):
        path = ASSETSPATH / 'Tilemaps'
        tmx = load_pygame(path / 'room_01_winding_corridor.tmx')

        bgGroup = py.sprite.Group()
        tiles = py.sprite.Group()

        for layer in tmx.layers:

            if isinstance(layer, TiledTileLayer):
                groups = [bgGroup if layer.name == 'Background' else tiles]
                if layer.name == 'Decoration':
                    groups.append(self.unseeables)

                for x, y, surface in layer.tiles():
                    Tile((x * 64, y * 64), surface, *groups)

            elif isinstance(layer, TiledObjectGroup):
                match layer.name:
                    case 'Enemy Locations':
                        self.renderEnemies(layer)
                        break
                    case 'LineOfSight':
                        target = self.seeables
                    case _:
                        target = self.walls

                for obj in layer:
                    Tile((obj.x, obj.y), py.Surface((obj.width, obj.height)), target,
                         properties='Invisible')

        self.allSprites.addBg(bgGroup)
        self.allSprites.add(tiles, self.walls, self.seeables)

    def renderEnemies(self, layer):
        enemies = {}
        for point in layer:
            enemy = enemies.setdefault(point.properties['ID'], Enemy(self.groupData, (point.x, point.y)))
            if enemy is not None:
                enemy.addPos((point.x, point.y))

    def update(self, win, dt):
        self.allSprites.cDraw(win, self.player, dt)
        self.hud.update(dt, win)

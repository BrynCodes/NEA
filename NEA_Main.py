from NEA_Constants import *
from NEA_states import GameState, StateManager


class Game:

    def __init__(self):
        py.init()
        self.gameWindow = py.display.set_mode(SCREENSIZE)
        self.clock = py.time.Clock()
        self.running = True
        gameState = GameState()
        self.stateManager = StateManager('Game')
        states = {'Game': gameState}
        self.stateManager.setAllStates(states)

    def run(self):
        while self.running:
            dt = self.clock.tick(120) / 1000
            self.gameWindow.fill((26, 26, 26))
            for event in py.event.get():
                if event.type == py.QUIT:
                    self.running = False

            self.stateManager.getState().update(self.gameWindow, dt)

            py.display.set_caption(f"FPS: {str(round(self.clock.get_fps()))}")
            py.display.update()


if __name__ == '__main__':
    game = Game()
    game.run()
    py.quit()

"""
A manager manages a specific game context, such as hitting or weather
"""

from blaseball.playball.gamestate import GameState
from blaseball.util.messenger import Messenger


class Manager:
    def __init__(self, state: GameState, messenger: Messenger):
        self.state = state
        self.messenger = messenger

    def start(self):
        raise NotImplementedError("Abstract base class for Manager called!")

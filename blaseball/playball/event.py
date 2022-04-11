"""
Events are things that happen during the game. This is generic, but in a nutshell, an event is:
- something
- becuase of a player, other event, or external factor
- that affects the game state
- and updates the display
- have text
- during a game

"""


from blaseball.playball.ballgame import BallGame

from typing import List


class Event:
    def __init__(self, name=None):
        self.name = name

    def update_game(self, game: BallGame) -> None:
        """
        Update BallGame's internal data to reflect changes in game state.

        Use BallGame's methods when possible.
        """
        pass

    def feed_text(self, debug=False) -> List[str]:
        return [f"Base class Event {self}"]

    def __str__(self):
        name = self.name if self.name is not None else id(self)
        return f"Event {name}"


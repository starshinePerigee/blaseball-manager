"""
This handles fielding, with the end goal of creating an event
which captures everything that has happened.
"""


from blaseball.playball.liveball import LiveBall
from blaseball.playball.event import Event
from blaseball.util.geometry import Coord


class FieldBall(Event):
    """
    This is EARLYFIELDING: as simple as possible so we can build a game and then a UI, since tuning fielding needs UI
    work.

    This does not currently take into account:
    - multiple fielders
    - ball bouncing
    - z axis catchability
    - errors as new balls
    """
    def __init__(self, live: LiveBall):
        self.live = live
        super().__init__(f"Fielding ball from {self.live}")




if __name__ == "__main__":
    l1 = LiveBall(15, 30, 105)
    print(l1)
    l2 = LiveBall(10, -20, 30, Coord(-0.312451, 1.1518293))
    print(l2)

    print(l1.ground_location())
    l1.launch_angle = 20
    print(l1.ground_location())
    l1.field_angle = 90
    print(l1.ground_location())

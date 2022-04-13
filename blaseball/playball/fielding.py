"""
This handles fielding, with the end goal of creating an event
which captures everything that has happened.
"""


from blaseball.playball.event import Event
from blaseball.util.geometry import Coords

import math
from typing import Set


DEGSY = u'\N{DEGREE SIGN}'

GRAVITY_MPH = 80000
WIND_RESISTANCE = 16


class LiveBall:
    """A ball live on the field that must be fielded."""
    def __init__(self, launch_angle, field_angle, speed, origin=Coords(0, 0)):
        self.launch_angle = launch_angle  # 0 is flat horizontal, 90 is straight up, can go negative
        self.field_angle = field_angle  # 0 is right to first base, 90 is to third base, can go 360
        self.speed = speed  # speed of the ball in miles per hour
        self.origin = origin  # the originating point of the ball, from 0,0 for home plate to 1,1 for second base
        # can extend past home base into the field - actual limit depends on the field.

    def _theoretical_distance(self) -> float:
        return self.speed ** 2 * 2 * math.sin(math.radians(self.launch_angle)) / GRAVITY_MPH * 5280

    def flight_time(self) -> float:
        return 2 * self.speed * math.sin(math.radians(self.launch_angle)) / GRAVITY_MPH * 60 * 60

    def distance(self):
        return self._theoretical_distance() - self.flight_time() ** 2 * WIND_RESISTANCE

    def ground_location(self) -> Coords:
        # 0 degs is right along first base
        pos_x = self.distance() * math.cos(math.radians(self.field_angle)) + self.origin.x
        pos_y = self.distance() * math.sin(math.radians(self.field_angle)) + self.origin.y
        return Coords(pos_x, pos_y)

    def __bool__(self):
        return self.speed > 0

    def __str__(self):
        string = f"launch {self.launch_angle:.0f}{DEGSY} field {self.field_angle:.0f}{DEGSY} speed {self.speed:.0f} mph"
        if self.origin:
            string += f" origin ({self.origin.x:.2f}, {self.origin.y:.2f})"
        return string


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
    l2 = LiveBall(10, -20, 30, Coords(-0.312451, 1.1518293))
    print(l2)

    print(l1.ground_location())
    l1.launch_angle = 20
    print(l1.ground_location())
    l1.field_angle = 90
    print(l1.ground_location())

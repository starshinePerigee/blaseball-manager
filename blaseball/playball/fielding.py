"""
This handles fielding, with the end goal of creating an event
which captures everything that has happened.
"""


DEGSY = u'\N{DEGREE SIGN}'


class LiveBall:
    """A ball live on the field that must be fielded."""
    def __init__(self, launch_angle, field_angle, speed, origin=(0, 0)):
        self.launch_angle = launch_angle  # 0 is flat horizontal, 90 is straight up, can go negative
        self.field_angle = field_angle  # 0 is right to first base, 90 is to third base, can go 360
        self.speed = speed  # speed of the ball in miles per hour
        self.origin = origin  # the originating point of the ball, from 0,0 for home plate to 1,1 for second base
        # can extend past home base into the field - actual limit depends on the field.

    def __bool__(self):
        return self.speed > 0

    def __str__(self):
        string = f"launch {self.launch_angle:.0f}{DEGSY} field {self.field_angle:.0f}{DEGSY} speed {self.speed:.0f} mph"
        if self.origin != (0, 0):
            string += f" origin ({self.origin[0]:.2f}, {self.origin[1]:.2f})"
        return string


if __name__ == "__main__":
    l1 = LiveBall(15, 30, 105)
    print(l1)
    l2 = LiveBall(10, -20, 30, (-0.312451, 1.1518293))
    print(l2)
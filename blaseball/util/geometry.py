"""
We're using sympy for geometry handling, but there's a couple quirks - mostly because
sympy is built for symbolic algebra. We wrap this so we can easily access sympy without having to worry
about conversions in the field.
"""

from sympy.geometry import Point
import math

DEGSY = u'\N{DEGREE SIGN}'


class Coords:  # noqa - we don't really care about the abstract methods here.
    def __init__(self, a, b, polar=False):
        """Create a new coordinate; a = x and b = y if polar is false, else a = radius and b = degrees"""
        if polar:
            self.x = a * math.cos(math.radians(b))
            self.y = a * math.sin(math.radians(b))
        else:
            self.x = a
            self.y = b
        self.p = Point(self.x, self.y)

    def theta(self):
        if self.x == 0:
            if self.y == 0:
                theta = 0
            elif self.y > 0:
                theta = 90
            else:
                theta = 360 - 90
        else:
            theta = math.degrees(math.atan(self.y / self.x))
        return theta

    def __bool__(self):
        return self.x != 0 or self.y != 0

    def __str__(self):
        return f"Coords x: {self.x:.0f}' y: {self.y:.0f}' ϴ: {self.theta():.1f}{DEGSY}"


if __name__ == "__main__":
    p1 = Coords(0, 0)
    print(p1)

    p2 = Coords(10, 50.283)
    print(p2)

    p3 = Coords(60.5, 45, True)
    print(p3)

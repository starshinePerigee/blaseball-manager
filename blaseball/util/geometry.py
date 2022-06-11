"""
We were using sympy for geometry handling, but there were too many quirks - so we're switching to Shapely.
Luckily, we were already wrapping Sympy, so shapely just has to drop in here.

It probably would make more sense to use shapely objects directly, or inherit directly, but
we can deal with that later.
"""

from typing import List
from shapely.geometry import Point, Polygon, LineString
import math

DEGSY = u'\N{DEGREE SIGN}'


class Coord(Point):  # noqa - we don't really care about the abstract methods here.
    def __init__(self, a, b, polar=False):
        """Create a new coordinate; a = x and b = y if polar is false, else a = radius and b = degrees"""
        if polar:
            x = a * math.cos(math.radians(b))
            y = a * math.sin(math.radians(b))
        else:
            x = a
            y = b
        super().__init__(x, y)

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

    def move_towards(self, location: "Coord", distance: float) -> "Coord":
        """Returns a coord that's equal to this point moved distance towards another point.
        Can move past the other point."""
        line = LineString([self, location])
        return line.interpolate(distance)

    def __bool__(self):
        return self.x != 0 or self.y != 0

    def __str__(self):
        return f"{self.x:.0f}'x{self.y:.0f}' {self.theta():.1f}{DEGSY}"

    def __repr__(self):
        return F"<Coords(x: {self.x:.3f} y: {self.y:.3f}) θ: {self.theta():.1f}{DEGSY}>"


if __name__ == "__main__":
    p1 = Coord(0, 0)
    print(p1)

    p2 = Coord(10, 50.283)
    print(p2)

    p3 = Coord(60.5, 45, True)
    print(p3)

    pg = Polygon([p1, p2, p3])
    print(f"Area: {pg.area} and perimeter: {pg.length}")

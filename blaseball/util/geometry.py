"""
We were using sympy for geometry handling, but there were too many quirks - so we're switching to Shapely.
Luckily, we were already wrapping Sympy, so shapely just has to drop in here.

It probably would make more sense to use shapely objects directly, or inherit directly, but
we can deal with that later.
"""

from typing import List
from shapely.geometry import Point, Polygon
import math

DEGSY = u'\N{DEGREE SIGN}'


class Coord:  # noqa - we don't really care about the abstract methods here.
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

    def distance(self, other: "Coord") -> float:
        return self.p.distance(other.p)

    def __bool__(self):
        return self.x != 0 or self.y != 0

    def __str__(self):
        return f"Coords x: {self.x:.0f}' y: {self.y:.0f}' θ: {self.theta():.1f}{DEGSY}"

    def __repr__(self):
        return F"<Coords({self.x:.3f}, {self.y:.3f})>"


def polygonize(coords: List[Coord]) -> Polygon:
    """Converts a list of Coords into a sympy polygon"""
    return Polygon([c.p for c in coords])


if __name__ == "__main__":
    p1 = Coord(0, 0)
    print(p1)

    p2 = Coord(10, 50.283)
    print(p2)

    p3 = Coord(60.5, 45, True)
    print(p3)

    pg = polygonize([p1, p2, p3])
    print(f"Area: {pg.area} and perimeter: {pg.length}")

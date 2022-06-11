"""Governs the geometry and special effects of a stadium.

This is vastly premature, so mostly it just holds some coordinate data."""


from blaseball.util.geometry import Coord
from shapely.geometry import Polygon

from typing import Tuple


ANGELS_STADIUM = [330, 365, 396, 389, 330]


class Stadium:
    NUMBER_OF_BASES = 3  # not counting home
    BASEPATH_LENGTH = 90
    MOUND_DISTANCE = 60.5

    HOME_PLATE = Coord(0, 0)
    FIRST_BASE = Coord(BASEPATH_LENGTH, 0)
    SECOND_BASE = Coord(BASEPATH_LENGTH, BASEPATH_LENGTH)
    THIRD_BASE = Coord(0, BASEPATH_LENGTH)
    BASE_LOCATIONS = [HOME_PLATE, FIRST_BASE, SECOND_BASE, THIRD_BASE]
    PITCHING_MOUND = Coord(MOUND_DISTANCE, 45, True)

    WALLS_BONUS = 10

    def __init__(self, distances):
        self.points = [Stadium.HOME_PLATE]
        # here's a fun quibble:
        # stadium dimensions are traditionally reported left to right - left field first.
        # but our geometry has 0 degrees pointing down right field
        # so our points should be clockwise, so we need to reverse the coordinate input
        # hence the "distances[::-1]"
        for i, distance in enumerate(distances[::-1]):
            self.points += [Coord(distance, 90 * i / (len(distances)-1), True)]
        self.polygon = Polygon(self.points)

        self.walls = Stadium.WALLS_BONUS

    def check_home_run(self, location: Coord) -> Tuple[bool, bool]:
        """Check if a ball is a home run and if it hit the wall"""
        outside = not self.polygon.contains(location)
        hit_wall = outside & self.polygon.contains(location.move_towards(self.points[0], self.walls))
        if hit_wall:
            outside = False
        return outside, hit_wall


if __name__ == "__main__":
    s = Stadium(ANGELS_STADIUM)
    print(int(s.polygon.area))
    print(int(s.polygon.length))

    print(s.polygon.contains(Coord(550, 200)))
    print(s.polygon.contains(Coord(360, 100)))
    print(s.polygon.contains(Coord(100, 100)))
"""
Classes for handling location on the field.
"""


class Coords:
    """a helper class to represent an x y pair. This is almost certainly done better elsewhere."""
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __bool__(self):
        return self.x != 0 or self.y != 0

    def __str__(self):
        return f"({self.x:.0f}, {self.y:.0f})"
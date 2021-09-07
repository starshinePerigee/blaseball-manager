"""
This function takes a stat and a player and returns a weighted evaluation of that stat for that player.

It probably didn't need to be it's own module, but it is going to be used in a few different places.
"""

from data.weights import WEIGHTS


def calculate_weighted(player, stat) -> float:
    weight = sum(WEIGHTS[stat].values())
    total = sum(
        [player[s] * WEIGHTS[stat][s] for s in WEIGHTS[stat]]
    )
    return total / weight

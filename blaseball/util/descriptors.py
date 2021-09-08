"""
This helper function creates english descriptors for a player's stats:
overall a more creative and general descriptor of a player's best features
offense a focused description of a player's offensive style
defense a focused description of player's defensive style,
  including if the player leans pitcher, catcher, infield, or outfiled
off-field a player's assets and personality off the field, including constitution and social

This also is used to develop a player's element, which is basically Personality but in a funny way

How does this work? 
1. calculate a set of 3-6 "meta stats" that determine a player's performance
2. run them through the name grid
"""

from data.playerdescriptors import ASPECTS, THRESHOLDS, DESCRIPTOR_DB
from blaseball.util.weighter import calculate_weighted


ASPECT_THRESHOLD = 0.8


def get_descriptor(player, stat) -> str:
    aspect_weights = {aspect: calculate_weighted(player, ("descriptor_" + aspect)) for aspect in ASPECTS[stat]}
    aspects_sorted = sorted((v, k) for k, v in aspect_weights.items())
    aspects_sorted.reverse()
    high_threshold = aspects_sorted[0][0] * ASPECT_THRESHOLD
    total_above_threshold = sum([(1 if x[0] > high_threshold else 0) for x in aspects_sorted])
    if total_above_threshold == 1:
        primary = aspects_sorted[0][1]
        secondary = primary
    elif total_above_threshold == len(aspect_weights):
        primary = 'All'
        secondary = aspects_sorted[0][1]
    elif total_above_threshold == len(aspect_weights) - 1:
        primary = 'Not'
        secondary = aspects_sorted[-1][1]
    else:
        primary = aspects_sorted[0][1]
        secondary = aspects_sorted[1][1]
    descriptor_options = DESCRIPTOR_DB[stat][primary][secondary]

    for option, threshold in zip(descriptor_options, THRESHOLDS):
        if high_threshold < threshold:
            return option
    raise RuntimeError(f"Could not build a descriptor for {stat} and player {player}!"
                       f"High threshold: {high_threshold}, options: {descriptor_options}")


if __name__ == "__main__":
    from blaseball.stats import players
    pb = players.PlayerBase(3)
    for i in range(1001, 1004):
        text = pb[i].text_breakdown().split("\r\n")
        lines = [4, 5, 10, 11, 12, 13, 14, 15] + list(range(53, 94))
        for j in lines:
            #print(f"{j}: {text[j]}")
            print(text[j])

        for stat in ['batting']:
            p_weights = {aspect: calculate_weighted(pb[i], ("descriptor_" + aspect)) for aspect in ASPECTS[stat]}
            p_sorted = sorted((v, k) for k, v in p_weights.items())
            p_sorted.reverse()
            for weight in p_sorted:
                print(f"{weight[1]}: {weight[0]:.3f}")
            thresh = p_sorted[0][0] * ASPECT_THRESHOLD
            print(f"threshold: {thresh:.3f}")

        print("\r\n\r\n--------------------------\r\n\r\n")

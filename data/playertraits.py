"""
This file contains all the base player traits for a player

Define a trait in the following format:
(Name, {stat: value})
"""

PERSONALITY_TRAITS = {
    "annoyed": {"determination": -3, "stability": -3, "insight": 2, },
    "bossy": {"determination": 2, "stability": -2, "insight": -2, },
    "carefree": {"determination": -5, "enthusiasm": 5, "stability": 2, "insight": -3, },
    "serious": {"enthusiasm": -3, "stability": 5, "insight": 2, "mysticism": -3, },
    "adventurous": {"enthusiasm": 4, "stability": -4, "mysticism": 2, },
    "calm": {"enthusiasm": -4, "stability": 6, },
    "charming": {"determination": 2, "insight": -2, "mysticism": 2, },
    "daring": {"determination": 2, "stability": 2, "insight": -4, "mysticism": 2, },
    "determined": {"determination": 6, "enthusiasm": -2, "mysticism": -2, },
    "cautious": {"enthusiasm": -4, "stability": 4, "insight": 6, "mysticism": -3, },
    "humble": {"determination": -2, "enthusiasm": -1, "stability": 6, },
    "energetic": {"enthusiasm": 6, "stability": -2, },
    "hopeful": {"determination": -2, "enthusiasm": 4, "stability": 2, },
    "ambitious": {"determination": 4, "enthusiasm": -3, "insight": 4, },
    "brave": {"determination": 5, "enthusiasm": 2, "insight": -2, },
    "brilliant": {"stability": -2, "insight": 6, "mysticism": 2, },
    "creative": {"stability": -2, "insight": 2, "mysticism": 6, },
}
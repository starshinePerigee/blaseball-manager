"""
This file contains all the base player traits for a player

Define a trait in the following format:
(Name, {stat: value})
"""

PERSONALITY_TRAITS = {
    "adventurous": {"determination": 1, },
    "ambitious": {"enthusiasm": 1, },
    "annoyed": {"stability": 1, },
    "bossy": {"insight": 1, },
    "brave": {"determination": 2, },
    "brilliant": {"enthusiasm": 2, },
    "calm": {"stability": 2, },
    "carefree": {"insight": 2, },
    "cautious": {"determination": 3, },
    "charming": {"enthusiasm": 3, },
    "conceited": {"stability": 3, },
    "considerate": {"insight": 3, },
    "cooperative": {"determination": 1, "enthusiasm": 1, },
    "creative": {"enthusiasm": 1, "stability": 1, },
    "curious": {"stability": 1, "insight": 1, },
    "daring": {"determination": 1, "insight": 1, },
    "demanding": {"determination": 1, "stability": 1, },
    "determined": {"enthusiasm": 1, "insight": 1, },
    "eager": {"determination": 2, "enthusiasm": 2, },
    "energetic": {"enthusiasm": 2, "stability": 2, },
    "faithful": {"stability": 2, "insight": 2, },
    "foolish": {"determination": 2, "insight": 2, },
    "generous": {"determination": 2, "stability": 2, },
    "gentle": {"enthusiasm": 2, "insight": 2, },
    "grumpy": {"determination": 3, "stability": -2, },
    "gullible": {"enthusiasm": 3, "insight": -2, },
    "hardworking": {"determination": -2, "stability": 3, },
    "helpful": {"enthusiasm": -2, "insight": 3, },
}
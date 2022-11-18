"""
Saves a player's descriptors

Use the DescriptorBuilder to generate this code - or not lol

"""

from typing import TYPE_CHECKING
from blaseball.stats import statclasses
from blaseball.stats import stats as s


# notes on element count:
# 4x4 = 16 total
# threshold = 0 means 16 - 4 = 12 total
# allow overlaps but also singles = 16 - 6 = 10 total
# neither overlaps nor singles = 6 total

def describe_element(d: statclasses.Descriptor):
    d.secondary_threshold = 0.7
    d.add_weight(
        s.determination,
        {
            s.determination: "flame",
            s.enthusiasm: "purple",
            s.stability: "steam",
            s.insight: "lava",
        }
    )
    d.add_weight(
        s.enthusiasm,
        {
            s.determination: "electric",
            s.enthusiasm: "wind",
            s.stability: "rain",
            s.insight: "leaf",
        }
    )
    d.add_weight(
        s.stability,
        {
            s.determination: "ash",
            s.enthusiasm: "music",
            s.stability: "ocean",
            s.insight: "gold",
        }
    )
    d.add_weight(
        s.insight,
        {
            s.determination: "robot",
            s.enthusiasm: "space",
            s.stability: "bone",
            s.insight: "dirt",
        }
    )


def describe_offense(d: statclasses.Descriptor):
    # here are your weights:
    """
    slugger = statclasses.Weight("slugging")
    reliable_hitter = statclasses.Weight("contact hitter")
    manufacturer = statclasses.Weight("runs manufacturer")
    utility_hitter = statclasses.Weight("utility hitter")
    """
    d.secondary_threshold = 0.8
    d.add_weight(
        s.slugger,
        {
            s.slugger: "Slugger",
            s.contact: "Power, Contact",
            s.manufacturer: "Power, Speed",
        }
    )
    d.add_weight(
        s.reliable_hitter,
        {
            s.reliable_hitter: "Contact Hitter",
            s.slugger: "Contact, Power",
            s.manufacturer: "Contact, Speed"
        }
    )
    d.add_weight(
        s.manufacturer,
        {
            s.manufacturer: "Baserunner",
            s.contact: "Speed, Contact",
            s.power: "Speed, Power"
        }
    )
    d.add_weight(
        s.utility_hitter, "Utility Hitter"
    )
    d.add_all(
        {0.4: "Garbage", 2.0: "All-Rounder"}
    )


def describe_defense(d: statclasses.Descriptor):
    d.add_weight(
        s.pitching,
        {
            s.pitcher_speed: "Force Pitcher",
            s.pitcher_movement: "Trickery Pitcher",
            s.pitcher_accuracy: "Ruthless Pitcher",
            s.pitcher_special: "Special Pitcher"
        }
    )
    d.add_weight(
        s.defense,
        {
            s.infield: "Infielder",
            s.outfield: "Outfielder",
            s.catcher: "Catcher"
        }
    )


def _add_tiered_stat(descriptor, stat, description):
    descriptor.add_weight(
        stat,
        {0.5: f"Weak {description}", 1.0: f"Solid {description}", 2.0: f"Star {description}"}
    )


def describe_overall(d: statclasses.Descriptor):
    _add_tiered_stat(d, s.overall_power, "Slugger")
    _add_tiered_stat(d, s.overall_smallball, "On-Base Hitter")
    _add_tiered_stat(d, s.overall_fielding, "Fielder")
    _add_tiered_stat(d, s.overall_fastball, "Fastball Pitcher")
    _add_tiered_stat(d, s.overall_trickery, "Curveball Pitcher")
    _add_tiered_stat(d, s.overall_utility, "Utility Player")
    _add_tiered_stat(d, s.overall_captaincy, "Captain")
    _add_tiered_stat(d, s.overall_support, "Support")
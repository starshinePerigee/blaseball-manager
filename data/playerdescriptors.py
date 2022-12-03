"""
Saves a player's descriptors

Use the DescriptorBuilder to generate this code - or not lol

"""

from blaseball.stats import statclasses

# we have to jump through this hoop to avoid a circular import:
pbs = statclasses.all_base.stats


# notes on element count:
# 4x4 = 16 total
# threshold = 0 means 16 - 4 = 12 total
# allow overlaps but also singles = 16 - 6 = 10 total
# neither overlaps nor singles = 6 total

def describe_element(d: statclasses.Descriptor):
    d.secondary_threshold = 0.7
    d.add_weight(
        pbs['determination'],
        {
            pbs['determination']: "flame",
            pbs['enthusiasm']: "purple",
            pbs['stability']: "steam",
            pbs['insight']: "lava",
        }
    )
    d.add_weight(
        pbs['enthusiasm'],
        {
            pbs['determination']: "electric",
            pbs['enthusiasm']: "wind",
            pbs['stability']: "rain",
            pbs['insight']: "leaf",
        }
    )
    d.add_weight(
        pbs['stability'],
        {
            pbs['determination']: "ash",
            pbs['enthusiasm']: "music",
            pbs['stability']: "ocean",
            pbs['insight']: "gold",
        }
    )
    d.add_weight(
        pbs['insight'],
        {
            pbs['determination']: "robot",
            pbs['enthusiasm']: "space",
            pbs['stability']: "bone",
            pbs['insight']: "dirt",
        }
    )


def describe_offense(d: statclasses.Descriptor):
    # here are your weights:
    """
    slugger = statclasses.Weight("slugging")
    contact hitter = statclasses.Weight("contact hitter")
    manufacturer = statclasses.Weight("runs manufacturer")
    utility hitter = statclasses.Weight("utility hitter")
    """
    d.secondary_threshold = 0.8
    d.add_weight(
        pbs['slugging'],
        {
            pbs['slugging']: "Slugger",
            pbs['contact']: "Power, Contact",
            pbs['runs manufacturer']: "Power, Speed",
        }
    )
    d.add_weight(
        pbs['contact hitter'],
        {
            pbs['contact hitter']: "Contact Hitter",
            pbs['slugging']: "Contact, Power",
            pbs['runs manufacturer']: "Contact, Speed"
        }
    )
    d.add_weight(
        pbs['runs manufacturer'],
        {
            pbs['runs manufacturer']: "Baserunner",
            pbs['contact']: "Speed, Contact",
            pbs['power']: "Speed, Power"
        }
    )
    d.add_weight(
        pbs['utility hitter'], "Utility Hitter"
    )
    d.add_all(
        {0.4: "Garbage", 2.0: "All-Rounder"}
    )


def describe_defense(d: statclasses.Descriptor):
    d.add_weight(
        pbs['pitching'],
        {
            pbs['fastball pitcher']: "Force Pitcher",
            pbs['movement pitcher']: "Trickery Pitcher",
            pbs['control pitcher']: "Ruthless Pitcher",
            pbs['special pitcher']: "Special Pitcher"
        }
    )
    d.add_weight(
        pbs['defense'],
        {
            pbs['infielder']: "Infielder",
            pbs['outfielder']: "Outfielder",
            pbs['catcher']: "Catcher"
        }
    )


def _add_tiered_stat(descriptor, stat, description):
    descriptor.add_weight(
        stat,
        {0.5: f"Weak {description}", 1.0: f"Solid {description}", 2.0: f"Star {description}"}
    )


def describe_overall(d: statclasses.Descriptor):
    _add_tiered_stat(d, pbs['overall power'], "Slugger")
    _add_tiered_stat(d, pbs['overall smallball'], "On-Base Hitter")
    _add_tiered_stat(d, pbs['overall fielding'], "Fielder")
    _add_tiered_stat(d, pbs['overall fastball'], "Fastball Pitcher")
    _add_tiered_stat(d, pbs['overall trickery'], "Curveball Pitcher")
    _add_tiered_stat(d, pbs['overall utility'], "Utility Player")
    _add_tiered_stat(d, pbs['overall captaincy'], "Captain")
    _add_tiered_stat(d, pbs['overall support'], "Support")
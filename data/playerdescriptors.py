"""
Saves a player's descriptors

Use the DescriptorBuilder to generate this code
"""

"""

the name grid takes the meta stats and has cells for:
one good stat
each pair of stats
everything but a stat
everything balanced

and then at each level there are descriptors for total stars of the weighting factors
 
"""

ASPECTS = {
    'overall': (
        ['o_power', 'o_smallball', 'o_fielding', 'o_fastball', 'o_tricky', 'o_utility', 'o_coach', 'o_support'],
        [0.4, 0.8, 1.2, 2]
    ),
    'offense': (
        ['slugging', 'contact', 'manufacture', 'utility_hitter'],
        [2]
    ),
    'pitching': (
        ['force', 'trickery', 'accuracy', 'special'],
        [2]
    ),
    'fielding': (
        ['infield', 'outfield', 'catcher', 'pitcher_generic'],
        [2]
    ),
    'personality': (
        ['determination', 'enthusiasm', 'stability', 'insight'],
        [2]
    ),
    'element': (
        ['determination', 'enthusiasm', 'stability', 'insight'],
        [2]
    )
}

OVERALL_DESCRIPTORS = {
    'o_power': {
        'o_power': ['o_power: o_power - 0.4', 'o_power: o_power - 0.8', 'o_power: o_power - 1.2', 'o_power: o_power - 2', ],
        'o_smallball': ['o_power: o_smallball - 0.4', 'o_power: o_smallball - 0.8', 'o_power: o_smallball - 1.2', 'o_power: o_smallball - 2', ],
        'o_fielding': ['o_power: o_fielding - 0.4', 'o_power: o_fielding - 0.8', 'o_power: o_fielding - 1.2', 'o_power: o_fielding - 2', ],
        'o_fastball': ['o_power: o_fastball - 0.4', 'o_power: o_fastball - 0.8', 'o_power: o_fastball - 1.2', 'o_power: o_fastball - 2', ],
        'o_tricky': ['o_power: o_tricky - 0.4', 'o_power: o_tricky - 0.8', 'o_power: o_tricky - 1.2', 'o_power: o_tricky - 2', ],
        'o_utility': ['o_power: o_utility - 0.4', 'o_power: o_utility - 0.8', 'o_power: o_utility - 1.2', 'o_power: o_utility - 2', ],
        'o_coach': ['o_power: o_coach - 0.4', 'o_power: o_coach - 0.8', 'o_power: o_coach - 1.2', 'o_power: o_coach - 2', ],
        'o_support': ['o_power: o_support - 0.4', 'o_power: o_support - 0.8', 'o_power: o_support - 1.2', 'o_power: o_support - 2', ],
    },
    'o_smallball': {
        'o_power': ['o_smallball: o_power - 0.4', 'o_smallball: o_power - 0.8', 'o_smallball: o_power - 1.2', 'o_smallball: o_power - 2', ],
        'o_smallball': ['o_smallball: o_smallball - 0.4', 'o_smallball: o_smallball - 0.8', 'o_smallball: o_smallball - 1.2', 'o_smallball: o_smallball - 2', ],
        'o_fielding': ['o_smallball: o_fielding - 0.4', 'o_smallball: o_fielding - 0.8', 'o_smallball: o_fielding - 1.2', 'o_smallball: o_fielding - 2', ],
        'o_fastball': ['o_smallball: o_fastball - 0.4', 'o_smallball: o_fastball - 0.8', 'o_smallball: o_fastball - 1.2', 'o_smallball: o_fastball - 2', ],
        'o_tricky': ['o_smallball: o_tricky - 0.4', 'o_smallball: o_tricky - 0.8', 'o_smallball: o_tricky - 1.2', 'o_smallball: o_tricky - 2', ],
        'o_utility': ['o_smallball: o_utility - 0.4', 'o_smallball: o_utility - 0.8', 'o_smallball: o_utility - 1.2', 'o_smallball: o_utility - 2', ],
        'o_coach': ['o_smallball: o_coach - 0.4', 'o_smallball: o_coach - 0.8', 'o_smallball: o_coach - 1.2', 'o_smallball: o_coach - 2', ],
        'o_support': ['o_smallball: o_support - 0.4', 'o_smallball: o_support - 0.8', 'o_smallball: o_support - 1.2', 'o_smallball: o_support - 2', ],
    },
    'o_fielding': {
        'o_power': ['o_fielding: o_power - 0.4', 'o_fielding: o_power - 0.8', 'o_fielding: o_power - 1.2', 'o_fielding: o_power - 2', ],
        'o_smallball': ['o_fielding: o_smallball - 0.4', 'o_fielding: o_smallball - 0.8', 'o_fielding: o_smallball - 1.2', 'o_fielding: o_smallball - 2', ],
        'o_fielding': ['o_fielding: o_fielding - 0.4', 'o_fielding: o_fielding - 0.8', 'o_fielding: o_fielding - 1.2', 'o_fielding: o_fielding - 2', ],
        'o_fastball': ['o_fielding: o_fastball - 0.4', 'o_fielding: o_fastball - 0.8', 'o_fielding: o_fastball - 1.2', 'o_fielding: o_fastball - 2', ],
        'o_tricky': ['o_fielding: o_tricky - 0.4', 'o_fielding: o_tricky - 0.8', 'o_fielding: o_tricky - 1.2', 'o_fielding: o_tricky - 2', ],
        'o_utility': ['o_fielding: o_utility - 0.4', 'o_fielding: o_utility - 0.8', 'o_fielding: o_utility - 1.2', 'o_fielding: o_utility - 2', ],
        'o_coach': ['o_fielding: o_coach - 0.4', 'o_fielding: o_coach - 0.8', 'o_fielding: o_coach - 1.2', 'o_fielding: o_coach - 2', ],
        'o_support': ['o_fielding: o_support - 0.4', 'o_fielding: o_support - 0.8', 'o_fielding: o_support - 1.2', 'o_fielding: o_support - 2', ],
    },
    'o_fastball': {
        'o_power': ['o_fastball: o_power - 0.4', 'o_fastball: o_power - 0.8', 'o_fastball: o_power - 1.2', 'o_fastball: o_power - 2', ],
        'o_smallball': ['o_fastball: o_smallball - 0.4', 'o_fastball: o_smallball - 0.8', 'o_fastball: o_smallball - 1.2', 'o_fastball: o_smallball - 2', ],
        'o_fielding': ['o_fastball: o_fielding - 0.4', 'o_fastball: o_fielding - 0.8', 'o_fastball: o_fielding - 1.2', 'o_fastball: o_fielding - 2', ],
        'o_fastball': ['o_fastball: o_fastball - 0.4', 'o_fastball: o_fastball - 0.8', 'o_fastball: o_fastball - 1.2', 'o_fastball: o_fastball - 2', ],
        'o_tricky': ['o_fastball: o_tricky - 0.4', 'o_fastball: o_tricky - 0.8', 'o_fastball: o_tricky - 1.2', 'o_fastball: o_tricky - 2', ],
        'o_utility': ['o_fastball: o_utility - 0.4', 'o_fastball: o_utility - 0.8', 'o_fastball: o_utility - 1.2', 'o_fastball: o_utility - 2', ],
        'o_coach': ['o_fastball: o_coach - 0.4', 'o_fastball: o_coach - 0.8', 'o_fastball: o_coach - 1.2', 'o_fastball: o_coach - 2', ],
        'o_support': ['o_fastball: o_support - 0.4', 'o_fastball: o_support - 0.8', 'o_fastball: o_support - 1.2', 'o_fastball: o_support - 2', ],
    },
    'o_tricky': {
        'o_power': ['o_tricky: o_power - 0.4', 'o_tricky: o_power - 0.8', 'o_tricky: o_power - 1.2', 'o_tricky: o_power - 2', ],
        'o_smallball': ['o_tricky: o_smallball - 0.4', 'o_tricky: o_smallball - 0.8', 'o_tricky: o_smallball - 1.2', 'o_tricky: o_smallball - 2', ],
        'o_fielding': ['o_tricky: o_fielding - 0.4', 'o_tricky: o_fielding - 0.8', 'o_tricky: o_fielding - 1.2', 'o_tricky: o_fielding - 2', ],
        'o_fastball': ['o_tricky: o_fastball - 0.4', 'o_tricky: o_fastball - 0.8', 'o_tricky: o_fastball - 1.2', 'o_tricky: o_fastball - 2', ],
        'o_tricky': ['o_tricky: o_tricky - 0.4', 'o_tricky: o_tricky - 0.8', 'o_tricky: o_tricky - 1.2', 'o_tricky: o_tricky - 2', ],
        'o_utility': ['o_tricky: o_utility - 0.4', 'o_tricky: o_utility - 0.8', 'o_tricky: o_utility - 1.2', 'o_tricky: o_utility - 2', ],
        'o_coach': ['o_tricky: o_coach - 0.4', 'o_tricky: o_coach - 0.8', 'o_tricky: o_coach - 1.2', 'o_tricky: o_coach - 2', ],
        'o_support': ['o_tricky: o_support - 0.4', 'o_tricky: o_support - 0.8', 'o_tricky: o_support - 1.2', 'o_tricky: o_support - 2', ],
    },
    'o_utility': {
        'o_power': ['o_utility: o_power - 0.4', 'o_utility: o_power - 0.8', 'o_utility: o_power - 1.2', 'o_utility: o_power - 2', ],
        'o_smallball': ['o_utility: o_smallball - 0.4', 'o_utility: o_smallball - 0.8', 'o_utility: o_smallball - 1.2', 'o_utility: o_smallball - 2', ],
        'o_fielding': ['o_utility: o_fielding - 0.4', 'o_utility: o_fielding - 0.8', 'o_utility: o_fielding - 1.2', 'o_utility: o_fielding - 2', ],
        'o_fastball': ['o_utility: o_fastball - 0.4', 'o_utility: o_fastball - 0.8', 'o_utility: o_fastball - 1.2', 'o_utility: o_fastball - 2', ],
        'o_tricky': ['o_utility: o_tricky - 0.4', 'o_utility: o_tricky - 0.8', 'o_utility: o_tricky - 1.2', 'o_utility: o_tricky - 2', ],
        'o_utility': ['o_utility: o_utility - 0.4', 'o_utility: o_utility - 0.8', 'o_utility: o_utility - 1.2', 'o_utility: o_utility - 2', ],
        'o_coach': ['o_utility: o_coach - 0.4', 'o_utility: o_coach - 0.8', 'o_utility: o_coach - 1.2', 'o_utility: o_coach - 2', ],
        'o_support': ['o_utility: o_support - 0.4', 'o_utility: o_support - 0.8', 'o_utility: o_support - 1.2', 'o_utility: o_support - 2', ],
    },
    'o_coach': {
        'o_power': ['o_coach: o_power - 0.4', 'o_coach: o_power - 0.8', 'o_coach: o_power - 1.2', 'o_coach: o_power - 2', ],
        'o_smallball': ['o_coach: o_smallball - 0.4', 'o_coach: o_smallball - 0.8', 'o_coach: o_smallball - 1.2', 'o_coach: o_smallball - 2', ],
        'o_fielding': ['o_coach: o_fielding - 0.4', 'o_coach: o_fielding - 0.8', 'o_coach: o_fielding - 1.2', 'o_coach: o_fielding - 2', ],
        'o_fastball': ['o_coach: o_fastball - 0.4', 'o_coach: o_fastball - 0.8', 'o_coach: o_fastball - 1.2', 'o_coach: o_fastball - 2', ],
        'o_tricky': ['o_coach: o_tricky - 0.4', 'o_coach: o_tricky - 0.8', 'o_coach: o_tricky - 1.2', 'o_coach: o_tricky - 2', ],
        'o_utility': ['o_coach: o_utility - 0.4', 'o_coach: o_utility - 0.8', 'o_coach: o_utility - 1.2', 'o_coach: o_utility - 2', ],
        'o_coach': ['o_coach: o_coach - 0.4', 'o_coach: o_coach - 0.8', 'o_coach: o_coach - 1.2', 'o_coach: o_coach - 2', ],
        'o_support': ['o_coach: o_support - 0.4', 'o_coach: o_support - 0.8', 'o_coach: o_support - 1.2', 'o_coach: o_support - 2', ],
    },
    'o_support': {
        'o_power': ['o_support: o_power - 0.4', 'o_support: o_power - 0.8', 'o_support: o_power - 1.2', 'o_support: o_power - 2', ],
        'o_smallball': ['o_support: o_smallball - 0.4', 'o_support: o_smallball - 0.8', 'o_support: o_smallball - 1.2', 'o_support: o_smallball - 2', ],
        'o_fielding': ['o_support: o_fielding - 0.4', 'o_support: o_fielding - 0.8', 'o_support: o_fielding - 1.2', 'o_support: o_fielding - 2', ],
        'o_fastball': ['o_support: o_fastball - 0.4', 'o_support: o_fastball - 0.8', 'o_support: o_fastball - 1.2', 'o_support: o_fastball - 2', ],
        'o_tricky': ['o_support: o_tricky - 0.4', 'o_support: o_tricky - 0.8', 'o_support: o_tricky - 1.2', 'o_support: o_tricky - 2', ],
        'o_utility': ['o_support: o_utility - 0.4', 'o_support: o_utility - 0.8', 'o_support: o_utility - 1.2', 'o_support: o_utility - 2', ],
        'o_coach': ['o_support: o_coach - 0.4', 'o_support: o_coach - 0.8', 'o_support: o_coach - 1.2', 'o_support: o_coach - 2', ],
        'o_support': ['o_support: o_support - 0.4', 'o_support: o_support - 0.8', 'o_support: o_support - 1.2', 'o_support: o_support - 2', ],
    },
}

OFFENSE_DESCRIPTORS = {
    'slugging': {
        'slugging': ['Pure Slugger', ],
        'contact': ['Power, Contact', ],
        'manufacture': ['Power, Speed', ],
        'utility_hitter': ['Power, Utility', ],
    },
    'contact': {
        'slugging': ['Contact, Power', ],
        'contact': ['Pure Contact', ],
        'manufacture': ['Contact, Speed', ],
        'utility_hitter': ['Contact, Utility', ],
    },
    'manufacture': {
        'slugging': ['Speed, Power', ],
        'contact': ['Speed, Contact', ],
        'manufacture': ['Pure Speed', ],
        'utility_hitter': ['Speed, Utility', ],
    },
    'utility_hitter': {
        'slugging': ['Utility, Power', ],
        'contact': ['Utility, Contact', ],
        'manufacture': ['Utility, Speed', ],
        'utility_hitter': ['Pure Utility', ],
    },
    'All': {
        'slugging': ['Powerful All-Rounder', ],
        'contact': ['Contact All-Rounder', ],
        'manufacture': ['Speed All-Rounder', ],
        'utility_hitter': ['Utility All-Rounder', ],
    },
}

FIELDING_DESCRIPTORS = {
    'infield': {
        'infield': ['Pure Infield', ],
        'outfield': ['Infield, Outfield', ],
        'catcher': ['Infield, Catcher', ],
        'pitcher_generic': ['Infield, Pitcher', ],
    },
    'outfield': {
        'infield': ['Outfield, Infield', ],
        'outfield': ['Pure Outfield', ],
        'catcher': ['Outfield, Catcher', ],
        'pitcher_generic': ['Outfield, Pitcher', ],
    },
    'catcher': {
        'infield': ['Catcher, Infield', ],
        'outfield': ['Catcher, Outfield', ],
        'catcher': ['Pure Catcher', ],
        'pitcher_generic': ['Catcher, Pitcher', ],
    },
    'pitcher_generic': {
        'infield': ['Pitcher, Infield', ],
        'outfield': ['Pitcher, Outfield', ],
        'catcher': ['Pitcher, Catcher', ],
        'pitcher_generic': ['Pure Pitcher', ],
    },
    'All': {
        'infield': ['Versatile Infield', ],
        'outfield': ['Versatile Outfield', ],
        'catcher': ['Versatile Catcher', ],
        'pitcher_generic': ['Versatile Pitcher', ],
    },
}

PITCHING_DESCRIPTORS = {
    'force': {
        'force': ['Pure Force', ],
        'trickery': ['Force, Trickery', ],
        'accuracy': ['Force, Accuracy', ],
        'special': ['Force, Special', ],
    },
    'trickery': {
        'force': ['Trickery, Force', ],
        'trickery': ['Pure Trickery', ],
        'accuracy': ['Trickery, Accuracy', ],
        'special': ['Trickery, Special', ],
    },
    'accuracy': {
        'force': ['Accuracy, Force', ],
        'trickery': ['Accuracy, Trickery', ],
        'accuracy': ['Pure Accuracy', ],
        'special': ['Accuracy, Special', ],
    },
    'special': {
        'force': ['Special, Force', ],
        'trickery': ['Special, Trickery', ],
        'accuracy': ['Special, Accuracy', ],
        'special': ['Pure Special', ],
    },
    'All': {
        'force': ['Versatile Force', ],
        'trickery': ['Versatile Trickery', ],
        'accuracy': ['Versatile Accuracy', ],
        'special': ['Versatile Special', ],
    },
}

PERSONALITY_DESCRIPTORS = {
    'determination': {
        'determination': ['determination: determination - 1', 'determination: determination - 2',],
        'enthusiasm': ['determination: enthusiasm - 1', 'determination: enthusiasm - 2',],
        'stability': ['determination: stability - 1', 'determination: stability - 2',],
        'insight': ['determination: insight - 1', 'determination: insight - 2',],
        'mysticism': ['determination: mysticism - 1', 'determination: mysticism - 2',],
    },
    'enthusiasm': {
        'determination': ['enthusiasm: determination - 1', 'enthusiasm: determination - 2',],
        'enthusiasm': ['enthusiasm: enthusiasm - 1', 'enthusiasm: enthusiasm - 2',],
        'stability': ['enthusiasm: stability - 1', 'enthusiasm: stability - 2',],
        'insight': ['enthusiasm: insight - 1', 'enthusiasm: insight - 2',],
        'mysticism': ['enthusiasm: mysticism - 1', 'enthusiasm: mysticism - 2',],
    },
    'stability': {
        'determination': ['stability: determination - 1', 'stability: determination - 2',],
        'enthusiasm': ['stability: enthusiasm - 1', 'stability: enthusiasm - 2',],
        'stability': ['stability: stability - 1', 'stability: stability - 2',],
        'insight': ['stability: insight - 1', 'stability: insight - 2',],
        'mysticism': ['stability: mysticism - 1', 'stability: mysticism - 2',],
    },
    'insight': {
        'determination': ['insight: determination - 1', 'insight: determination - 2',],
        'enthusiasm': ['insight: enthusiasm - 1', 'insight: enthusiasm - 2',],
        'stability': ['insight: stability - 1', 'insight: stability - 2',],
        'insight': ['insight: insight - 1', 'insight: insight - 2',],
        'mysticism': ['insight: mysticism - 1', 'insight: mysticism - 2',],
    },
    'mysticism': {
        'determination': ['mysticism: determination - 1', 'mysticism: determination - 2',],
        'enthusiasm': ['mysticism: enthusiasm - 1', 'mysticism: enthusiasm - 2',],
        'stability': ['mysticism: stability - 1', 'mysticism: stability - 2',],
        'insight': ['mysticism: insight - 1', 'mysticism: insight - 2',],
        'mysticism': ['mysticism: mysticism - 1', 'mysticism: mysticism - 2',],
    },
    'All': {
        'determination': ['All: determination - 1', 'All: determination - 2',],
        'enthusiasm': ['All: enthusiasm - 1', 'All: enthusiasm - 2',],
        'stability': ['All: stability - 1', 'All: stability - 2',],
        'insight': ['All: insight - 1', 'All: insight - 2',],
        'mysticism': ['All: mysticism - 1', 'All: mysticism - 2',],
    },
    'Not': {
        'determination': ['Not: determination - 1', 'Not: determination - 2',],
        'enthusiasm': ['Not: enthusiasm - 1', 'Not: enthusiasm - 2',],
        'stability': ['Not: stability - 1', 'Not: stability - 2',],
        'insight': ['Not: insight - 1', 'Not: insight - 2',],
        'mysticism': ['Not: mysticism - 1', 'Not: mysticism - 2',],
    },
}

ELEMENT_DESCRIPTORS = {
    'determination': {
        'determination': ['flame', ],
        'enthusiasm': ['purple', ],
        'stability': ['steam', ],
        'insight': ['lava', ],
    },
    'enthusiasm': {
        'determination': ['electric', ],
        'enthusiasm': ['wind', ],
        'stability': ['rain', ],
        'insight': ['leaf', ],
    },
    'stability': {
        'determination': ['ash', ],
        'enthusiasm': ['music', ],
        'stability': ['ocean', ],
        'insight': ['gold', ],
    },
    'insight': {
        'determination': ['robot', ],
        'enthusiasm': ['space', ],
        'stability': ['bone', ],
        'insight': ['dirt', ],
    },
}

DESCRIPTOR_DB = {
    'overall': OVERALL_DESCRIPTORS,
    'offense': OFFENSE_DESCRIPTORS,
    'fielding': FIELDING_DESCRIPTORS,
    'pitching': PITCHING_DESCRIPTORS,
    'personality': PERSONALITY_DESCRIPTORS,
    'element': ELEMENT_DESCRIPTORS,
}

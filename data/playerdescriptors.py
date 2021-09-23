"""
Saves a player's descriptors
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
        ['o_slugging', 'o_smallball', 'o_baserunning', 'o_fielding', 'o_fastball', 'o_tricky', 'o_utility', 'o_coach'],
        [0.4, 0.8, 2]
    ),
    'batting': (
        ['slugging', 'smallball', 'manufacture', 'utility_hitter'],
        [0.4, 0.8, 2]
    ),
    'pitching': (
        ['fastball', 'curveball', 'utility_pitcher'],
        [0.4, 0.7, 1.1, 1.5, 2]
    ),
    'fielding': (
        ['infield', 'outfield', 'catcher', 'pitcher_generic'],
        [0.4, 0.8, 2]
    ),
    'personality': (
        ['determination', 'enthusiasm', 'stability', 'insight'],
        [1, 2]
    ),
    'element': (
        ['determination', 'enthusiasm', 'stability', 'insight'],
        [2]
    )
}

OVERALL_DESCRIPTORS = {
    'o_slugging': {
        'o_slugging': ['o_slugging: o_slugging - 0.4', 'o_slugging: o_slugging - 0.8', 'o_slugging: o_slugging - 2',],
        'o_smallball': ['o_slugging: o_smallball - 0.4', 'o_slugging: o_smallball - 0.8', 'o_slugging: o_smallball - 2',],
        'o_baserunning': ['o_slugging: o_baserunning - 0.4', 'o_slugging: o_baserunning - 0.8', 'o_slugging: o_baserunning - 2',],
        'o_fielding': ['o_slugging: o_fielding - 0.4', 'o_slugging: o_fielding - 0.8', 'o_slugging: o_fielding - 2',],
        'o_tricky': ['o_slugging: o_tricky - 0.4', 'o_slugging: o_tricky - 0.8', 'o_slugging: o_tricky - 2',],
        'o_fastball': ['o_slugging: o_fastball - 0.4', 'o_slugging: o_fastball - 0.8', 'o_slugging: o_fastball - 2',],
        'o_utility': ['o_slugging: o_utility - 0.4', 'o_slugging: o_utility - 0.8', 'o_slugging: o_utility - 2',],
        'o_coach': ['o_slugging: o_coach - 0.4', 'o_slugging: o_coach - 0.8', 'o_slugging: o_coach - 2',],
    },
    'o_smallball': {
        'o_slugging': ['o_smallball: o_slugging - 0.4', 'o_smallball: o_slugging - 0.8', 'o_smallball: o_slugging - 2',],
        'o_smallball': ['o_smallball: o_smallball - 0.4', 'o_smallball: o_smallball - 0.8', 'o_smallball: o_smallball - 2',],
        'o_baserunning': ['o_smallball: o_baserunning - 0.4', 'o_smallball: o_baserunning - 0.8', 'o_smallball: o_baserunning - 2',],
        'o_fielding': ['o_smallball: o_fielding - 0.4', 'o_smallball: o_fielding - 0.8', 'o_smallball: o_fielding - 2',],
        'o_tricky': ['o_smallball: o_tricky - 0.4', 'o_smallball: o_tricky - 0.8', 'o_smallball: o_tricky - 2',],
        'o_fastball': ['o_smallball: o_fastball - 0.4', 'o_smallball: o_fastball - 0.8', 'o_smallball: o_fastball - 2',],
        'o_utility': ['o_smallball: o_utility - 0.4', 'o_smallball: o_utility - 0.8', 'o_smallball: o_utility - 2',],
        'o_coach': ['o_smallball: o_coach - 0.4', 'o_smallball: o_coach - 0.8', 'o_smallball: o_coach - 2',],
    },
    'o_baserunning': {
        'o_slugging': ['o_baserunning: o_slugging - 0.4', 'o_baserunning: o_slugging - 0.8', 'o_baserunning: o_slugging - 2',],
        'o_smallball': ['o_baserunning: o_smallball - 0.4', 'o_baserunning: o_smallball - 0.8', 'o_baserunning: o_smallball - 2',],
        'o_baserunning': ['o_baserunning: o_baserunning - 0.4', 'o_baserunning: o_baserunning - 0.8', 'o_baserunning: o_baserunning - 2',],
        'o_fielding': ['o_baserunning: o_fielding - 0.4', 'o_baserunning: o_fielding - 0.8', 'o_baserunning: o_fielding - 2',],
        'o_tricky': ['o_baserunning: o_tricky - 0.4', 'o_baserunning: o_tricky - 0.8', 'o_baserunning: o_tricky - 2',],
        'o_fastball': ['o_baserunning: o_fastball - 0.4', 'o_baserunning: o_fastball - 0.8', 'o_baserunning: o_fastball - 2',],
        'o_utility': ['o_baserunning: o_utility - 0.4', 'o_baserunning: o_utility - 0.8', 'o_baserunning: o_utility - 2',],
        'o_coach': ['o_baserunning: o_coach - 0.4', 'o_baserunning: o_coach - 0.8', 'o_baserunning: o_coach - 2',],
    },
    'o_fielding': {
        'o_slugging': ['o_fielding: o_slugging - 0.4', 'o_fielding: o_slugging - 0.8', 'o_fielding: o_slugging - 2',],
        'o_smallball': ['o_fielding: o_smallball - 0.4', 'o_fielding: o_smallball - 0.8', 'o_fielding: o_smallball - 2',],
        'o_baserunning': ['o_fielding: o_baserunning - 0.4', 'o_fielding: o_baserunning - 0.8', 'o_fielding: o_baserunning - 2',],
        'o_fielding': ['o_fielding: o_fielding - 0.4', 'o_fielding: o_fielding - 0.8', 'o_fielding: o_fielding - 2',],
        'o_tricky': ['o_fielding: o_tricky - 0.4', 'o_fielding: o_tricky - 0.8', 'o_fielding: o_tricky - 2',],
        'o_fastball': ['o_fielding: o_fastball - 0.4', 'o_fielding: o_fastball - 0.8', 'o_fielding: o_fastball - 2',],
        'o_utility': ['o_fielding: o_utility - 0.4', 'o_fielding: o_utility - 0.8', 'o_fielding: o_utility - 2',],
        'o_coach': ['o_fielding: o_coach - 0.4', 'o_fielding: o_coach - 0.8', 'o_fielding: o_coach - 2',],
    },
    'o_tricky': {
        'o_slugging': ['o_tricky: o_slugging - 0.4', 'o_tricky: o_slugging - 0.8', 'o_tricky: o_slugging - 2',],
        'o_smallball': ['o_tricky: o_smallball - 0.4', 'o_tricky: o_smallball - 0.8', 'o_tricky: o_smallball - 2',],
        'o_baserunning': ['o_tricky: o_baserunning - 0.4', 'o_tricky: o_baserunning - 0.8', 'o_tricky: o_baserunning - 2',],
        'o_fielding': ['o_tricky: o_fielding - 0.4', 'o_tricky: o_fielding - 0.8', 'o_tricky: o_fielding - 2',],
        'o_tricky': ['o_tricky: o_tricky - 0.4', 'o_tricky: o_tricky - 0.8', 'o_tricky: o_tricky - 2',],
        'o_fastball': ['o_tricky: o_fastball - 0.4', 'o_tricky: o_fastball - 0.8', 'o_tricky: o_fastball - 2',],
        'o_utility': ['o_tricky: o_utility - 0.4', 'o_tricky: o_utility - 0.8', 'o_tricky: o_utility - 2',],
        'o_coach': ['o_tricky: o_coach - 0.4', 'o_tricky: o_coach - 0.8', 'o_tricky: o_coach - 2',],
    },
    'o_fastball': {
        'o_slugging': ['o_fastball: o_slugging - 0.4', 'o_fastball: o_slugging - 0.8', 'o_fastball: o_slugging - 2',],
        'o_smallball': ['o_fastball: o_smallball - 0.4', 'o_fastball: o_smallball - 0.8', 'o_fastball: o_smallball - 2',],
        'o_baserunning': ['o_fastball: o_baserunning - 0.4', 'o_fastball: o_baserunning - 0.8', 'o_fastball: o_baserunning - 2',],
        'o_fielding': ['o_fastball: o_fielding - 0.4', 'o_fastball: o_fielding - 0.8', 'o_fastball: o_fielding - 2',],
        'o_tricky': ['o_fastball: o_tricky - 0.4', 'o_fastball: o_tricky - 0.8', 'o_fastball: o_tricky - 2',],
        'o_fastball': ['o_fastball: o_fastball - 0.4', 'o_fastball: o_fastball - 0.8', 'o_fastball: o_fastball - 2',],
        'o_utility': ['o_fastball: o_utility - 0.4', 'o_fastball: o_utility - 0.8', 'o_fastball: o_utility - 2',],
        'o_coach': ['o_fastball: o_coach - 0.4', 'o_fastball: o_coach - 0.8', 'o_fastball: o_coach - 2',],
    },
    'o_utility': {
        'o_slugging': ['o_utility: o_slugging - 0.4', 'o_utility: o_slugging - 0.8', 'o_utility: o_slugging - 2',],
        'o_smallball': ['o_utility: o_smallball - 0.4', 'o_utility: o_smallball - 0.8', 'o_utility: o_smallball - 2',],
        'o_baserunning': ['o_utility: o_baserunning - 0.4', 'o_utility: o_baserunning - 0.8', 'o_utility: o_baserunning - 2',],
        'o_fielding': ['o_utility: o_fielding - 0.4', 'o_utility: o_fielding - 0.8', 'o_utility: o_fielding - 2',],
        'o_tricky': ['o_utility: o_tricky - 0.4', 'o_utility: o_tricky - 0.8', 'o_utility: o_tricky - 2',],
        'o_fastball': ['o_utility: o_fastball - 0.4', 'o_utility: o_fastball - 0.8', 'o_utility: o_fastball - 2',],
        'o_utility': ['o_utility: o_utility - 0.4', 'o_utility: o_utility - 0.8', 'o_utility: o_utility - 2',],
        'o_coach': ['o_utility: o_coach - 0.4', 'o_utility: o_coach - 0.8', 'o_utility: o_coach - 2',],
    },
    'o_coach': {
        'o_slugging': ['o_coach: o_slugging - 0.4', 'o_coach: o_slugging - 0.8', 'o_coach: o_slugging - 2',],
        'o_smallball': ['o_coach: o_smallball - 0.4', 'o_coach: o_smallball - 0.8', 'o_coach: o_smallball - 2',],
        'o_baserunning': ['o_coach: o_baserunning - 0.4', 'o_coach: o_baserunning - 0.8', 'o_coach: o_baserunning - 2',],
        'o_fielding': ['o_coach: o_fielding - 0.4', 'o_coach: o_fielding - 0.8', 'o_coach: o_fielding - 2',],
        'o_tricky': ['o_coach: o_tricky - 0.4', 'o_coach: o_tricky - 0.8', 'o_coach: o_tricky - 2',],
        'o_fastball': ['o_coach: o_fastball - 0.4', 'o_coach: o_fastball - 0.8', 'o_coach: o_fastball - 2',],
        'o_utility': ['o_coach: o_utility - 0.4', 'o_coach: o_utility - 0.8', 'o_coach: o_utility - 2',],
        'o_coach': ['o_coach: o_coach - 0.4', 'o_coach: o_coach - 0.8', 'o_coach: o_coach - 2',],
    },
    'All': {
        'o_slugging': ['All: o_slugging - 0.4', 'All: o_slugging - 0.8', 'All: o_slugging - 2',],
        'o_smallball': ['All: o_smallball - 0.4', 'All: o_smallball - 0.8', 'All: o_smallball - 2',],
        'o_baserunning': ['All: o_baserunning - 0.4', 'All: o_baserunning - 0.8', 'All: o_baserunning - 2',],
        'o_fielding': ['All: o_fielding - 0.4', 'All: o_fielding - 0.8', 'All: o_fielding - 2',],
        'o_tricky': ['All: o_tricky - 0.4', 'All: o_tricky - 0.8', 'All: o_tricky - 2',],
        'o_fastball': ['All: o_fastball - 0.4', 'All: o_fastball - 0.8', 'All: o_fastball - 2',],
        'o_utility': ['All: o_utility - 0.4', 'All: o_utility - 0.8', 'All: o_utility - 2',],
        'o_coach': ['All: o_coach - 0.4', 'All: o_coach - 0.8', 'All: o_coach - 2',],
    },
    'Not': {
        'o_slugging': ['Not: o_slugging - 0.4', 'Not: o_slugging - 0.8', 'Not: o_slugging - 2',],
        'o_smallball': ['Not: o_smallball - 0.4', 'Not: o_smallball - 0.8', 'Not: o_smallball - 2',],
        'o_baserunning': ['Not: o_baserunning - 0.4', 'Not: o_baserunning - 0.8', 'Not: o_baserunning - 2',],
        'o_fielding': ['Not: o_fielding - 0.4', 'Not: o_fielding - 0.8', 'Not: o_fielding - 2',],
        'o_tricky': ['Not: o_tricky - 0.4', 'Not: o_tricky - 0.8', 'Not: o_tricky - 2',],
        'o_fastball': ['Not: o_fastball - 0.4', 'Not: o_fastball - 0.8', 'Not: o_fastball - 2',],
        'o_utility': ['Not: o_utility - 0.4', 'Not: o_utility - 0.8', 'Not: o_utility - 2',],
        'o_coach': ['Not: o_coach - 0.4', 'Not: o_coach - 0.8', 'Not: o_coach - 2',],
    },
}

BATTING_DESCRIPTORS = {
    'slugging': {
        'slugging': ['Pathetic Slugger', 'Power Slugger', 'Power Slugger', ],
        'smallball': ['Weak Slugger', 'Complete Hitter', 'Complete Hitter', ],
        'manufacture': ['Weak Slugger', 'Fast Slugger', 'Fast Slugger', ],
        'utility_hitter': ['Weak Slugger', 'Utility Slugger', 'Utility Slugger', ],
    },
    'smallball': {
        'slugging': ['Weak Contact', 'Complete Hitter', 'Complete Hitter', ],
        'smallball': ['Pathetic Contact', 'Pure Contact', 'Pure Contact', ],
        'manufacture': ['Weak Contact', 'Fast Contact', 'Fast Contact', ],
        'utility_hitter': ['Weak Contact', 'Utility Contact', 'Utility Contact', ],
    },
    'manufacture': {
        'slugging': ['Weak Baserunner', 'Fast Slugger', 'Fast Slugger', ],
        'smallball': ['Weak Baserunner', 'Fast Contact', 'Fast Contact', ],
        'manufacture': ['Pathetic Baserunner', 'Pure Runner', 'Pure Runner', ],
        'utility_hitter': ['Weak Baserunner', 'Fast Utility', 'Fast Utility', ],
    },
    'utility_hitter': {
        'slugging': ['Weak Utility', 'Utility Slugger', 'Utility Slugger', ],
        'smallball': ['Weak Utility', 'Utility Contact', 'Utility Contact', ],
        'manufacture': ['Weak Utility', 'Fast Utility', 'Fast Utility', ],
        'utility_hitter': ['Pathetic Utility', 'Pure Utility', 'Pure Utility', ],
    },
    'All': {
        'slugging': ['Versatile Hitter', 'All-Rounder Slugger', 'Power All Star', ],
        'smallball': ['Versatile Contact', 'All-Rounder Contact', 'Contact All Star', ],
        'manufacture': ['Versatile Baserunner', 'Fast All-Rounder', 'Fast All Star', ],
        'utility_hitter': ['Versatile Utility', 'All-Rounder Utility', 'Utility All Star', ],
    },
}

FIELDING_DESCRIPTORS = {
    'infield': {
        'infield': ['Garbage Infield', 'Right Infield', ],
        'outfield': ['Weak Infield', 'Agile Infield', ],
        'catcher': ['Weak Infield', 'Infield / Catcher', ],
        'pitcher_generic': ['Garbage Infield', 'Infield / Backup Pitcher', ],
    },
    'outfield': {
        'infield': ['Weak Outfield', 'Outfield / Shortstop', ],
        'outfield': ['Garbage Outfield', 'Reliable Outfield', ],
        'catcher': ['Weak Outfield', 'Outfield / Catcher', ],
        'pitcher_generic': ['Garbage Outfield', 'Outfield / Backup Pitcher', ],
    },
    'catcher': {
        'infield': ['Weak Catcher', 'Catcher / Infield', ],
        'outfield': ['Weak Catcher', 'Catcher / Outfield', ],
        'catcher': ['Garbage Catcher', 'Reliable Catcher', ],
        'pitcher_generic': ['Garbage Catcher', 'Catcher / Backup Pitcher', ],
    },
    'pitcher_generic': {
        'infield': ['Garbage Infield', 'Infield / Backup Pitcher', ],
        'outfield': ['Garbage Outfield', 'Outfield / Backup Pitcher', ],
        'catcher': ['Garbage Catcher', 'Catcher / Backup Pitcher', ],
        'pitcher_generic': ['Garbage Pitcher', 'Defensive Pitcher', ],
    },
    'All': {
        'infield': ['Defensive Filler', 'Agile Infield', ],
        'outfield': ['Defensive Filler', 'Outfield / Shortstop', ],
        'catcher': ['Defensive Filler', 'Catcher / Backup Defense', ],
        'pitcher_generic': ['Defensive Filler', 'Defensive Pitcher', ],
    },
}

PITCHING_DESCRIPTORS = {
    'fastball': {
        'fastball': ['Weak Fastball', 'Average Fastball', 'Strong Fastball', 'Outstanding Fastball', 'Stellar Fastball', ],
        'curveball': ['Weak Changeup', 'Average Changeup', 'Strong Changeup', 'Outstanding Changeup', 'Stellar Changeup', ],
        'utility_pitcher': ['Weak Fastball', 'Utility Fastball', 'Utility Fastball', 'Outstanding Fastball', 'Stellar Fastball', ],
    },
    'curveball': {
        'fastball': ['Weak Slider', 'Average Slider', 'Strong Slider', 'Outstanding Slider', 'Stellar Slider', ],
        'curveball': ['Weak Curveball', 'Average Curveball', 'Strong Curveball', 'Outstanding Curveball', 'Stellar Curveball', ],
        'utility_pitcher': ['Weak Curveball', 'Utility Curveball', 'Utility Curveball', 'Outstanding Curveball', 'Stellar Curveball', ],
    },
    'utility_pitcher': {
        'fastball': ['Weak Fastball', 'Utility Fastball', 'Utility Fastball', 'Shutdown Fastball', 'Shutdown Fastball', ],
        'curveball': ['Weak Curveball', 'Utility Curveball', 'Utility Curveball', 'Shutdown Curveball', 'Shutdown Curveball', ],
        'utility_pitcher': ['Weak Defense', 'Defensive Pitcher', 'Defensive Pitcher', 'Oustanding Defensive Pitcher', 'Stellar Defensive Pitcher', ],
    },
    'All': {
        'fastball': ['Weak Changeup', 'Average Changeup', 'Strong Changeup', 'Outstanding Changeup', 'Stellar Changeup', ],
        'curveball': ['Weak Curveball', 'Average Curveball', 'Strong Curveball', 'Outstanding Curveball', 'Stellar Curveball', ],
        'utility_pitcher': ['Weak Defense', 'Defensive Pitcher', 'Defensive Pitcher', 'Oustanding Defensive Pitcher', 'Stellar Defensive Pitcher', ],
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
        'determination': ['fire', ],
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
        'enthusiasm': ['rune', ],
        'stability': ['water', ],
        'insight': ['gold', ],
    },
    'insight': {
        'determination': ['robot', ],
        'enthusiasm': ['music', ],
        'stability': ['space', ],
        'insight': ['earth', ],
    },
}

DESCRIPTOR_DB = {
    'overall': OVERALL_DESCRIPTORS,
    'batting': BATTING_DESCRIPTORS,
    'fielding': FIELDING_DESCRIPTORS,
    'pitching': PITCHING_DESCRIPTORS,
    'personality': PERSONALITY_DESCRIPTORS,
    'element': ELEMENT_DESCRIPTORS,
}

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


Here are the stats that make up a player's offense:

Batting:
Power x
Contact xx
Control xx
Discipline x

Baserunning:
Speed xx
Bravery x
Timing x

Edge:
Strategy x 
Sparkle x
Clutch

A player brings one of the four following things:
slugging (power, contact)
smallball (contact, control, speed)
manufacture (discipline, speed, bravery, timing)
utility (control, sparkle, strategy)


Here are the stats that make up a player's defense:
Defense:
Reach 
Reaction 
Throwing 

Pitching:
Force 
Accuracy 
Trickery 
Awareness 

Edge:
Strategy 
Sparkle 
Clutch

if you're fielding (C, 1B, 2B, 3B, SS, RF, CF, LF), you have a balance of the following stats:
- reach
- reaction
- throwing
- strategy (for catchers)

Here are the stats that make up a player's off-field performance:
Constitution
Endurance 
Positivity 
Extroversion 
Introversion 
Recovery 

Social
Teaching 
Patience 
Cool 
Hang 
Support 

These are the stats that make up a player's personality and element:
Determination 
Enthusiasm 
Stability 
Insight 
Mysticism 
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
        [0.4, 0.8, 2]
    ),
    'fielding': (
        ['infield_potential', 'outfield_potential', 'catcher_potential', 'pitcher_potential'],
        [0.4, 0.8, 2]
    ),
    'personality': (
        ['determination', 'enthusiasm', 'stability', 'insight', 'mysticism'],
        [1, 2]
    ),
    'element': (
        ['determination', 'enthusiasm', 'stability', 'insight', 'mysticism'],
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
        'slugging': ['Slugger Only', 'Power Slugger', 'Power Slugger',],
        'smallball': ['Weak Slugger', 'Complete Hitter', 'Complete Hitter',],
        'manufacture': ['Weak Slugger', 'Fast Slugger', 'Fast Slugger',],
        'utility_hitter': ['Weak Slugger', 'Utility Slugger', 'Utility Slugger',],
    },
    'smallball': {
        'slugging': ['Weak Contact', 'Complete Hitter', 'Complete Hitter',],
        'smallball': ['Contact Only', 'Pure Contact', 'Pure Contact',],
        'manufacture': ['Weak Contact', 'Fast Contact', 'Fast Contact',],
        'utility_hitter': ['Weak Contact', 'Utility Contact', 'Utility Contact',],
    },
    'manufacture': {
        'slugging': ['Weak Baserunner', 'Fast Slugger', 'Fast Slugger',],
        'smallball': ['Weak Baserunner', 'Fast Contact', 'Fast Contact',],
        'manufacture': ['Baserunning Only', 'Pure Runner', 'Pure Runner',],
        'utility_hitter': ['Weak Baserunner', 'Fast Utility', 'Fast Utility',],
    },
    'utility_hitter': {
        'slugging': ['Weak Utility', 'Utility Slugger', 'Utility Slugger',],
        'smallball': ['Weak Utility', 'Utility Contact', 'Utility Contact',],
        'manufacture': ['Weak Utility', 'Fast Utility', 'Fast Utility',],
        'utility_hitter': ['Utility Only', 'Pure Utility', 'Pure Utility',],
    },
    'All': {
        'slugging': ['Versatile Hitter', 'All-Rounder Slugger', 'Power All Star',],
        'smallball': ['Versatile Contact', 'All-Rounder Contact', 'Contact All Star',],
        'manufacture': ['Versatile Baserunner', 'Fast All-Rounder', 'Fast All Star',],
        'utility_hitter': ['Versatile Utility', 'All-Rounder Utility', 'Utility All Star',],
    },
    'Not': {
        'slugging': ['Weak Contact', 'Leadoff Batter', 'Ideal Leadoff',],
        'smallball': ['Weak Slugger', 'Cleanup Hitter', 'Cleanup Hitter',],
        'manufacture': ['Slow Hitter', 'Slow Hitter', 'Slow Hitter',],
        'utility_hitter': ['Straightforward', 'Straightforward', 'Straightforward',],
    },
}

FIELDING_DESCRIPTORS = {
    'infield_potential': {
        'infield_potential': ['infield_potential: infield_potential - 0.4', 'infield_potential: infield_potential - 0.8', 'infield_potential: infield_potential - 2',],
        'outfield_potential': ['infield_potential: outfield_potential - 0.4', 'infield_potential: outfield_potential - 0.8', 'infield_potential: outfield_potential - 2',],
        'catcher_potential': ['infield_potential: catcher_potential - 0.4', 'infield_potential: catcher_potential - 0.8', 'infield_potential: catcher_potential - 2',],
        'pitcher_potential': ['infield_potential: pitcher_potential - 0.4', 'infield_potential: pitcher_potential - 0.8', 'infield_potential: pitcher_potential - 2',],
    },
    'outfield_potential': {
        'infield_potential': ['outfield_potential: infield_potential - 0.4', 'outfield_potential: infield_potential - 0.8', 'outfield_potential: infield_potential - 2',],
        'outfield_potential': ['outfield_potential: outfield_potential - 0.4', 'outfield_potential: outfield_potential - 0.8', 'outfield_potential: outfield_potential - 2',],
        'catcher_potential': ['outfield_potential: catcher_potential - 0.4', 'outfield_potential: catcher_potential - 0.8', 'outfield_potential: catcher_potential - 2',],
        'pitcher_potential': ['outfield_potential: pitcher_potential - 0.4', 'outfield_potential: pitcher_potential - 0.8', 'outfield_potential: pitcher_potential - 2',],
    },
    'catcher_potential': {
        'infield_potential': ['catcher_potential: infield_potential - 0.4', 'catcher_potential: infield_potential - 0.8', 'catcher_potential: infield_potential - 2',],
        'outfield_potential': ['catcher_potential: outfield_potential - 0.4', 'catcher_potential: outfield_potential - 0.8', 'catcher_potential: outfield_potential - 2',],
        'catcher_potential': ['catcher_potential: catcher_potential - 0.4', 'catcher_potential: catcher_potential - 0.8', 'catcher_potential: catcher_potential - 2',],
        'pitcher_potential': ['catcher_potential: pitcher_potential - 0.4', 'catcher_potential: pitcher_potential - 0.8', 'catcher_potential: pitcher_potential - 2',],
    },
    'pitcher_potential': {
        'infield_potential': ['pitcher_potential: infield_potential - 0.4', 'pitcher_potential: infield_potential - 0.8', 'pitcher_potential: infield_potential - 2',],
        'outfield_potential': ['pitcher_potential: outfield_potential - 0.4', 'pitcher_potential: outfield_potential - 0.8', 'pitcher_potential: outfield_potential - 2',],
        'catcher_potential': ['pitcher_potential: catcher_potential - 0.4', 'pitcher_potential: catcher_potential - 0.8', 'pitcher_potential: catcher_potential - 2',],
        'pitcher_potential': ['pitcher_potential: pitcher_potential - 0.4', 'pitcher_potential: pitcher_potential - 0.8', 'pitcher_potential: pitcher_potential - 2',],
    },
    'All': {
        'infield_potential': ['All: infield_potential - 0.4', 'All: infield_potential - 0.8', 'All: infield_potential - 2',],
        'outfield_potential': ['All: outfield_potential - 0.4', 'All: outfield_potential - 0.8', 'All: outfield_potential - 2',],
        'catcher_potential': ['All: catcher_potential - 0.4', 'All: catcher_potential - 0.8', 'All: catcher_potential - 2',],
        'pitcher_potential': ['All: pitcher_potential - 0.4', 'All: pitcher_potential - 0.8', 'All: pitcher_potential - 2',],
    },
    'Not': {
        'infield_potential': ['Not: infield_potential - 0.4', 'Not: infield_potential - 0.8', 'Not: infield_potential - 2',],
        'outfield_potential': ['Not: outfield_potential - 0.4', 'Not: outfield_potential - 0.8', 'Not: outfield_potential - 2',],
        'catcher_potential': ['Not: catcher_potential - 0.4', 'Not: catcher_potential - 0.8', 'Not: catcher_potential - 2',],
        'pitcher_potential': ['Not: pitcher_potential - 0.4', 'Not: pitcher_potential - 0.8', 'Not: pitcher_potential - 2',],
    },
}

PITCHING_DESCRIPTORS = {
    'fastball': {
        'fastball': ['fastball: fastball - 0.4', 'fastball: fastball - 0.8', 'fastball: fastball - 2', ],
        'curveball': ['fastball: curveball - 0.4', 'fastball: curveball - 0.8', 'fastball: curveball - 2', ],
        'utility_pitcher': ['fastball: utility_pitcher - 0.4', 'fastball: utility_pitcher - 0.8',
                            'fastball: utility_pitcher - 2', ],
    },
    'curveball': {
        'fastball': ['curveball: fastball - 0.4', 'curveball: fastball - 0.8', 'curveball: fastball - 2', ],
        'curveball': ['curveball: curveball - 0.4', 'curveball: curveball - 0.8', 'curveball: curveball - 2', ],
        'utility_pitcher': ['curveball: utility_pitcher - 0.4', 'curveball: utility_pitcher - 0.8',
                            'curveball: utility_pitcher - 2', ],
    },
    'utility_pitcher': {
        'fastball': ['utility_pitcher: fastball - 0.4', 'utility_pitcher: fastball - 0.8',
                     'utility_pitcher: fastball - 2', ],
        'curveball': ['utility_pitcher: curveball - 0.4', 'utility_pitcher: curveball - 0.8',
                      'utility_pitcher: curveball - 2', ],
        'utility_pitcher': ['utility_pitcher: utility_pitcher - 0.4', 'utility_pitcher: utility_pitcher - 0.8',
                            'utility_pitcher: utility_pitcher - 2', ],
    },
    'All': {
        'fastball': ['All: fastball - 0.4', 'All: fastball - 0.8', 'All: fastball - 2', ],
        'curveball': ['All: curveball - 0.4', 'All: curveball - 0.8', 'All: curveball - 2', ],
        'utility_pitcher': ['All: utility_pitcher - 0.4', 'All: utility_pitcher - 0.8', 'All: utility_pitcher - 2', ],
    },
    'Not': {
        'fastball': ['Not: fastball - 0.4', 'Not: fastball - 0.8', 'Not: fastball - 2', ],
        'curveball': ['Not: curveball - 0.4', 'Not: curveball - 0.8', 'Not: curveball - 2', ],
        'utility_pitcher': ['Not: utility_pitcher - 0.4', 'Not: utility_pitcher - 0.8', 'Not: utility_pitcher - 2', ],
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
        'determination': ['fire',],
        'enthusiasm': ['electric',],
        'stability': ['steam',],
        'insight': ['lava',],
        'mysticism': ['plasma',],
    },
    'enthusiasm': {
        'determination': ['electric',],
        'enthusiasm': ['wind',],
        'stability': ['fog',],
        'insight': ['bird',],
        'mysticism': ['space',],
    },
    'stability': {
        'determination': ['ash',],
        'enthusiasm': ['rain',],
        'stability': ['water',],
        'insight': ['ice',],
        'mysticism': ['gold',],
    },
    'insight': {
        'determination': ['mechancal',],
        'enthusiasm': ['music',],
        'stability': ['leaf',],
        'insight': ['earth',],
        'mysticism': ['peanut',],
    },
    'mysticism': {
        'determination': ['force',],
        'enthusiasm': ['whoa',],
        'stability': ['purple',],
        'insight': ['rune',],
        'mysticism': ['spirit',],
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

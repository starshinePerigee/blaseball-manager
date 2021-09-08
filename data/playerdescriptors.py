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
    'batting': ['slugging', 'smallball', 'manufacture', 'utility_hitter'],
}

THRESHOLDS = [0.4, 0.8, 2]

BATTING_DESCRIPTORS = {
    'slugging': {
        'slugging': ['Weak Slugger', 'Average Slugger', 'Power Slugger', ],
        'smallball': ['Weak Slugger', 'Complete Hitter', 'Complete Clean-Up', ],
        'manufacture': ['Weak Slugger', 'Average Slugger', 'Fast Power Hitter', ],
        'utility_hitter': ['Weak Slugger', 'slugging: utility_hitter - 0.8', 'slugging: utility_hitter - 2', ],
    },
    'smallball': {
        'slugging': ['Weak Contact', 'smallball: slugging - 0.8', 'smallball: slugging - 2', ],
        'smallball': ['Weak Contact', 'smallball: smallball - 0.8', 'smallball: smallball - 2', ],
        'manufacture': ['Weak Contact', 'smallball: manufacture - 0.8', 'smallball: manufacture - 2', ],
        'utility_hitter': ['Weak Contact', 'smallball: utility_hitter - 0.8', 'smallball: utility_hitter - 2', ],
    },
    'manufacture': {
        'slugging': ['Weak Baserunner', 'manufacture: slugging - 0.8', 'manufacture: slugging - 2', ],
        'smallball': ['Weak Baserunner', 'manufacture: smallball - 0.8', 'manufacture: smallball - 2', ],
        'manufacture': ['Weak Baserunner', 'manufacture: manufacture - 0.8', 'manufacture: manufacture - 2', ],
        'utility_hitter': ['Weak Baserunner', 'manufacture: utility_hitter - 0.8', 'manufacture: utility_hitter - 2', ],
    },
    'utility_hitter': {
        'slugging': ['Weak Strategy Hitter', 'utility_hitter: slugging - 0.8', 'utility_hitter: slugging - 2', ],
        'smallball': ['Weak Strategy Hitter', 'utility_hitter: smallball - 0.8', 'utility_hitter: smallball - 2', ],
        'manufacture': ['Weak Strategy Hitter', 'utility_hitter: manufacture - 0.8',
                        'utility_hitter: manufacture - 2', ],
        'utility_hitter': ['Weak Strategy Hitter', 'utility_hitter: utility_hitter - 0.8',
                           'utility_hitter: utility_hitter - 2', ],
    },
    'All': {
        'slugging': ['Versatile Hitter', 'All: slugging - 0.8', 'All: slugging - 2', ],
        'smallball': ['Versatile Hitter', 'All: smallball - 0.8', 'All: smallball - 2', ],
        'manufacture': ['Versatile Baserunner', 'All: manufacture - 0.8', 'All: manufacture - 2', ],
        'utility_hitter': ['Versatile Hitter', 'All: utility_hitter - 0.8', 'All: utility_hitter - 2', ],
    },
    'Not': {
        'slugging': ['Weak Contact', 'Not: slugging - 0.8', 'Not: slugging - 2', ],
        'smallball': ['Weak Slugger', 'Not: smallball - 0.8', 'Not: smallball - 2', ],
        'manufacture': ['Slow Hitter', 'Not: manufacture - 0.8', 'Not: manufacture - 2', ],
        'utility_hitter': ['Versatile Hitter', 'Not: utility_hitter - 0.8', 'Not: utility_hitter - 2', ],
    },
}

DESCRIPTOR_DB = {
    'batting': BATTING_DESCRIPTORS
}
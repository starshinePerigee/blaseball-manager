"""
This is the arbitrary rating dictionary for composite / derived stats.

Note that an 'extra_weight' factor can be applied to lower (or raise, in the case of a negative)
"""

WEIGHTS = {
    # top level stat weights:
    'batting': {
        'power': 2,
        'contact': 3,
        'discipline': 1
    },
    'baserunning': {
        'speed': 3,
        'bravery': 1,
        'timing': 2
    },
    'defense': {
        'reach': 1,
        'grabbiness': 2,
        'calling': 0.5,
    },
    'pitching': {
        'force': 2,
        'accuracy': 1,
        'trickery': 1.5,
        'calling': 0.25
    },
    'edge': {
        'sparkle': 1.5,
        'leadership': 0.5,
        'heckling': 0.5,
        'i.t.': 1
    },
    'vitality': {
        'endurance': 1,
        'positivity': 1,
        'energy': 1,
        'recovery': 1
    },
    'social': {
        'teach': 1.5,
        'cool': 1,
        'hangouts': 1,
        'support': 1
    },
    # summary weights:
    'total_offense': {
        'batting': 2,
        'baserunning': 1,
        'sparkle': 0.25,
    },
    'total_defense_pitching': {
        'pitching': 2,
        'defense': 0.5,
        'sparkle': 0.25,
    },
    'total_defense_fielding': {
        'defense': 2,
        'pitching': 0.5,
    },
    'total_off_field': {
        'vitality': 1.5,
        'social': 1.5,
    },
    # overall descriptors (TBR big time)
    'descriptor_o_slugging': {
        'power': 1,
    },
    'descriptor_o_smallball': {
        'contact': 1,
    },
    'descriptor_o_baserunning': {
        'speed': 1,
    },
    'descriptor_o_fielding': {
        'grabbiness': 1,
    },
    'descriptor_o_fastball': {
        'force': 1,
    },
    'descriptor_o_tricky': {
        'trickery': 1,
    },
    'descriptor_o_utility': {
        'sparkle': 1,
    },
    'descriptor_o_coach': {
        'leadership': 1,
    },
    'descriptor_o_support': {
        'leadership': 1,
    },
    # other descriptor weights:
    'descriptor_slugging': {
        'power': 2,
        'contact': 0.5
    },
    'descriptor_contact': {
        'contact': 2,
        'discipline': 0.5,
    },
    'descriptor_manufacture': {
        'discipline': 1,
        'speed': 2,
        'bravery': 1,
        'timing': 1,
    },
    'descriptor_utility_hitter': {
        'sparkle': 1,
        'contact': 0.5,
        'extra_weight': 0.25
    },
    'descriptor_force': {
        'force': 2,
        'extra_weight': 0.25
    },
    'descriptor_trickery': {
        'trickery': 2,
        'extra_weight': 0.25
    },
    'descriptor_accuracy': {
        'accuracy': 1,
        'extra_weight': 0.25
    },
    'descriptor_special': {
        'sparkle': 2,
        'grabbiness': 1,
    },
    'descriptor_infield': {
        'grabbiness': 1,
    },
    'descriptor_outfield': {
        'reach': 2,
    },
    'descriptor_catcher': {
        'calling': 3,
        'grabbiness': 1,
    },
    'descriptor_pitcher_generic': {
        'force': 2,
        'trickery': 1.5,
        'accuracy': 1,
    },
    'descriptor_determination': {
        'determination': 1,
    },
    'descriptor_enthusiasm': {
        'enthusiasm': 1,
    },
    'descriptor_stability': {
        'stability': 1,
    },
    'descriptor_insight': {
        'insight': 1,
    },
}

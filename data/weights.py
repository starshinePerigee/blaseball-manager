"""
This is the arbitrary rating dictionary for composite / derived stats.

Note that an 'extra_weight' factor can be applied to lower (or raise, in the case of a negative)
"""

WEIGHTS = {
    'batting': {
        'power': 2,
        'contact': 3,
        'control': 1.5,
        'discipline': 1
    },
    'baserunning': {
        'speed': 3,
        'bravery': 1,
        'timing': 2
    },
    'defense': {
        'reach': 1,
        'grabbiness': 1,
        'throwing': 1,
        'calling': 0.5,
        'awareness': 0.25,
    },
    'pitching': {
        'force': 2,
        'accuracy': 1,
        'trickery': 1.5,
        'awareness': 0.5,
        'calling': 0.25
    },
    'edge': {
        'strategy': 1,
        'leadership': 1,
        'heckling': 1,
        'cheers': 1
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
    'total_offense': {
        'batting': 2,
        'baserunning': 1,
    },
    'total_defense_pitching': {
        'pitching': 2,
        'defense': 0.5,
    },
    'total_defense_fielding': {
        'defense': 2,
        'pitching': 0.5,
    },
    'total_off_field': {
        'vitality': 1.5,
        'social': 1.5,
        'edge': 1
    },
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
        'control': 1,
    },
    'descriptor_o_coach': {
        'leadership': 1,
    },
    'descriptor_slugging': {
        'power': 2,
        'contact': 1,
        'extra_weight': 0.5
    },
    'descriptor_smallball': {
        'contact': 2,
        'control': 0.5,
        'speed': 1,
    },
    'descriptor_manufacture': {
        'discipline': 1,
        'speed': 1,
        'bravery': 1,
        'timing': 1,
    },
    'descriptor_utility_hitter': {
        'control': 1,
        'extra_weight': 0.5
    },
    'descriptor_fastball': {
        'force': 2,
        'accuracy': 1
    },
    'descriptor_curveball': {
        'trickery': 2,
        'accuracy': 1
    },
    'descriptor_utility_pitcher': {
        'awareness': 1,
        'calling': 1,
        'grabbiness': 1,
        'extra_weight': 0.25
    },
    'descriptor_infield': {
        'grabbiness': 1,
    },
    'descriptor_outfield': {
        'reach': 2,
        'throwing': 1
    },
    'descriptor_catcher': {
        'calling': 3,
        'awareness': 2,
        'throwing': 1,
    },
    'descriptor_pitcher_generic': {
        'force': 2,
        'trickery': 1.5,
        'accuracy': 1,
        'awareness': 0.5,
        'calling': 0.25
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
    'position_C': {
        'calling': 1,
        'grabbiness': 1,
        'throwing': 1
    }
}

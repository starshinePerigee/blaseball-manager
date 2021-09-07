'''
This is the arbitrary rating dictionary for composite / derived stats.
'''

WEIGHTS = {
    'batting': {
        'power': 2,
        'contact': 3,
        'control': 2,
        'discipline': 1
    },
    'baserunning': {
        'speed': 3,
        'bravery': 1,
        'timing': 2
    },
    'defense': {
        'reach': 1,
        'reaction': 1,
        'throwing': 1,
    },
    'pitching': {
        'force': 2,
        'accuracy': 1,
        'trickery': 1.5,
        'awareness': 0.5,
    },
    'edge': {
        'strategy': 1,
        'sparkle': 1,
        'clutch': 1
    },
    'durability': {
        'endurance': 1,
        'positivity': 1,
        'extroversion': 0.5,
        'introversion': 0.5,
        'recovery': 2
    },
    'social': {
        'teaching': 2,
        'patience': 2,
        'cool': 1,
        'hang': 1,
        'support': 1
    },
    'total_offense': {
        'batting': 2,
        'baserunning': 1,
        'edge': 0.5
    },
    'total_defense_pitching': {
        'pitching': 2,
        'defense': 0.5,
        'edge': 1,
    },
    'total_defense_fielding': {
        'defense': 2,
        'pitching': 0.5,
        'edge': 0.5
    },
    'total_off_field': {
        'constitution': 2,
        'social': 2,
        'edge': 0.5
    }
}
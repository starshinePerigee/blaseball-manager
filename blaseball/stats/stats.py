"""
This module contains all discrete stats definitions and initializations. As such, accessing a stat's class object
is easiest by just pulling it from this module. Because we do this so often, the typical invocation is:

from blaseball.stats import stats as s

and then you can call individual stats as s.my_stat. The core playerbase also exists as s.pb.

Be aware that importing this module runs a lot of code, which then sets up the core playerbase! This is weird and a
little dangerous, and causes some issues in test, but we're commmited at this point.

Also be aware that actual logic for the stats classes is in statclasses.py.
"""

import random
from numpy.random import normal as numpy_normal
import functools
from decimal import Decimal

from blaseball.stats import statclasses
from data import playerdata, playerdescriptors


pb = statclasses.all_base


# CORE PLAYER STATS
def _generate_name(df, cid) -> str:
    """Creates a random name from the playerdata lists.
    Guaranteed to be great."""
    first_name = random.choice(playerdata.PLAYER_FIRST_NAMES)
    last_name = random.choice(playerdata.PLAYER_LAST_NAMES)
    return f"{first_name} {last_name}".title()


name = statclasses.Stat('name', statclasses.Kinds.character, "Wyatt Mason", _generate_name)
name.abbreviate("NAME")


def _generate_number(df, cid) -> int:
    """dumb fun function to create a player number based partially on CID"""
    unusual = random.random() < 0.10

    low_thresh = max(random.randrange(-20, 20, 2), (-20 if unusual else 0))
    high_thresh = random.randrange(45, random.randrange(50, (1000 if unusual else 100)))
    base = cid % 100

    if (base < high_thresh) and (base > low_thresh) and not unusual:
        return base
    else:
        ones = base % 10
        tens = int(((base % high_thresh) + low_thresh) / 10) * 10
        return ones + tens


number = statclasses.Stat('number', statclasses.Kinds.character, -100, _generate_number)
number.abbreviate("#")

team = statclasses.Stat('team', statclasses.Kinds.character, "DETROIT DEFAULT")
team.abbreviate("TEAM")


# THE PERSONALITY FOUR

def _calculate_initial_personality(playerbase, player_index, source_stat):
    stat_modifier = playerbase.players[player_index].get_modifier_total(source_stat)
    return random.random() + stat_modifier


determination = statclasses.Stat(
    "determination",
    statclasses.Kinds.personality,
    1.0,
    functools.partial(_calculate_initial_personality, source_stat="determination")
)
determination.abbreviate("DTR")

enthusiasm = statclasses.Stat(
    "enthusiasm",
    statclasses.Kinds.personality,
    1.0,
    functools.partial(_calculate_initial_personality, source_stat="enthusiasm")
)
enthusiasm.abbreviate("ENT")

stability = statclasses.Stat(
    "stability",
    statclasses.Kinds.personality,
    1.0,
    functools.partial(_calculate_initial_personality, source_stat="stability")
)
stability.abbreviate("STB")

insight = statclasses.Stat(
    "insight",
    statclasses.Kinds.personality,
    1.0,
    functools.partial(_calculate_initial_personality, source_stat="insight")
)
insight.abbreviate("INS")

# # top level ultimate summary weights
total_offense = statclasses.Weight('total offense', statclasses.Kinds.total_weight)
total_offense.abbreviate("TOF")

# these are named with underscores so we can use them in a calculatable
total_defense_pitching = statclasses.Weight("total pitching defense", statclasses.Kinds.total_weight)
total_defense_pitching.display_name = "total defence - pitching"

total_defense_fielding = statclasses.Weight("total fielding defense", statclasses.Kinds.total_weight)
total_defense_fielding.display_name = "total defence - fielding"
# no abbreviations because these are internal stats

total_defense = statclasses.Calculatable(
    'total defense',
    statclasses.Kinds.total_weight,
    value_formula=lambda df, cid: max(total_defense_pitching[cid], total_defense_fielding[cid])
)

total_defense.abbreviate("TDE")

total_off_field = statclasses.Weight('total off-field', statclasses.Kinds.total_weight)
total_off_field.abbreviate("TFD")

# # categories and category weights

batting = statclasses.Weight("batting", statclasses.Kinds.category)
batting.abbreviate("BAT")
batting.weight(total_offense, 2)

baserunning = statclasses.Weight("baserunning", statclasses.Kinds.category)
baserunning.abbreviate("RUN")
baserunning.weight(total_offense, 1)

defense = statclasses.Weight("defense", statclasses.Kinds.category)
defense.abbreviate("DEF")
defense.weight(total_defense_pitching, 0.5)
defense.weight(total_defense_fielding, 2)

pitching = statclasses.Weight("pitching", statclasses.Kinds.category)
pitching.abbreviate("PCH")
pitching.weight(total_defense_pitching, 2)

edge = statclasses.Weight("edge", statclasses.Kinds.category)
edge.abbreviate("EDG")
edge.weight(total_offense, 0.5)
edge.weight(total_defense_pitching, 0.25)
edge.weight(total_defense_fielding, 0.25)

vitality = statclasses.Weight("vitality", statclasses.Kinds.category)
vitality.abbreviate("VIT")
vitality.weight(total_off_field, 1.5)

social = statclasses.Weight("social", statclasses.Kinds.category)
social.abbreviate("SOC")
social.weight(total_off_field, 1.5)


# rating descriptor weights (total weights)

# pulled these out of Player:

#     self["overall descriptor"] = get_descriptor(self, 'overall', False)
#     self["offense descriptor"] = get_descriptor(self, 'offense')
#     if self["is pitcher"]:
#         self["defense descriptor"] = get_descriptor(self, 'pitching')
#     else:
#         self["defense descriptor"] = get_descriptor(self, 'fielding')
#     self['personality descriptor'] = get_descriptor(self, 'personality')


#     self["is pitcher"] = self["pitching"] > self["defense"] * 1.1

# overall weights:
overall_power = statclasses.Weight("overall power")
overall_smallball = statclasses.Weight("overall smallball")
overall_fielding = statclasses.Weight("overall fielding")
overall_fastball = statclasses.Weight("overall fastball")
overall_trickery = statclasses.Weight("overall trickery")
overall_utility = statclasses.Weight("overall utility")
overall_utility.extra_weight = -0.5
overall_captaincy = statclasses.Weight("overall captaincy")
overall_support = statclasses.Weight("overall support")

# offense weights
slugger = statclasses.Weight("slugging")
reliable_hitter = statclasses.Weight("contact hitter")
manufacturer = statclasses.Weight("runs manufacturer")
utility_hitter = statclasses.Weight("utility hitter")
# utility_hitter.extra_weight = 0.25

# pitching weights
pitcher_speed = statclasses.Weight("fastball pitcher")
pitcher_speed.extra_weight = 0.25
pitcher_movement = statclasses.Weight("movement pitcher")
pitcher_speed.extra_weight = 0.25
pitcher_accuracy = statclasses.Weight("control pitcher")
pitcher_accuracy.extra_weight = 0.25
pitcher_special = statclasses.Weight("special pitcher")

# fielding weights
infield = statclasses.Weight("infielder")
outfield = statclasses.Weight("outfielder")
outfield.extra_weight = -0.75
catcher = statclasses.Weight("catcher")
pitcher_generic = statclasses.Weight("pitcher")

# TODO: personality and element handling

# TODO: Descriptors

# Rating stats
# offense

power = statclasses.Rating('power', determination, batting)
power.abbreviate("POW")
power.weight(batting, 2)
power.weight(overall_power, 2)
power.weight(slugger, 2)

contact = statclasses.Rating('contact', enthusiasm, batting)
contact.abbreviate("CON")
contact.weight(batting, 3)
contact.weight(overall_power, 0.5)
contact.weight(overall_smallball, 2)
contact.weight(slugger, 1)
contact.weight(utility_hitter, 1)

discipline = statclasses.Rating('discipline', stability, batting)
discipline.abbreviate("DSC")
discipline.weight(batting, 1)
discipline.weight(overall_power, 1)
discipline.weight(overall_smallball, 1)
discipline.weight(overall_utility, 0.25)
discipline.weight(reliable_hitter, 1)
discipline.weight(manufacturer, 1)

speed = statclasses.Rating('speed', enthusiasm, baserunning)
speed.abbreviate("SPD")
speed.weight(baserunning, 3)
speed.weight(overall_smallball, 1)
speed.weight(manufacturer, 2)

bravery = statclasses.Rating('bravery', determination, baserunning)
bravery.abbreviate("BRV")
bravery.weight(baserunning, 1)
bravery.weight(overall_smallball, 0.5)
bravery.weight(manufacturer, 1)

timing = statclasses.Rating('timing', insight, baserunning)
timing.abbreviate("TMG")
timing.weight(baserunning, 2)
timing.weight(overall_smallball, 0.75)
timing.weight(overall_utility, 0.25)
timing.weight(manufacturer, 1)

# defense

reach = statclasses.Rating('reach', enthusiasm, defense)
reach.abbreviate("RCH")
reach.weight(defense, 1)
reach.weight(overall_fielding, 1)
reach.weight(outfield, 2)

grabbiness = statclasses.Rating('grabbiness', stability, defense)
grabbiness.abbreviate("GRA")
grabbiness.weight(defense, 1.5)
grabbiness.weight(overall_fielding, 1)
grabbiness.weight(pitcher_special, 1)
grabbiness.weight(infield, 1)
grabbiness.weight(catcher, 1)

throwing = statclasses.Rating('throwing', stability, defense)
throwing.abbreviate("THR")
throwing.weight(defense, 1)
throwing.weight(overall_fielding, 0.75)
throwing.weight(outfield, 1)
throwing.weight(catcher, 0.5)
throwing.weight(pitcher_special, .5)

awareness = statclasses.Rating('awareness', insight, defense)
awareness.abbreviate("AWR")
awareness.weight(defense, 0.5)
awareness.weight(overall_fielding, 0.5)
awareness.weight(pitching, 0.25)
awareness.weight(catcher, 1)
awareness.weight(outfield, 0.5)
awareness.weight(pitcher_special, .75)

calling = statclasses.Rating('calling', insight, defense)
calling.abbreviate('CAL')
calling.weight(defense, 0.5)
calling.weight(pitching, 0.25)
calling.weight(overall_fielding, 0.25)
calling.weight(catcher, 3)

force = statclasses.Rating('force')
force.personality = determination
force.category = pitching
force.abbreviate("FOR")
force.weight(pitching, 2)
force.weight(overall_fastball, 2)
force.weight(pitcher_speed, 2)
force.weight(pitcher_generic, 2)

trickery = statclasses.Rating('trickery')
trickery.personality = insight
trickery.category = pitching
trickery.abbreviate("TRK")
trickery.weight(pitching, 1.5)
trickery.weight(overall_trickery, 2)
trickery.weight(overall_utility, 0.25)
trickery.weight(pitcher_movement, 2)
trickery.weight(pitcher_generic, 1.5)

accuracy = statclasses.Rating('accuracy')
accuracy.personality = stability
accuracy.category = pitching
accuracy.abbreviate('ACC')
accuracy.weight(pitching, 1)
accuracy.weight(overall_fastball, 1)
accuracy.weight(overall_trickery, 1)
accuracy.weight(pitcher_accuracy, 2)
accuracy.weight(pitcher_generic, 1)

leadership = statclasses.Rating('leadership')
leadership.personality = determination
leadership.category = edge
leadership.abbreviate("LED")
leadership.weight(edge, 0.5)
leadership.weight(overall_captaincy, 1)

heckling = statclasses.Rating('heckling')
heckling.personality = enthusiasm
heckling.category = edge
heckling.abbreviate('HCK')
heckling.weight(edge, 0.5)
heckling.weight(overall_captaincy, 0.5)

sparkle = statclasses.Rating('sparkle')
sparkle.personality = insight
sparkle.category = edge
sparkle.abbreviate('SPK')
sparkle.weight(edge, 1.5)
sparkle.weight(total_offense, 0.25)
sparkle.weight(total_defense_pitching, 0.25)
sparkle.weight(overall_trickery, 0.25)
sparkle.weight(overall_utility, 1.5)
sparkle.weight(utility_hitter, 1)
sparkle.weight(pitcher_special, 2)

infotech = statclasses.Rating('i.t.')
infotech.personality = stability
infotech.category = edge
infotech.abbreviate('I.T')
infotech.weight(edge, 1)
infotech.weight(overall_utility, 1)

endurance = statclasses.Rating('endurance')
endurance.personality = determination
endurance.category = vitality
endurance.abbreviate("EDR")
endurance.weight(vitality, 1)

energy = statclasses.Rating('energy')
energy.personality = enthusiasm
energy.category = vitality
energy.abbreviate("ENG")
energy.weight(vitality, 1)

positivity = statclasses.Rating('positivity')
positivity.personality = stability
positivity.category = vitality
positivity.abbreviate("POS")
positivity.weight(vitality, 1)

recovery = statclasses.Rating('recovery')
recovery.personality = insight
recovery.category = vitality
recovery.abbreviate("RCV")
recovery.weight(vitality, 1)

cool = statclasses.Rating('cool')
cool.personality = determination
cool.category = social
cool.abbreviate("COO")
cool.weight(social, 1)
cool.weight(overall_utility, 0.5)

hangouts = statclasses.Rating('hangouts')
hangouts.personality = enthusiasm
hangouts.category = social
hangouts.abbreviate("HNG")
hangouts.weight(social, 1)
hangouts.weight(overall_support, 1)

support = statclasses.Rating('support')
support.personality = stability
support.category = social
support.abbreviate("SUP")
support.weight(social, 1)
support.weight(overall_support, 2)

teaching = statclasses.Rating('teaching')
teaching.personality = insight
teaching.category = social
teaching.abbreviate("TCH")
teaching.weight(social, 1)
teaching.weight(overall_captaincy, 1)

# Descriptors

offense_descriptor = statclasses.Descriptor('offense descriptor', default="Unevaluated Hitter")
playerdescriptors.describe_offense(offense_descriptor)

defense_descriptor = statclasses.Descriptor('defense descriptor', default="Unable To Catch A Cold")
playerdescriptors.describe_defense(defense_descriptor)

# personality_descriptor = statclasses.Descriptor('personality descriptor', default="Smol Bean")

overall_descriptor = statclasses.Descriptor('overall descriptor', default="The Observed")
playerdescriptors.describe_overall(overall_descriptor)

# offense_position = statclasses.Descriptor('offense position', default="Bench")
#
# defense_position = statclasses.Descriptor('defense position', default="Bullpen")


# other stats

vibes = statclasses.Stat('vibes', statclasses.Kinds.condition, default=1.0)
vibes.abbreviate("VIB")

stamina = statclasses.Stat('stamina', statclasses.Kinds.condition, 1.0)
stamina.abbreviate('STA')

mood = statclasses.Stat('mood', statclasses.Kinds.condition, 1.0)
mood.abbreviate("MOD")

soul = statclasses.Stat('soul', statclasses.Kinds.condition, 1.0)
soul.abbreviate("SOL")

fingers = statclasses.Stat('fingers', statclasses.Kinds.character, 9)


def _roll_clutch(pb_, cid):
    return random.random()


clutch = statclasses.Stat('clutch', statclasses.Kinds.character, 0.2, initial_function=_roll_clutch)
clutch.abbreviate("CLT")


def _roll_pull(pb_, cid):
    handedness = random.choice([55, 55, 55, 45])
    temp_pull = -1
    while 0 < temp_pull < 90:
        temp_pull = numpy_normal(handedness, 10)
    return temp_pull


pull = statclasses.Stat('pull', statclasses.Kinds.character, -1, initial_function=_roll_pull)

element = statclasses.Descriptor('element', statclasses.Kinds.descriptor, "Basic")
playerdescriptors.describe_element(element)
element.abbreviate("ELE")


# performance statistics

plate_appearances = statclasses.Stat('plate appearances', statclasses.Kinds.performance, 0)

walks = statclasses.Stat('walks', statclasses.Kinds.performance, 0)

sacrifice_hits = statclasses.Stat('sacrifice hits', statclasses.Kinds.performance, 0)

hit_by_pitch = statclasses.Stat('hit by pitch', statclasses.Kinds.performance, 0)


def calc_at_bats(df, cid):
    return plate_appearances[cid] - (walks[cid] + sacrifice_hits[cid] + hit_by_pitch[cid])


at_bats = statclasses.Calculatable('at bats', statclasses.Kinds.derived, calc_at_bats)
at_bats.display_name = 'at-bats'


pitches_called = statclasses.Stat('total pitches called', statclasses.Kinds.performance, 0)

average_called_location, total_called_location = statclasses.build_averaging(
    pitches_called, 'average called location',
)

pitches_thrown = statclasses.Stat("total pitches thrown", statclasses.Kinds.performance, 0)

average_pitch_difficulty, total_pitch_difficulty = statclasses.build_averaging(
    pitches_thrown, 'average pitch difficulty'
)
average_pitch_obscurity, total_pitch_obscurity = statclasses.build_averaging(
    pitches_thrown, 'average pitch obscurity'
)
average_pitch_distance_from_edge, total_pitch_distance_from_edge = statclasses.build_averaging(
    pitches_thrown, 'average pitch distance from edge'
)
average_pitch_distance_from_call, total_pitch_distance_from_call = statclasses.build_averaging(
    pitches_thrown, 'average pitch distance from call'
)
thrown_strike_rate, total_strikes_thrown = statclasses.build_averaging(
    pitches_thrown, 'thrown strike rate', 'total strikes thrown'
)
average_reduction, total_reduction = statclasses.build_averaging(
    pitches_thrown, "average reduction"
)

pitches_seen = statclasses.Stat('pitches seen', statclasses.Kinds.performance, 0)

total_hits = statclasses.Stat('total hits', statclasses.Kinds.performance, 0)

hit_rate = statclasses.Calculatable(
    "hit rate not BA",
    statclasses.Kinds.averaging,
    value_formula=lambda df, cid: total_hits[cid] / pitches_seen[cid] if pitches_seen[cid] > 0 else 0
)

strike_rate, total_strikes_against = statclasses.build_averaging(
    pitches_seen, 'hitting strike rate', 'total strikes against'
)
ball_rate, total_balls_taken = statclasses.build_averaging(pitches_seen, "ball rate", "total balls taken")
foul_rate, total_fouls = statclasses.build_averaging(pitches_seen, "foul rate", "total fouls")
pitch_read_chance, total_pitch_read_percent = statclasses.build_averaging(
    pitches_seen, "pitch read rate", "total pitch read percentage (dumb stat)"
)

average_hit_distance, total_hit_distance = statclasses.build_averaging(total_hits, "average hit distance")
average_exit_velocity, total_exit_velocity = statclasses.build_averaging(
    total_hits, "average exit velocity"
)
average_launch_angle, total_launch_angle = statclasses.build_averaging(total_hits, "average launch angle")
average_field_angle, total_field_angle = statclasses.build_averaging(total_hits, "average field angle")

total_home_runs = statclasses.Stat('total home runs', statclasses.Kinds.performance, 0)
total_runs_seen_from_home = statclasses.Stat('total runs "batted" in', statclasses.Kinds.performance, Decimal('0.0'))


if __name__ == "__main__":
    for p in pb.get_stats_with_kind(statclasses.Kinds.personality):
        print(p.name.upper())
        for s in pb.get_stats_with_personality(p):
            print(f"\t{s}")
    print("\n")
    for c in pb.get_stats_with_kind(statclasses.Kinds.category):
        print(c.name.upper())
        for s in pb.get_stats_with_category(c):
            print(f"\t{s}")

    print("\r\n\r\n")
    for weight in pb.get_stats_with_kind(statclasses.Kinds.weight):
        if "overall" not in weight.name and "total" not in weight.name:
            print(weight.nice_string())
    print('\r\n')
    for weight in pb.get_stats_with_kind(statclasses.Kinds.weight):
        if "overall" in weight.name and "total" not in weight.name:
            print(weight.nice_string())
    print('\r\n')
    for weight in pb.get_stats_with_kind(statclasses.Kinds.weight):
        if "total" in weight.name:
            print(weight.nice_string())

    print("\r\n\r\nPersonality Report:")
    print("TBR")
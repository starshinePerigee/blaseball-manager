import random
import functools

from blaseball.stats import statclasses
from data import playerdata


pb = statclasses.all_base


# CORE PLAYER STATS
def _generate_name(df, cid) -> str:
    """Creates a random name from the playerdata lists.
    Guaranteed to be great."""
    first_name = random.choice(playerdata.PLAYER_FIRST_NAMES)
    last_name = random.choice(playerdata.PLAYER_LAST_NAMES)
    return f"{first_name} {last_name}".title()


name = statclasses.Stat('name', statclasses.Kinds.character, "WYATT MASON", _generate_name)
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
total_offense = statclasses.Weight('total offense')
total_offense.abbreviate("TOF")

total_defense = statclasses.Weight('total defense')
total_defense.abbreviate("TDE")

total_defense_pitching = statclasses.Weight("total pitching defense")
total_defense_fielding = statclasses.Weight("total fielding defense")
# no abbreviations because these are internal stats

total_off_field = statclasses.Weight('total field')
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
#
#
# # rating descriptor weights (total weights)
#
# # overall statclasses.Weights:
# overall_power = statclasses.Weight("overall power")
# overall_smallball = statclasses.Weight("overall smallball")
# overall_fielding = statclasses.Weight("overall fielding")
# overall_fastball = statclasses.Weight("overall fastball")
# overall_trickery = statclasses.Weight("overall trickery")
# overall_utility = statclasses.Weight("overall utility")
# overall_utility.extra_weight = -0.5
# overall_captaincy = statclasses.Weight("overall captaincy")
# overall_support = statclasses.Weight("overall support")
#
# # offense statclasses.Weights
# slugger = statclasses.Weight("slugging")
# reliable_hitter = statclasses.Weight("contact hitter")
# manufacturer = statclasses.Weight("runs manufacturer")
# utility_hitter = statclasses.Weight("utility hitter")
# utility_hitter.extra_weight = 0.25
#
# # pitching statclasses.Weights
# pitcher_speed = statclasses.Weight("fastball pitcher")
# pitcher_speed.extra_weight = 0.25
# pitcher_movement = statclasses.Weight("movement pitcher")
# pitcher_speed.extra_weight = 0.25
# pitcher_accuracy = statclasses.Weight("control pitcher")
# pitcher_accuracy.extra_weight = 0.25
# pitcher_special = statclasses.Weight("special pitcher")
#
# # fielding statclasses.Weights
# infield = statclasses.Weight("infielder")
# outfield = statclasses.Weight("outfielder")
# outfield.extra_weight = -0.75
# catcher = statclasses.Weight("catcher")
# pitcher_generic = statclasses.Weight("pitcher")
#
# # TODO: personality and element handling
#
# # TODO: Descriptors
#
# # Rating stats
# # offense
#
# power, base_power = statclasses.build_rating('power', determination, batting)
# power.abbreviate("POW")
# power.weight(batting, 2)
# power.weight(overall_power, 2)
# power.weight(slugger, 2)
#
# contact, base_contact = statclasses.build_rating('contact', enthusiasm, batting)
# contact.abbreviate("CON")
# contact.weight(batting, 3)
# contact.weight(overall_power, 0.5)
# contact.weight(overall_smallball, 2)
# contact.weight(slugger, 1)
# contact.weight(utility_hitter, 1)
#
# discipline, base_discipline = statclasses.build_rating('discipline', stability, batting)
# discipline.abbreviate("DSC")
# discipline.weight(batting, 1)
# discipline.weight(overall_power, 1)
# discipline.weight(overall_smallball, 1)
# discipline.weight(overall_utility, 0.25)
# discipline.weight(reliable_hitter, 1)
# discipline.weight(manufacturer, 1)
#
# speed, base_speed = statclasses.build_rating('speed', enthusiasm, baserunning)
# speed.abbreviate("SPD")
# speed.weight(baserunning, 3)
# speed.weight(overall_smallball, 1)
# speed.weight(manufacturer, 2)
#
# bravery, base_bravery = statclasses.build_rating('bravery', determination, baserunning)
# bravery.abbreviate("BRV")
# bravery.weight(baserunning, 1)
# bravery.weight(overall_smallball, 0.5)
# bravery.weight(manufacturer, 1)
#
# timing, base_timing = statclasses.build_rating('timing', insight, baserunning)
# timing.abbreviate("TMG")
# timing.weight(baserunning, 2)
# timing.weight(overall_smallball, 0.75)
# timing.weight(overall_utility, 0.25)
# timing.weight(manufacturer, 1)
#
# # defense
#
# reach, base_reach = statclasses.build_rating('reach', enthusiasm, defense)
# reach.abbreviate("RCH")
# reach.weight(defense, 1)
# reach.weight(overall_fielding, 1)
# reach.weight(outfield, 2)
#
# grabbiness, base_grabbiness = statclasses.build_rating('grabbiness', stability, defense)
# grabbiness.abbreviate("GRA")
# grabbiness.weight(defense, 1.5)
# grabbiness.weight(overall_fielding, 1)
# grabbiness.weight(pitcher_special, 1)
# grabbiness.weight(infield, 1)
# grabbiness.weight(catcher, 1)
#
# throwing = statclasses.build_rating('throwing', stability, defense)
# throwing.abbreviate("THR")
# throwing.weight(defense, 1)
# throwing.weight(overall_fielding, 0.75)
# throwing.weight(outfield, 1)
# throwing.weight(catcher, 0.5)
# throwing.weight(pitcher_special, .5)
#
# awareness = statclasses.build_rating('awareness', insight, defense)
# awareness.abbreviate("AWR")
# awareness.weight(defense, 0.5)
# awareness.weight(overall_fielding, 0.5)
# awareness.weight(pitching, 0.25)
# awareness.weight(catcher, 1)
# awareness.weight(outfield, 0.5)
# awareness.weight(pitcher_special, .75)
#
# calling = statclasses.build_rating('calling', insight, defense)
# calling.abbreviate('CAL')
# calling.weight(defense, 0.5)
# calling.weight(pitching, 0.25)
# calling.weight(overall_fielding, 0.25)
# calling.weight(catcher, 3)
#
# force = statclasses.build_rating('force')
# force.personality = determination
# force.category = pitching
# force.abbreviate("FOR")
# force.weight(pitching, 2)
# force.weight(overall_fastball, 2)
# force.weight(pitcher_speed, 2)
# force.weight(pitcher_generic, 2)
#
# trickery = statclasses.build_rating('trickery')
# trickery.personality = insight
# trickery.category = pitching
# trickery.abbreviate("TRK")
# trickery.weight(pitching, 1.5)
# trickery.weight(overall_trickery, 2)
# trickery.weight(overall_utility, 0.25)
# trickery.weight(pitcher_movement, 2)
# trickery.weight(pitcher_generic, 1.5)
#
# accuracy = statclasses.build_rating('accuracy')
# accuracy.personality = stability
# accuracy.category = pitching
# accuracy.abbreviate('ACC')
# accuracy.weight(pitching, 1)
# accuracy.weight(overall_fastball, 1)
# accuracy.weight(overall_trickery, 1)
# accuracy.weight(pitcher_accuracy, 2)
# accuracy.weight(pitcher_generic, 1)
#
# leadership = statclasses.build_rating('leadership')
# leadership.personality = determination
# leadership.category = edge
# leadership.abbreviate("LED")
# leadership.weight(edge, 0.5)
# leadership.weight(overall_captaincy, 1)
#
# heckling = statclasses.build_rating('heckling')
# heckling.personality = enthusiasm
# heckling.category = edge
# heckling.abbreviate('HCK')
# heckling.weight(edge, 0.5)
# heckling.weight(overall_captaincy, 0.5)
#
# sparkle = statclasses.build_rating('sparkle')
# sparkle.personality = insight
# sparkle.category = edge
# sparkle.abbreviate('SPK')
# sparkle.weight(edge, 1.5)
# sparkle.weight(total_offense, 0.25)
# sparkle.weight(total_defense_pitching, 0.25)
# sparkle.weight(overall_trickery, 0.25)
# sparkle.weight(overall_utility, 1.5)
# sparkle.weight(utility_hitter, 1)
# sparkle.weight(pitcher_special, 2)
#
# infotech = statclasses.build_rating('i.t.')
# infotech.personality = stability
# infotech.category = edge
# infotech.abbreviate('I.T')
# infotech.weight(edge, 1)
# infotech.weight(overall_utility, 1)
#
# endurance = statclasses.build_rating('endurance')
# endurance.personality = determination
# endurance.category = vitality
# endurance.abbreviate("EDR")
# endurance.weight(vitality, 1)
#
# energy = statclasses.build_rating('energy')
# energy.personality = enthusiasm
# energy.category = vitality
# energy.abbreviate("ENG")
# energy.weight(vitality, 1)
#
# positivity = statclasses.build_rating('positivity')
# positivity.personality = stability
# positivity.category = vitality
# positivity.abbreviate("POS")
# positivity.weight(vitality, 1)
#
# recovery = statclasses.build_rating('recovery')
# recovery.personality = insight
# recovery.category = vitality
# recovery.abbreviate("RCV")
# recovery.weight(vitality, 1)
#
# cool = statclasses.build_rating('cool')
# cool.personality = determination
# cool.category = social
# cool.abbreviate("COO")
# cool.weight(social, 1)
# cool.weight(overall_utility, 0.5)
#
# hangouts = statclasses.build_rating('hangouts')
# hangouts.personality = enthusiasm
# hangouts.category = social
# hangouts.abbreviate("HNG")
# hangouts.weight(social, 1)
# hangouts.weight(overall_support, 1)
#
# support = statclasses.build_rating('support')
# support.personality = stability
# support.category = social
# support.abbreviate("SUP")
# support.weight(social, 1)
# support.weight(overall_support, 2)
#
# teaching = statclasses.build_rating('teaching')
# teaching.personality = insight
# teaching.category = social
# teaching.abbreviate("TCH")
# teaching.weight(social, 1)
# teaching.weight(overall_captaincy, 1)
# #
# for stat in s['rating']:
#     stat.default = 0
#
#
# # Descriptors
#
# overall_descriptor = Calculatable('overall descriptor', statclasses.Kinds.descriptor)
# overall_descriptor.default = "The Observed"
#
# offense_descriptor = Calculatable('offense descriptor', statclasses.Kinds.descriptor)
# offense_descriptor.default = "Unevaluated Hitter"
#
# defense_descriptor = Calculatable('defense descriptor', statclasses.Kinds.descriptor)
# defense_descriptor.default = "Unable To Catch A Cold"
#
# personality_descriptor = Calculatable('personality descriptor', statclasses.Kinds.descriptor)
# personality_descriptor.default = "Smol Bean"
#
# offense_position = Calculatable('offense position', statclasses.Kinds.descriptor)
# offense_position.default = 'Bench'
#
# defense_position = Calculatable('defense position', statclasses.Kinds.descriptor)
# defense_position.default = 'Bullpen'
#
#
#
# vibes = Stat('vibes', statclasses.Kinds.condition)
# vibes.abbreviate("VIB")
# vibes.default = 1.0
#
# stamina = Stat('stamina', statclasses.Kinds.condition)
# stamina.abbreviate('STA')
# stamina.default = 1.0
#
# mood = Stat('mood', statclasses.Kinds.condition)
# mood.abbreviate("MOD")
# mood.default = 1.0
#
# soul = Stat('soul', statclasses.Kinds.condition)
# soul.abbreviate("SOL")
# soul.default = 1.0
#
# fingers = Stat('fingers', statclasses.Kinds.character)
# fingers.default = 9
#
# is_pitcher = Stat('is pitcher', statclasses.Kinds.character)
# is_pitcher.default = False
#
# clutch = Stat('clutch', statclasses.Kinds.character)
# clutch.default = 0.2
# clutch.abbreviate("CLT")
#
# pull = Stat('pull', statclasses.Kinds.character)
# pull.default = -1
#
# element = Stat('element', statclasses.Kinds.character)
# element.default = "Basic"
# element.abbreviate("ELE")

#
# all_stats.at_bats = Stat('at bats', 'performance')
#
# pitches_called = Stat('total pitches called', 'performance')
#
# average_called_location = Stat('average called location', 'averaging')
# average_called_location.total_stat = 'total pitches called'
#
# pitches_thrown = Stat('total pitches thrown', 'performance')
#
# pitch_stats = [
#     'average pitch difficulty',
#     'average pitch obscurity',
#     'average pitch distance from edge',
#     'average pitch distance from call',
#     'thrown strike rate',
#     'average reduction'
# ]
#
# for stat in pitch_stats:
#     new_stat = Stat(stat, 'averaging')
#     new_stat.total_stat = 'total pitches thrown'
#
# pitches_seen = Stat('pitches seen', 'performance')
#
# hit_stats = ['strike rate', 'ball rate', 'foul rate', 'hit rate', 'pitch read chance']
# for stat in hit_stats:
#     new_stat = Stat(stat, 'averaging')
#     new_stat.total_stat = 'pitches seen'
#
# total_hits = Stat('total hits', 'performance')
#
# average_hit_distance = Stat('average hit distance', 'averaging')
# average_hit_distance.total_stat = 'total hits'
#
# exit_velo = Stat('average exit velocity', 'averaging')
# exit_velo.total_stat = 'total hits'
#
# total_home_runs = Stat('total home runs', 'performance')
#
# for stat in all_stats['performance'] + all_stats['averaging']:
#     stat.default = 0
#
#
# if __name__ == "__main__":
#     for p in all_stats[Kinds.personality]:
#         print(p.name.upper())
#         for s in all_stats[p]:
#             print(f"\t{s}")
#     print("\n")
#     for c in all_stats[Kinds.category]:
#         print(c.name.upper())
#         for s in all_stats[c]:
#             print(f"\t{s}")
#
#     print("\r\n\r\n")
#     for weight in all_stats[Kinds.weight]:
#         if "overall" not in weight.name and "total" not in weight.name:
#             print(weight.nice_string())
#     print('\r\n')
#     for weight in all_stats[Kinds.weight]:
#         if "overall" in weight.name and "total" not in weight.name:
#             print(weight.nice_string())
#     print('\r\n')
#     for weight in all_stats[Kinds.weight]:
#         if "total" in weight.name:
#             print(weight.nice_string())
#
#     print("\r\n\r\nPersonality Report:")
#     print("TBR")
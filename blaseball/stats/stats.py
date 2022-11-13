import random

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


name = statclasses.Stat('name', statclasses.Kinds.character, _generate_name)
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


number = statclasses.Stat('number', statclasses.Kinds.character, _generate_number)
number.abbreviate("#")


# THE PERSONALITY FOUR

base_determination = statclasses.BasePersonality("base determination")
determination = statclasses.Rating(
    "determination",
    base_determination,
)
determination.abbreviate("DTR")

base_enthusiasm = statclasses.BasePersonality("base enthusiasm")
enthusiasm = statclasses.Rating(
    "enthusiasm",
    base_enthusiasm
)
enthusiasm.abbreviate("ENT")

base_stability = statclasses.BasePersonality("base stability")
stability = statclasses.Rating(
    "stability",
    base_stability
)
stability.abbreviate("STB")

base_insight = statclasses.BasePersonality("base insight")
insight = statclasses.Rating(
    "insight",
    base_insight
)
insight.abbreviate("INS")




# # personality descriptor weights:
# s.weight_determination = Weight("determination weight")
# s.weight_enthusiasm = Weight("enthusiasm weight")
# s.weight_stability = Weight("stability weight")
# s.weight_insight = Weight("insight weight")
#
#
# # top level ultimate summary weights
# s.total_offense = Weight('total offense', Kinds.total_weight)
# s.total_offense.abbreviate("TOF")
# s.total_offense.default = -1
#
# s.total_defense = Weight('total defense', Kinds.total_weight)
# s.total_defense.abbreviate("TDE")
# s.total_defense.default = -1
#
# s.total_off_field = Weight('total off-field', Kinds.total_weight)
# s.total_off_field.abbreviate("TFD")
# s.total_off_field.default = -1
#
# s.total_defense_pitching = Weight("total pitching defense")
# s.total_defense_fielding = Weight("total fielding defense")
#
# # categories and category weights
#
# s.batting = Weight("batting", Kinds.category)
# s.batting.abbreviate("BAT")
# s.batting.weight(s.total_offense, 2)
#
# s.baserunning = Weight("baserunning", Kinds.category)
# s.baserunning.abbreviate("RUN")
# s.baserunning.weight(s.total_offense, 1)
#
# s.defense = Weight("defense", Kinds.category)
# s.defense.abbreviate("DEF")
# s.defense.weight(s.total_defense_pitching, 0.5)
# s.defense.weight(s.total_defense_fielding, 2)
#
# s.pitching = Weight("pitching", Kinds.category)
# s.pitching.abbreviate("PCH")
# s.pitching.weight(s.total_defense_pitching, 2)
#
# s.edge = Weight("edge", Kinds.category)
# s.edge.abbreviate("EDG")
# s.edge.weight(s.total_offense, 0.5)
# s.edge.weight(s.total_defense_pitching, 0.25)
# s.edge.weight(s.total_defense_fielding, 0.25)
#
# s.vitality = Weight("vitality", Kinds.category)
# s.vitality.abbreviate("VIT")
# s.vitality.weight(s.total_off_field, 1.5)
#
# s.social = Weight("social", Kinds.category)
# s.social.abbreviate("SOC")
# s.social.weight(s.total_off_field, 1.5)

#
# # rating descriptor weights
#
# # overall weights:
# s.overall_power = Weight("overall power")
# s.overall_smallball = Weight("overall smallball")
# s.overall_fielding = Weight("overall fielding")
# s.overall_fastball = Weight("overall fastball")
# s.overall_trickery = Weight("overall trickery")
# s.overall_utility = Weight("overall utility")
# s.overall_utility.extra_weight = -0.5
# s.overall_captaincy = Weight("overall captaincy")
# s.overall_support = Weight("overall support")
#
# # offense weights
# s.slugger = Weight("slugging")
# s.reliable_hitter = Weight("contact hitter")
# s.manufacturer = Weight("runs manufacturer")
# s.utility_hitter = Weight("utility hitter")
# s.utility_hitter.extra_weight = 0.25
#
# # pitching weights
# s.pitcher_speed = Weight("fastball pitcher")
# s.pitcher_speed.extra_weight = 0.25
# s.pitcher_movement = Weight("movement pitcher")
# s.pitcher_speed.extra_weight = 0.25
# s.pitcher_accuracy = Weight("control pitcher")
# s.pitcher_accuracy.extra_weight = 0.25
# s.pitcher_special = Weight("special pitcher")
#
# # fielding weights
# s.infield = Weight("infielder")
# s.outfield = Weight("outfielder")
# s.outfield.extra_weight = -0.75
# s.catcher = Weight("catcher")
# s.pitcher_generic = Weight("pitcher")
#
# # TODO: personality and element handling
#
# # Rating stats
# # offense
#
# s.power = Rating('power', s.determination, s.batting)
# s.power.abbreviate("POW")
# s.power.weight(s.batting, 2)
# s.power.weight(s.overall_power, 2)
# s.power.weight(s.slugger, 2)
#
# s.contact = Rating('contact', s.enthusiasm, s.batting)
# s.contact.abbreviate("CON")
# s.contact.weight(s.batting, 3)
# s.contact.weight(s.overall_power, 0.5)
# s.contact.weight(s.overall_smallball, 2)
# s.contact.weight(s.slugger, 1)
# s.contact.weight(s.utility_hitter, 1)
#
# s.discipline = Rating('discipline', s.stability, s.batting)
# s.discipline.abbreviate("DSC")
# s.discipline.weight(s.batting, 1)
# s.discipline.weight(s.overall_power, 1)
# s.discipline.weight(s.overall_smallball, 1)
# s.discipline.weight(s.overall_utility, 0.25)
# s.discipline.weight(s.reliable_hitter, 1)
# s.discipline.weight(s.manufacturer, 1)
#
# s.speed = Rating('speed', s.enthusiasm, s.baserunning)
# s.speed.abbreviate("SPD")
# s.speed.weight(s.baserunning, 3)
# s.speed.weight(s.overall_smallball, 1)
# s.speed.weight(s.manufacturer, 2)
#
# s.bravery = Rating('bravery', s.determination, s.baserunning)
# s.bravery.abbreviate("BRV")
# s.bravery.weight(s.baserunning, 1)
# s.bravery.weight(s.overall_smallball, 0.5)
# s.bravery.weight(s.manufacturer, 1)
#
# s.timing = Rating('timing', s.insight, s.baserunning)
# s.timing.abbreviate("TMG")
# s.timing.weight(s.baserunning, 2)
# s.timing.weight(s.overall_smallball, 0.75)
# s.timing.weight(s.overall_utility, 0.25)
# s.timing.weight(s.manufacturer, 1)
#
# # defense
#
# s.reach = Rating('reach', s.enthusiasm, s.defense)
# s.reach.abbreviate("RCH")
# s.reach.weight(s.defense, 1)
# s.reach.weight(s.overall_fielding, 1)
# s.reach.weight(s.outfield, 2)
#
# s.grabbiness = Rating('grabbiness', s.stability, s.defense)
# s.grabbiness.abbreviate("GRA")
# s.grabbiness.weight(s.defense, 1.5)
# s.grabbiness.weight(s.overall_fielding, 1)
# s.grabbiness.weight(s.pitcher_special, 1)
# s.grabbiness.weight(s.infield, 1)
# s.grabbiness.weight(s.catcher, 1)
#
# s.throwing = Rating('throwing', s.stability, s.defense)
# s.throwing.abbreviate("THR")
# s.throwing.weight(s.defense, 1)
# s.throwing.weight(s.overall_fielding, 0.75)
# s.throwing.weight(s.outfield, 1)
# s.throwing.weight(s.catcher, 0.5)
# s.throwing.weight(s.pitcher_special, .5)
#
# s.awareness = Rating('awareness', s.insight, s.defense)
# s.awareness.abbreviate("AWR")
# s.awareness.weight(s.defense, 0.5)
# s.awareness.weight(s.overall_fielding, 0.5)
# s.awareness.weight(s.pitching, 0.25)
# s.awareness.weight(s.catcher, 1)
# s.awareness.weight(s.outfield, 0.5)
# s.awareness.weight(s.pitcher_special, .75)
#
# s.calling = Rating('calling', s.insight, s.defense)
# s.calling.abbreviate('CAL')
# s.calling.weight(s.defense, 0.5)
# s.calling.weight(s.pitching, 0.25)
# s.calling.weight(s.overall_fielding, 0.25)
# s.calling.weight(s.catcher, 3)
#
# s.force = Rating('force')
# s.force.personality = s.determination
# s.force.category = s.pitching
# s.force.abbreviate("FOR")
# s.force.weight(s.pitching, 2)
# s.force.weight(s.overall_fastball, 2)
# s.force.weight(s.pitcher_speed, 2)
# s.force.weight(s.pitcher_generic, 2)
#
# s.trickery = Rating('trickery')
# s.trickery.personality = s.insight
# s.trickery.category = s.pitching
# s.trickery.abbreviate("TRK")
# s.trickery.weight(s.pitching, 1.5)
# s.trickery.weight(s.overall_trickery, 2)
# s.trickery.weight(s.overall_utility, 0.25)
# s.trickery.weight(s.pitcher_movement, 2)
# s.trickery.weight(s.pitcher_generic, 1.5)
#
# s.accuracy = Rating('accuracy')
# s.accuracy.personality = s.stability
# s.accuracy.category = s.pitching
# s.accuracy.abbreviate('ACC')
# s.accuracy.weight(s.pitching, 1)
# s.accuracy.weight(s.overall_fastball, 1)
# s.accuracy.weight(s.overall_trickery, 1)
# s.accuracy.weight(s.pitcher_accuracy, 2)
# s.accuracy.weight(s.pitcher_generic, 1)
#
# s.leadership = Rating('leadership')
# s.leadership.personality = s.determination
# s.leadership.category = s.edge
# s.leadership.abbreviate("LED")
# s.leadership.weight(s.edge, 0.5)
# s.leadership.weight(s.overall_captaincy, 1)
#
# s.heckling = Rating('heckling')
# s.heckling.personality = s.enthusiasm
# s.heckling.category = s.edge
# s.heckling.abbreviate('HCK')
# s.heckling.weight(s.edge, 0.5)
# s.heckling.weight(s.overall_captaincy, 0.5)
#
# s.sparkle = Rating('sparkle')
# s.sparkle.personality = s.insight
# s.sparkle.category = s.edge
# s.sparkle.abbreviate('SPK')
# s.sparkle.weight(s.edge, 1.5)
# s.sparkle.weight(s.total_offense, 0.25)
# s.sparkle.weight(s.total_defense_pitching, 0.25)
# s.sparkle.weight(s.overall_trickery, 0.25)
# s.sparkle.weight(s.overall_utility, 1.5)
# s.sparkle.weight(s.utility_hitter, 1)
# s.sparkle.weight(s.pitcher_special, 2)
#
# s.infotech = Rating('i.t.')
# s.infotech.personality = s.stability
# s.infotech.category = s.edge
# s.infotech.abbreviate('I.T')
# s.infotech.weight(s.edge, 1)
# s.infotech.weight(s.overall_utility, 1)
#
# s.endurance = Rating('endurance')
# s.endurance.personality = s.determination
# s.endurance.category = s.vitality
# s.endurance.abbreviate("EDR")
# s.endurance.weight(s.vitality, 1)
#
# s.energy = Rating('energy')
# s.energy.personality = s.enthusiasm
# s.energy.category = s.vitality
# s.energy.abbreviate("ENG")
# s.energy.weight(s.vitality, 1)
#
# s.positivity = Rating('positivity')
# s.positivity.personality = s.stability
# s.positivity.category = s.vitality
# s.positivity.abbreviate("POS")
# s.positivity.weight(s.vitality, 1)
#
# s.recovery = Rating('recovery')
# s.recovery.personality = s.insight
# s.recovery.category = s.vitality
# s.recovery.abbreviate("RCV")
# s.recovery.weight(s.vitality, 1)
#
# s.cool = Rating('cool')
# s.cool.personality = s.determination
# s.cool.category = s.social
# s.cool.abbreviate("COO")
# s.cool.weight(s.social, 1)
# s.cool.weight(s.overall_utility, 0.5)
#
# s.hangouts = Rating('hangouts')
# s.hangouts.personality = s.enthusiasm
# s.hangouts.category = s.social
# s.hangouts.abbreviate("HNG")
# s.hangouts.weight(s.social, 1)
# s.hangouts.weight(s.overall_support, 1)
#
# s.support = Rating('support')
# s.support.personality = s.stability
# s.support.category = s.social
# s.support.abbreviate("SUP")
# s.support.weight(s.social, 1)
# s.support.weight(s.overall_support, 2)
#
# s.teaching = Rating('teaching')
# s.teaching.personality = s.insight
# s.teaching.category = s.social
# s.teaching.abbreviate("TCH")
# s.teaching.weight(s.social, 1)
# s.teaching.weight(s.overall_captaincy, 1)
#
# for stat in s['rating']:
#     stat.default = 0
#
#
# # Descriptors
#
# s.overall_descriptor = Calculatable('overall descriptor', Kinds.descriptor)
# s.overall_descriptor.default = "The Observed"
#
# s.offense_descriptor = Calculatable('offense descriptor', Kinds.descriptor)
# s.offense_descriptor.default = "Unevaluated Hitter"
#
# s.defense_descriptor = Calculatable('defense descriptor', Kinds.descriptor)
# s.defense_descriptor.default = "Unable To Catch A Cold"
#
# s.personality_descriptor = Calculatable('personality descriptor', Kinds.descriptor)
# s.personality_descriptor.default = "Smol Bean"
#
# s.offense_position = Calculatable('offense position', Kinds.descriptor)
# s.offense_position.default = 'Bench'
#
# s.defense_position = Calculatable('defense position', Kinds.descriptor)
# s.defense_position.default = 'Bullpen'
#
#
#
# s.vibes = Stat('vibes', Kinds.condition)
# s.vibes.abbreviate("VIB")
# s.vibes.default = 1.0
#
# s.stamina = Stat('stamina', Kinds.condition)
# s.stamina.abbreviate('STA')
# s.stamina.default = 1.0
#
# s.mood = Stat('mood', Kinds.condition)
# s.mood.abbreviate("MOD")
# s.mood.default = 1.0
#
# s.soul = Stat('soul', Kinds.condition)
# s.soul.abbreviate("SOL")
# s.soul.default = 1.0
#
#
# s.team = Stat('team', Kinds.character)
# s.team.abbreviate("TEAM")
# s.team.default = "DETROIT DEFAULT"
#
# s.fingers = Stat('fingers', Kinds.character)
# s.fingers.default = 9
#
# s.is_pitcher = Stat('is pitcher', Kinds.character)
# s.is_pitcher.default = False
#
# s.clutch = Stat('clutch', Kinds.character)
# s.clutch.default = 0.2
# s.clutch.abbreviate("CLT")
#
# s.pull = Stat('pull', Kinds.character)
# s.pull.default = -1
#
# s.element = Stat('element', Kinds.character)
# s.element.default = "Basic"
# s.element.abbreviate("ELE")

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
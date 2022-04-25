"""
defines stats for use in other classes
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from blaseball.stats.players import Player

from collections.abc import Collection
from typing import Union, List


STAT_KINDS = [
    'personality',  # one of the personality four
    'category',  # one of the categories
    'rating',  # one of the 0-2 numeric ratings
    'descriptor',  # an english derived stat
    'condition',  # stats that govern a player's condition
    'character',  # a miscellaneous player attribute
    'performance',  # a tracked performance metric
    'averaging',  # a performance stat that is a running average; requires a total performance stat.
    'test'  # stats in the test group are only for use in testing and shouldn't be called anywhere else
]


class AllStats(Collection):
    def __init__(self):
        self.all_stats = []
        self.weights = {}

    def append(self, item):
        self.all_stats.append(item)

    def all_personality(self, personality):
        personality = str(personality).lower()
        return [x for x in self.all_stats if x.personality == personality]

    def all_category(self, category):
        category = str(category).lower()
        return [x for x in self.all_stats if x.category == category]

    def weight(self, weight: str, stat: 'Stat', value):
        if weight not in self.weights:
            self.weights[weight] = Weight(weight)
        self.weights[weight].add(stat, value)

    def __getitem__(self, item) -> Union['Stat', List]:
        found_stats = [found_stat for found_stat in self.all_stats if found_stat.name == item]
        if len(found_stats) > 1:
            return found_stats
        elif len(found_stats) == 1:
            return found_stats[0]
        else:
            return [x for x in self.all_stats if x.kind == item]

    def __contains__(self, item):
        if isinstance(item, Stat):
            return item.name in self
        return item in [this_stat.name for this_stat in self.all_stats]

    def __iter__(self):
        return iter(self.all_stats)

    def __len__(self):
        return len(self.all_stats)


all_stats = AllStats()


class Weight:
    def __init__(self, name: str):
        self.name = name
        self.stats = {}
        self.extra_weight = 0

    def add(self, stat: Union['Stat', str], value: Union[float, int]):
        if isinstance(stat, str):
            if 'extra' in stat:
                self.extra_weight += value
            else:
                raise KeyError("You must add stats to a weight by class, not name.")
        else:
            self.stats[stat.name] = value

    def calculate_weighted(self, player: 'Player'):
        weight = sum(self.stats.values()) + self.extra_weight
        total = sum(player[s] * self.stats[s] for s in self.stats)
        return total / weight

    def nice_string(self) -> str:
        nice = self.name + ":"
        for v, s in sorted(zip(self.stats.values(), self.stats.keys()), reverse=True):
            nice += f" {s} {v}"
        if self.extra_weight != 0:
            nice += f" extra {self.extra_weight}"
        return nice

    def __str__(self):
        return f"Weight {self.name.capitalize()}"


class Stat:
    def __init__(self, name: str, kind:str):
        self.name = name
        if name in all_stats:
            raise KeyError(f"Stat {name} already defined!")

        self.kind = kind
        if kind not in STAT_KINDS:
            raise RuntimeError("Invalid stat type!")

        self.personality = None
        self.category = None
        self.abbreviation = None
        self.default = None
        self.total_stat = None

        all_stats.append(self)

    def personalize(self, personality: 'Stat'):
        self.personality = personality.name

    def categorize(self, category: 'Stat'):
        self.category = category.name

    def abbreviate(self, abbreviation: str):
        for stat in all_stats:
            if stat.abbreviation == abbreviation:
                raise KeyError(f"Duplicate Abbreviation {abbreviation}! "
                               f"Collision between {stat.name} and {self.name}")
        self.abbreviation = abbreviation

    def weight(self, weight: str, value: Union[float, int]):
        all_stats.weight(weight, self, value)

    def __str__(self):
        return self.name.capitalize()

    def __repr__(self):
        return f"Stat({self.name}, {self.kind})"


determination = Stat('determination', 'personality')
determination.abbreviate("DTR")
determination.weight('descriptor_determination', 1)

enthusiasm = Stat('enthusiasm', 'personality')
enthusiasm.abbreviate("ENT")
enthusiasm.weight('descriptor_enthusiasm', 1)

stability = Stat('stability', 'personality')
stability.abbreviate("STB")
stability.weight('descriptor_stability', 1)

insight = Stat('insight', 'personality')
insight.abbreviate("INS")
insight.weight('descriptor_insight', 1)

for stat in all_stats['personality']:
    stat.default = 0


batting = Stat('batting', 'category')
batting.abbreviate("BAT")
batting.weight('total_offense', 2)

baserunning = Stat('baserunning', 'category')
baserunning.abbreviate("RUN")
baserunning.weight('total_offense', 1)

defense = Stat('defense', 'category')
defense.abbreviate("DEF")
defense.weight('total_defense_pitching', 0.5)
defense.weight('total_defense_fielding', 2)

pitching = Stat('pitching', 'category')
pitching.abbreviate("PCH")
pitching.weight('total_defense_pitching', 2)

edge = Stat('edge', 'category')
edge.abbreviate("EDG")
edge.weight('total_offense', 0.5)
edge.weight('total_defense_pitching', 0.25)
edge.weight('total_defense_fielding', 0.25)

vitality = Stat('vitality', 'category')
vitality.abbreviate('VIT')
vitality.weight('total_off_field', 1.5)

social = Stat('social', 'category')
social.abbreviate("SOC")
social.weight('total_off_field', 1.5)

for stat in all_stats['category']:
    stat.default = -1


power = Stat('power', 'rating')
power.personalize(determination)
power.categorize(batting)
power.abbreviate("POW")
power.weight('batting', 2)
power.weight('descriptor_o_power', 2)
power.weight('descriptor_slugging', 2)

contact = Stat('contact', 'rating')
contact.personalize(enthusiasm)
contact.categorize(batting)
contact.abbreviate("CON")
contact.weight('batting', 3)
contact.weight('descriptor_o_power', 0.5)
contact.weight('descriptor_o_smallball', 2)
contact.weight('descriptor_slugging', 1)
contact.weight('descriptor_contact', 2)
contact.weight('descriptor_utility_hitter', 1)
all_stats.weights['descriptor_utility_hitter'].add('extra_weight', 0.25)

discipline = Stat('discipline', 'rating')
discipline.personalize(stability)
discipline.categorize(batting)
discipline.abbreviate("DSC")
discipline.weight('batting', 1)
discipline.weight('descriptor_o_power', 1)
discipline.weight('descriptor_o_smallball', 1)
discipline.weight('descriptor_o_utility', 0.25)
discipline.weight('descriptor_contact', 1)
discipline.weight('descriptor_manufacture', 1)

speed = Stat('speed', 'rating')
speed.personality = 'enthusiasm'
speed.categorize(baserunning)
speed.abbreviate("SPD")
speed.weight('baserunning', 3)
speed.weight('descriptor_o_smallball', 1)
speed.weight('descriptor_manufacture', 2)

bravery = Stat('bravery', 'rating')
bravery.personalize(determination)
bravery.categorize(baserunning)
bravery.abbreviate("BRV")
bravery.weight('baserunning', 1)
bravery.weight('descriptor_o_smallball', 0.5)
bravery.weight('descriptor_manufacture', 1)

timing = Stat('timing', 'rating')
timing.personalize(insight)
timing.categorize(baserunning)
timing.abbreviate("TMG")
timing.weight('baserunning', 2)
timing.weight('descriptor_o_smallball', 0.75)
timing.weight('descriptor_o_utility', 0.25)
timing.weight('descriptor_manufacture', 1)

reach = Stat('reach', 'rating')
reach.personality = 'enthusiasm'
reach.categorize(defense)
reach.abbreviate("RCH")
reach.weight('defense', 1)
reach.weight('descriptor_o_fielding', 1)
reach.weight('descriptor_outfield', 2)
all_stats.weights['descriptor_outfield'].add('extra', -0.75)

grabbiness = Stat('grabbiness', 'rating')
grabbiness.personalize(stability)
grabbiness.categorize(defense)
grabbiness.abbreviate("GRA")
grabbiness.weight('defense', 1.5)
grabbiness.weight('descriptor_o_fielding', 1)
grabbiness.weight('descriptor_special', 1)
grabbiness.weight('descriptor_infield', 1)
grabbiness.weight('descriptor_catcher', 1)

throwing = Stat('throwing', 'rating')
throwing.personalize(stability)
throwing.abbreviate("THR")
throwing.weight('defense', 1)
throwing.weight('descriptor_o_fielding', 0.75)
throwing.weight('descriptor_outfield', 1)
throwing.weight('descriptor_catcher', 0.5)
throwing.weight('descriptor_special', .5)

awareness = Stat('awareness', 'rating')
awareness.personalize(insight)
awareness.abbreviate("AWR")
awareness.weight('defense', 0.5)
awareness.weight('descriptor_o_fielding', 0.5)
awareness.weight('pitching', 0.25)
awareness.weight('descriptor_catcher', 1)
throwing.weight('descriptor_outfield', 0.5)
awareness.weight('descriptor_special', .75)

calling = Stat('calling', 'rating')
calling.personalize(insight)
calling.categorize(defense)
calling.abbreviate('CAL')
calling.weight('defense', 0.5)
calling.weight('pitching', 0.25)
calling.weight('descriptor_o_fielding', 0.25)
calling.weight('descriptor_catcher', 3)

force = Stat('force', 'rating')
force.personalize(determination)
force.categorize(pitching)
force.abbreviate("FOR")
force.weight('pitching', 2)
force.weight('descriptor_o_fastball', 2)
force.weight('descriptor_force', 2)
all_stats.weights['descriptor_force'].add('extra_weight', 0.25)
force.weight('descriptor_pitcher_generic', 2)

trickery = Stat('trickery', 'rating')
trickery.personalize(insight)
trickery.categorize(pitching)
trickery.abbreviate("TRK")
trickery.weight('pitching', 1.5)
trickery.weight('descriptor_o_tricky', 2)
trickery.weight('descriptor_o_utility', 0.25)
trickery.weight('descriptor_trickery', 2)
all_stats.weights['descriptor_trickery'].add('extra_weight', 0.25)
trickery.weight('descriptor_pitcher_generic', 1.5)

accuracy = Stat('accuracy', 'rating')
accuracy.personalize(stability)
accuracy.categorize(pitching)
accuracy.abbreviate('ACC')
accuracy.weight('pitching', 1)
accuracy.weight('descriptor_o_fastball', 1)
accuracy.weight('descriptor_o_tricky', 1)
accuracy.weight('descriptor_accuracy', 2)
all_stats.weights['descriptor_accuracy'].add('extra_weight', 0.25)
accuracy.weight('descriptor_pitcher_generic', 1)

leadership = Stat('leadership', 'rating')
leadership.personalize(determination)
leadership.categorize(edge)
leadership.abbreviate("LED")
leadership.weight('edge', 0.5)
leadership.weight('descriptor_o_coach', 1)

heckling = Stat('heckling', 'rating')
heckling.personalize(enthusiasm)
heckling.categorize(edge)
heckling.abbreviate('HCK')
heckling.weight('edge', 0.5)
heckling.weight('descriptor_o_coach', 0.5)

sparkle = Stat('sparkle', 'rating')
sparkle.personalize(insight)
sparkle.categorize(edge)
sparkle.abbreviate('SPK')
sparkle.weight('edge', 1.5)
sparkle.weight('total_offense', 0.25)
sparkle.weight('total_defense_pitching', 0.25)
sparkle.weight('descriptor_o_tricky', 0.25)
sparkle.weight('descriptor_o_utility', 1.5)
all_stats.weights['descriptor_o_utility'].add('extra_weight', -0.5)
sparkle.weight('descriptor_utility_hitter', 1)
sparkle.weight('descriptor_special', 2)


infotech = Stat('i.t.', 'rating')
infotech.personalize(stability)
infotech.categorize(edge)
infotech.abbreviate('I.T')
infotech.weight('edge', 1)
infotech.weight('descriptor_o_utility', 1)

endurance = Stat('endurance', 'rating')
endurance.personalize(determination)
endurance.categorize(vitality)
endurance.abbreviate("EDR")
endurance.weight('vitality', 1)

energy = Stat('energy', 'rating')
energy.personalize(enthusiasm)
energy.categorize(vitality)
energy.abbreviate("ENG")
energy.weight('vitality', 1)

positivity = Stat('positivity', 'rating')
positivity.personalize(stability)
positivity.categorize(vitality)
positivity.abbreviate("POS")
positivity.weight('vitality', 1)

recovery = Stat('recovery', 'rating')
recovery.personalize(insight)
recovery.categorize(vitality)
recovery.abbreviate("RCV")
recovery.weight('vitality', 1)

cool = Stat('cool', 'rating')
cool.personalize(determination)
cool.categorize(social)
cool.abbreviate("COO")
cool.weight('social', 1)
cool.weight('descriptor_o_utility', 0.5)

hangouts = Stat('hangouts', 'rating')
hangouts.personalize(enthusiasm)
hangouts.categorize(social)
hangouts.abbreviate("HNG")
hangouts.weight('social', 1)
hangouts.weight('descriptor_o_support', 1)

support = Stat('support', 'rating')
support.personalize(stability)
support.categorize(social)
support.abbreviate("SUP")
support.weight('social', 1)
support.weight('descriptor_o_support', 2)

teaching = Stat('teaching', 'rating')
teaching.personalize(insight)
teaching.categorize(social)
teaching.abbreviate("TCH")
teaching.weight('social', 1)
teaching.weight('descriptor_o_coach', 1)


for stat in all_stats['rating']:
    stat.default = 0


total_offense = Stat('total offense', 'category')
total_offense.abbreviate("TOF")
total_offense.default = -1

total_defense = Stat('total defense', 'category')
total_defense.abbreviate("TDE")
total_defense.default = -1

total_off_field = Stat('total off-field', 'category')
total_off_field.abbreviate("TFD")
total_off_field.default = -1


overall_descriptor = Stat('overall descriptor', 'descriptor')
overall_descriptor.default = "The Observed"

offense_descriptor = Stat('offense descriptor', 'descriptor')
offense_descriptor.default = "Unevaluated Hitter"

defense_descriptor = Stat('defense descriptor', 'descriptor')
defense_descriptor.default = "Unable To Catch A Cold"

personality_descriptor = Stat('personality descriptor', 'descriptor')
personality_descriptor.default = "Smol Bean"

offense_position = Stat('offense position', 'descriptor')
offense_position.default = 'Bench'

defense_position = Stat('defense position', 'descriptor')
defense_position.default = 'Bullpen'


vibes = Stat('vibes', 'condition')
vibes.abbreviate("VIB")
vibes.default = 1.0

stamina = Stat('stamina', 'condition')
stamina.abbreviate('STA')
stamina.default = 1.0

mood = Stat('mood', 'condition')
mood.abbreviate("MOD")
mood.default = 1.0

soul = Stat('soul', 'condition')
soul.abbreviate("SOL")
soul.default = 1.0


name = Stat('name', 'character')
name.abbreviate("NAME")
name.default = "WYATT MASON"

team = Stat('team', 'character')
team.abbreviate("TEAM")
team.default = "DETROIT DEFAULT"

number = Stat('number', 'character')
number.abbreviate("#")
number.default = "-1"

fingers = Stat('fingers', 'character')
fingers.default = 9

is_pitcher = Stat('is pitcher', 'character')
is_pitcher.default = False

clutch = Stat('clutch', 'character')
clutch.default = 0.2
clutch.abbreviate("CLT")

pull = Stat('pull', 'character')
pull.default = -1

element = Stat('element', 'character')
element.default = "Basic"
element.abbreviate("ELE")

at_bats = Stat('at bats', 'performance')

pitches_called = Stat('total pitches called', 'performance')

average_called_location = Stat('average called location', 'averaging')
average_called_location.total_stat = 'total pitches called'

pitches_thrown = Stat('total pitches thrown', 'performance')

pitch_stats = [
    'average pitch difficulty',
    'average pitch obscurity',
    'average pitch distance from edge',
    'average pitch distance from call',
    'thrown strike rate',
    'average reduction'
]

for stat in pitch_stats:
    new_stat = Stat(stat, 'averaging')
    new_stat.total_stat = 'total pitches thrown'

pitches_seen = Stat('pitches seen', 'performance')

hit_stats = ['strike rate', 'ball rate', 'foul rate', 'hit rate', 'pitch read chance']
for stat in hit_stats:
    new_stat = Stat(stat, 'averaging')
    new_stat.total_stat = 'pitches seen'

total_hits = Stat('total hits', 'performance')

average_hit_distance = Stat('average hit distance', 'averaging')
average_hit_distance.total_stat = 'total hits'

exit_velo = Stat('average exit velocity', 'averaging')
exit_velo.total_stat = 'total hits'

total_home_runs = Stat('total home runs', 'performance')

for stat in all_stats['performance'] + all_stats['averaging']:
    stat.default = 0


if __name__ == "__main__":
    for p in all_stats['personality']:
        print(p.name.upper())
        for s in all_stats.all_personality(p):
            print(f"\t{s}")
    print("\n")
    for c in all_stats['category']:
        print(c.name.upper())
        for s in all_stats.all_category(c):
            print(f"\t{s}")

    for s in all_stats:
        print(s)
        print(type(s))
        break

    print("\r\n\r\n")
    for weight in all_stats.weights:
        if "descriptor" not in weight:
            print(all_stats.weights[weight].nice_string())
    print('\r\n')
    for weight in all_stats.weights:
        if "descriptor" in weight and "descriptor_o" not in weight:
            print(all_stats.weights[weight].nice_string())
    print('\r\n')
    for weight in all_stats.weights:
        if "descriptor_o" in weight:
            print(all_stats.weights[weight].nice_string())

    print("\r\n\r\nPersonality Report:")
    print("TBR")

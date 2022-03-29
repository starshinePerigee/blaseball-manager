"""
defines stats for use in other classes
"""

from collections.abc import Collection


STAT_KINDS = [
    'personality',  # one of the personality four
    'category',  # one of the categories
    'rating',  # one of the 0-2 numeric ratings
    'descriptor',  # an english derived stat
    'condition',  # stats that govern a player's condition
    'character',  # a miscellaneous player attribute
    'performance',  # a tracked performance metric
]


class AllStats(Collection):
    def __init__(self):
        self.all_stats = []

    def append(self, item):
        self.all_stats.append(item)

    def all_personality(self, personality):
        personality = str(personality).lower()
        return [x for x in self.all_stats if x.personality == personality]

    def all_category(self, category):
        category = str(category).lower()
        return [x for x in self.all_stats if x.category == category]

    def __getitem__(self, item):
        try:
            return self.all_stats[item]
        except (TypeError, KeyError):
            return [x for x in self.all_stats if x.kind == item]

    def __contains__(self, item):
        return item in self.all_stats

    def __iter__(self):
        return iter(self.all_stats)

    def __len__(self):
        return len(self.all_stats)


all_stats = AllStats()


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

        all_stats.append(self)

    def personalize(self, personality):
        self.personality = personality.name

    def categorize(self, category):
        self.category = category.name

    def abbreviate(self, abbreviation):
        for stat in all_stats:
            if stat.abbreviation == abbreviation:
                raise KeyError(f"Duplicate Abbreviation {abbreviation}! "
                               f"Collision between {stat.name} and {self.name}")
        self.abbreviation = abbreviation

    def __str__(self):
        return self.name.capitalize()


determination = Stat('determination', 'personality')
determination.abbreviate("DTR")

enthusiasm = Stat('enthusiasm', 'personality')
enthusiasm.abbreviate("ENT")

stability = Stat('stability', 'personality')
stability.abbreviate("STB")

insight = Stat('insight', 'personality')
insight.abbreviate("INS")

for stat in all_stats['personality']:
    stat.default = 0


batting = Stat('batting', 'category')
batting.abbreviate("BAT")

baserunning = Stat('baserunning', 'category')
baserunning.abbreviate("RUN")

defense = Stat('defense', 'category')
defense.abbreviate("DEF")

pitching = Stat('pitching', 'category')
pitching.abbreviate("PCH")

edge = Stat('edge', 'category')
edge.abbreviate("EDG")

vitality = Stat('vitality', 'category')
vitality.abbreviate('VIT')

social = Stat('social', 'category')
social.abbreviate("SOC")

for stat in all_stats['category']:
    stat.default = -1


power = Stat('power', 'rating')
power.personalize(determination)
power.categorize(batting)
power.abbreviate("POW")

contact = Stat('contact', 'rating')
contact.personalize(enthusiasm)
contact.categorize(batting)
contact.personalize(enthusiasm)
contact.category = 'batting'
contact.abbreviate("CON")

discipline = Stat('discipline', 'rating')
discipline.personalize(stability)
discipline.categorize(batting)
discipline.abbreviate("DSC")

speed = Stat('speed', 'rating')
speed.personality = 'enthusasm'
speed.categorize(baserunning)
speed.abbreviate("SPD")

bravery = Stat('bravery', 'rating')
bravery.personalize(determination)
bravery.categorize(baserunning)
bravery.abbreviate("BRV")

timing = Stat('timing', 'rating')
timing.personalize(insight)
timing.categorize(baserunning)
timing.abbreviate("TMG")

reach = Stat('reach', 'rating')
reach.personality = 'enthusasm'
reach.categorize(defense)
reach.abbreviate("RCH")

grabbiness = Stat('grabbiness', 'rating')
grabbiness.personalize(stability)
grabbiness.categorize(defense)
grabbiness.abbreviate("GRA")

calling = Stat('calling', 'rating')
calling.personalize(insight)
calling.categorize(defense)
calling.abbreviate('CAL')

force = Stat('force', 'rating')
force.personalize(determination)
force.categorize(pitching)
force.abbreviate("FOR")

trickery = Stat('trickery', 'rating')
trickery.personalize(insight)
trickery.categorize(pitching)
trickery.abbreviate("TRK")

accuracy = Stat('accuracy', 'rating')
accuracy.personalize(stability)
accuracy.categorize(pitching)
accuracy.abbreviate('ACC')

leadership = Stat('leadership', 'rating')
leadership.personalize(determination)
leadership.categorize(edge)
leadership.abbreviate("LED")

heckling = Stat('heckling', 'rating')
heckling.personalize(enthusiasm)
heckling.categorize(edge)
heckling.abbreviate('HCK')

sparkle = Stat('sparkle', 'rating')
sparkle.personalize(insight)
sparkle.categorize(edge)
sparkle.abbreviate('SPK')

infotech = Stat('i.t.', 'rating')
infotech.personalize(stability)
infotech.categorize(edge)
infotech.abbreviate('I.T')

endurance = Stat('endurance', 'rating')
endurance.personalize(determination)
endurance.categorize(vitality)
endurance.abbreviate("EDR")

energy = Stat('energy', 'rating')
energy.personalize(enthusiasm)
energy.categorize(vitality)
energy.abbreviate("ENG")

positivity = Stat('positivity', 'rating')
positivity.personalize(stability)
positivity.categorize(vitality)
positivity.abbreviate("POS")

recovery = Stat('recovery', 'rating')
recovery.personalize(insight)
recovery.categorize(vitality)
recovery.abbreviate("RCV")

cool = Stat('cool', 'rating')
cool.personalize(determination)
cool.categorize(social)
cool.abbreviate("COO")

hangouts = Stat('hangouts', 'rating')
hangouts.personalize(enthusiasm)
hangouts.categorize(social)
hangouts.abbreviate("HNG")

support = Stat('support', 'rating')
support.personalize(stability)
support.categorize(social)
support.abbreviate("SUP")

teaching = Stat('teaching', 'rating')
teaching.personalize(insight)
teaching.categorize(social)
teaching.abbreviate("TCH")


for stat in all_stats['rating']:
    stat.default = 0


total_offense = Stat('total offense', 'category')
total_offense.abbreviate("TOF")
total_offense.default = -1

total_defense = Stat('total defense', 'category')
total_defense.abbreviate("TDE")
total_defense.default = -1

total_off_field = Stat('total off field', 'category')
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

offense_position = Stat('offensive position', 'descriptor')
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
name.default = "Wyatt Mason"

fingers = Stat('fingers', 'character')
fingers.default = 9

is_pitcher = Stat('is pitcher', 'character')
is_pitcher.default = False

clutch = Stat('clutch', 'character')
clutch.default = 0.2
clutch.abbreviate("CLT")

element = Stat('element', 'character')
element.default = "Basic"
element.abbreviate("ELE")


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

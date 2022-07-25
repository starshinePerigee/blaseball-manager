"""
defines stats for use in other classes
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from blaseball.stats.players import Player

from collections.abc import Collection
from collections import defaultdict
from typing import Union, List
from enum import Enum, auto


class StatKinds(Enum):
    # the number in this enum
    personality = auto()  # core personality types
    category = auto()  # stat categories, like "batting"
    rating = auto()  # 0-2 numeric ratings that govern a player's ball ability
    base_rating = auto()  # a base value for a player's rating, before modifiers or effects
    weight = auto()  # a weight is a stat representing a summary of several other stats.
    descriptor = auto()  # english derived stat descriptors based on a weight
    total_weight = auto()  # a summary weight that depends on other weights
    condition = auto()  # a player's condition stats, such as mood and soul
    character = auto()  # a player's character stats, such as name and fingers
    performance = auto()  # a tracked performance metric, such as number of hits
    averaging = auto()  # tracked metric that is a running average, such as batting average
    test = auto()  # stats in the test group are only for use in testing and shouldn't be used anywehre else.
    test_dependent = auto()  # a test that depends on test


# A "dependency" is a list of all kinds that a kind depends on.
# ie: a rating stat depends on its base_rating.
# note that this is for live updates. So even though a base_rating is generated based on the personality,
# that stat doesn't update if personality later updates, and thus base_rating doesn't depend on personality.
#
# When a stat is updated, all stats that depend on that stat get their stale flags flipped.
# when defining a get method, only pull from stats in their dependency.
# to handle order, we manually define a recalculation order for each kind. (this could be automatically managed
# but that sounds like a ton of work! stats without dependencies do not need to be recalculated.

BASE_DEPENDENCIES = {
    # make sure you include all dependencies, include dependencies of dependencies.
    # Listed in recalculation order!
    StatKinds.rating: [StatKinds.base_rating],
    StatKinds.category: [StatKinds.rating, StatKinds.base_rating],
    StatKinds.weight: [StatKinds.rating, StatKinds.base_rating, StatKinds.category],
    StatKinds.total_weight: [StatKinds.rating, StatKinds.base_rating, StatKinds.category,
                             StatKinds.weight],
    StatKinds.descriptor: [StatKinds.rating, StatKinds.base_rating, StatKinds.character, StatKinds.category,
                           StatKinds.weight, StatKinds.total_weight],
    StatKinds.averaging: [StatKinds.performance],
    StatKinds.test_dependent: [StatKinds.test]
}

recalculation_order = BASE_DEPENDENCIES.keys()

dependencies = BASE_DEPENDENCIES
# fill in everything that's not a dependent
for kind in StatKinds:
    if kind not in dependencies:
        dependencies[kind] = []

# invert the array so we know what to look up / set the stale flag for when we write
dependents = {kind: [] for kind in StatKinds}
for kind in StatKinds:
    for dependency in dependencies[kind]:
        dependents[dependency] += [kind]


# initialize the stale flag dictionary
stale_flags = {kind: defaultdict(lambda: True) for kind in BASE_DEPENDENCIES}


class AllStats(Collection):
    """A singleston class meant to contain all stats and provide convenient indexing methods."""
    def __init__(self):
        self._stats_dict = {}

    def _get_all_with_kind(self, kind: StatKinds):
        return [x for x in self._stats_dict.values() if x.kind == kind]

    def _get_all_with_personality(self, personality: "Stat"):
        return [x for x in self._stats_dict.values() if x.personality == personality]

    def _get_all_with_category(self, category: "Stat"):
        return [x for x in self._stats_dict.values() if x.category == category]

    def _get_all_by_name_partial(self, identifier: str):
        return [self._stats_dict[x] for x in self._stats_dict if identifier in x]

    def __getitem__(self, item: Union['Stat', StatKinds, str]) -> Union['Stat', List]:
        """Get stats that match a criteria.
        Do not use this in core loops, index by dot directly."""
        if isinstance(item, Stat):
            if item.kind is StatKinds.personality:
                return self._get_all_with_personality(item)
            elif item.kind is StatKinds.category:
                return self._get_all_with_category(item)
        elif isinstance(item, StatKinds):
            return self._get_all_with_kind(item)
        else:
            if item in self._stats_dict:
                return self._stats_dict[item]
            else:
                return self._get_all_by_name_partial(item)

    def __setitem__(self, key: str, value: 'Stat'):
        self._stats_dict[key] = value

    def __contains__(self, item):
        if isinstance(item, Stat):
            return item.name in self._stats_dict
        return item in self._stats_dict

    def __iter__(self):
        return iter(self._stats_dict.values())

    def __len__(self):
        return len(self._stats_dict)


all_stats = AllStats()


class Stat:
    def __init__(self, name: str, kind: StatKinds):
        self.name = name
        if name in all_stats:
            raise KeyError(f"Stat {name} already defined!")
        all_stats[name] = self

        self.kind = kind

        # these are optional stat attributes
        self.personality = None  # the personality stat that governs this stat (applies to ratings)
        self.category = None  # the stat category this applies to
        self.abbreviation = None  # the abbreviation for this stat
        self.default = None  # the default value for this stat when a new player is generated

    def get(self, player: 'Player') -> Union[float, str]:
        return player.pb.df.at[player.cid, self.name]

    def set(self, player: 'Player', value: object) -> None:
        # set value
        player.pb.df.at[player.cid, self.name] = value
        # update stale flags
        for dependent in dependents[self.kind]:
            stale_flags[dependent][player.cid] = True

    def abbreviate(self, abbreviation: str):
        for stat in all_stats:
            if stat.abbreviation == abbreviation:
                raise KeyError(f"Duplicate Abbreviation {abbreviation}! "
                               f"Collision between {stat.name} and {self.name}")
        self.abbreviation = abbreviation

    def weight(self, weight: "Weight", value: Union[float, int]):
        weight.add(self, value)

    def __str__(self):
        return self.name.capitalize()

    def __repr__(self):
        return f"Stat({self.name}, {self.kind.name})"


class Calculatable(Stat):
    """a calculatable is a stat which can be calculated based on other stats."""

    def __init__(self, name: str, kind: StatKinds):
        super().__init__(name, kind)
        self.formula = None
        self.default = -1

    def get(self, player: 'Player') -> Union[float, str]:
        if stale_flags[self.kind][player.cid]:
            return player.pb.df.at[player.cid, self.name]
        else:
            return self.formula(player)

    def set(self, player: 'Player', value: object) -> None:
        raise AttributeError(f"Tried to set calculated stat {self}!")


def recalculate_kind(kind: StatKinds, player: 'Player'):
    """Recalculate all values in the specified Kind and update the stale flag"""
    for stat in all_stats[kind]:
        player.pb.df.at[player.cid, stat.name] = stat.get(player)
    stale_flags[kind][player.cid] = False


class Weight(Calculatable):
    """a Weight is a special stat which is derived from a number of other stats using methods described in
    util.descriptors. (this might move). """
    def __init__(self, name: str, kind: StatKinds = StatKinds.weight):
        super().__init__(name, kind)

        self.formula = self.calculate_weighted

        self.stats = {}
        self.extra_weight = 0

    def add(self, stat: Stat, value: Union[float, int]):
        """Add a stat to the total weight.
        To add extra weight, access the attribute directly."""
        self.stats[stat.name] = value

    def calculate_weighted(self, player: 'Player'):
        weight = sum(self.stats.values()) + self.extra_weight
        total = sum([player.pb.df.at[player.cid, stat.name] * self.stats[stat] for stat in self.stats])
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


class Rating(Calculatable):
    def __init__(self, name: str):
        super().__init__(name, StatKinds.rating)

        self.base_stat = Stat(('base_' + name), StatKinds.base_rating)
        setattr(all_stats, self.base_stat.name, self.base_stat)

        self.formula = self.calculate_rating

    def calculate_rating(self, player: 'Player'):
        # TODO
        return player.pb.df.at[player.cid, self.base_stat.name]


# personality descriptor weights:
all_stats.weight_determination = Weight("determination weight")
all_stats.weight_enthusiasm = Weight("enthusiasm weight")
all_stats.weight_stability = Weight("stability weight")
all_stats.weight_insight = Weight("insight weight")

# personality four
all_stats.determination = Stat("determination", StatKinds.personality)
all_stats.determination.abbreviate("DTR")
all_stats.determination.weight(all_stats.weight_determination, 1)

all_stats.enthusiasm = Stat("enthusiasm", StatKinds.personality)
all_stats.enthusiasm.abbreviate("ENT")
all_stats.enthusiasm.weight(all_stats.weight_enthusiasm, 1)

all_stats.stability = Stat("stability", StatKinds.personality)
all_stats.stability.abbreviate("STB")
all_stats.stability.weight(all_stats.weight_stability, 1)

all_stats.insight = Stat("insight", StatKinds.personality)
all_stats.insight.abbreviate("INS")
all_stats.insight.weight(all_stats.weight_insight, 1)

for stat in all_stats[StatKinds.personality]:
    stat.default = 0


# top level ultimate summary weights
all_stats.total_offense = Weight('total offense', StatKinds.total_weight)
all_stats.total_offense.abbreviate("TOF")
all_stats.total_offense.default = -1

all_stats.total_defense = Weight('total defense', StatKinds.total_weight)
all_stats.total_defense.abbreviate("TDE")
all_stats.total_defense.default = -1

all_stats.total_off_field = Weight('total off-field', StatKinds.total_weight)
all_stats.total_off_field.abbreviate("TFD")
all_stats.total_off_field.default = -1

all_stats.total_defense_pitching = Weight("total pitching defense")
all_stats.total_defense_fielding = Weight("total fielding defense")

# categories and category weights

all_stats.batting = Weight("batting", StatKinds.category)
all_stats.batting.abbreviate("BAT")
all_stats.batting.weight(all_stats.total_offense, 2)

all_stats.baserunning = Weight("baserunning", StatKinds.category)
all_stats.baserunning.abbreviate("RUN")
all_stats.baserunning.weight(all_stats.total_offense, 1)

all_stats.defense = Weight("defense", StatKinds.category)
all_stats.defense.abbreviate("DEF")
all_stats.defense.weight(all_stats.total_defense_pitching, 0.5)
all_stats.defense.weight(all_stats.total_defense_fielding, 2)

all_stats.pitching = Weight("pitching", StatKinds.category)
all_stats.pitching.abbreviate("PCH")
all_stats.pitching.weight(all_stats.total_defense_pitching, 2)

all_stats.edge = Weight("edge", StatKinds.category)
all_stats.edge.abbreviate("EDG")
all_stats.edge.weight(all_stats.total_offense, 0.5)
all_stats.edge.weight(all_stats.total_defense_pitching, 0.25)
all_stats.edge.weight(all_stats.total_defense_fielding, 0.25)

all_stats.vitality = Weight("vitality", StatKinds.category)
all_stats.vitality.abbreviate("VIT")
all_stats.vitality.weight(all_stats.total_off_field, 1.5)

all_stats.social = Weight("social", StatKinds.category)
all_stats.social.abbreviate("SOC")
all_stats.social.weight(all_stats.total_off_field, 1.5)


# rating descriptor weights

# overall weights:
all_stats.overall_power = Weight("overall power")
all_stats.overall_smallball = Weight("overall smallball")
all_stats.overall_fielding = Weight("overall fielding")
all_stats.overall_fastball = Weight("overall fastball")
all_stats.overall_trickery = Weight("overall trickery")
all_stats.overall_utility = Weight("overall utility")
all_stats.overall_utility.extra_weight = -0.5
all_stats.overall_captaincy = Weight("overall captaincy")
all_stats.overall_support = Weight("overall support")

# offense weights
all_stats.slugger = Weight("slugging")
all_stats.reliable_hitter = Weight("contact hitter")
all_stats.manufacturer = Weight("runs manufacturer")
all_stats.utility_hitter = Weight("utility hitter")
all_stats.utility_hitter.extra_weight = 0.25

# pitching weights
all_stats.pitcher_speed = Weight("fastball pitcher")
all_stats.pitcher_speed.extra_weight = 0.25
all_stats.pitcher_movement = Weight("movement pitcher")
all_stats.pitcher_speed.extra_weight = 0.25
all_stats.pitcher_accuracy = Weight("control pitcher")
all_stats.pitcher_accuracy.extra_weight = 0.25
all_stats.pitcher_special = Weight("special pitcher")

# fielding weights
all_stats.infield = Weight("infielder")
all_stats.outfield = Weight("outfielder")
all_stats.outfield.extra_weight = -0.75
all_stats.catcher = Weight("catcher")
all_stats.pitcher_generic = Weight("pitcher")

# TODO: personality and element handling

# Rating stats
# offense

all_stats.power = Rating('power')
all_stats.power.personality = all_stats.determination
all_stats.power.category = all_stats.batting
all_stats.power.abbreviate("POW")
all_stats.power.weight(all_stats.batting, 2)
all_stats.power.weight(all_stats.overall_power, 2)
all_stats.power.weight(all_stats.slugger, 2)

all_stats.contact = Rating('contact')
all_stats.contact.personality = all_stats.enthusiasm
all_stats.contact.category = all_stats.batting
all_stats.contact.abbreviate("CON")
all_stats.contact.weight(all_stats.batting, 3)
all_stats.contact.weight(all_stats.overall_power, 0.5)
all_stats.contact.weight(all_stats.overall_smallball, 2)
all_stats.contact.weight(all_stats.slugger, 1)
all_stats.contact.weight(all_stats.utility_hitter, 1)

all_stats.discipline = Rating('discipline')
all_stats.discipline.personality = all_stats.stability
all_stats.discipline.category = all_stats.batting
all_stats.discipline.abbreviate("DSC")
all_stats.discipline.weight(all_stats.batting, 1)
all_stats.discipline.weight(all_stats.overall_power, 1)
all_stats.discipline.weight(all_stats.overall_smallball, 1)
all_stats.discipline.weight(all_stats.overall_utility, 0.25)
all_stats.discipline.weight(all_stats.reliable_hitter, 1)
all_stats.discipline.weight(all_stats.manufacturer, 1)

all_stats.speed = Rating('speed')
all_stats.speed.personality = all_stats.enthusiasm
all_stats.speed.category = all_stats.baserunning
all_stats.speed.abbreviate("SPD")
all_stats.speed.weight(all_stats.baserunning, 3)
all_stats.speed.weight(all_stats.overall_smallball, 1)
all_stats.speed.weight(all_stats.manufacturer, 2)

all_stats.bravery = Rating('bravery')
all_stats.bravery.personality = all_stats.determination
all_stats.bravery.category = all_stats.baserunning
all_stats.bravery.abbreviate("BRV")
all_stats.bravery.weight(all_stats.baserunning, 1)
all_stats.bravery.weight(all_stats.overall_smallball, 0.5)
all_stats.bravery.weight(all_stats.manufacturer, 1)

all_stats.timing = Rating('timing')
all_stats.timing.personality = all_stats.insight
all_stats.timing.category = all_stats.baserunning
all_stats.timing.abbreviate("TMG")
all_stats.timing.weight(all_stats.baserunning, 2)
all_stats.timing.weight(all_stats.overall_smallball, 0.75)
all_stats.timing.weight(all_stats.overall_utility, 0.25)
all_stats.timing.weight(all_stats.manufacturer, 1)

# defense

all_stats.reach = Rating('reach')
all_stats.reach.personality = 'enthusiasm'
all_stats.reach.category = all_stats.defense
all_stats.reach.abbreviate("RCH")
all_stats.reach.weight(all_stats.defense, 1)
all_stats.reach.weight(all_stats.overall_fielding, 1)
all_stats.reach.weight(all_stats.outfield, 2)

all_stats.grabbiness = Rating('grabbiness')
all_stats.grabbiness.personality = all_stats.stability
all_stats.grabbiness.category = all_stats.defense
all_stats.grabbiness.abbreviate("GRA")
all_stats.grabbiness.weight(all_stats.defense, 1.5)
all_stats.grabbiness.weight(all_stats.overall_fielding, 1)
all_stats.grabbiness.weight(all_stats.pitcher_special, 1)
all_stats.grabbiness.weight(all_stats.infield, 1)
all_stats.grabbiness.weight(all_stats.catcher, 1)

all_stats.throwing = Rating('throwing')
all_stats.throwing.personality = all_stats.stability
all_stats.throwing.abbreviate("THR")
all_stats.throwing.weight(all_stats.defense, 1)
all_stats.throwing.weight(all_stats.overall_fielding, 0.75)
all_stats.throwing.weight(all_stats.outfield, 1)
all_stats.throwing.weight(all_stats.catcher, 0.5)
all_stats.throwing.weight(all_stats.pitcher_special, .5)

all_stats.awareness = Rating('awareness')
all_stats.awareness.personality = all_stats.insight
all_stats.awareness.abbreviate("AWR")
all_stats.awareness.weight(all_stats.defense, 0.5)
all_stats.awareness.weight(all_stats.overall_fielding, 0.5)
all_stats.awareness.weight(all_stats.pitching, 0.25)
all_stats.awareness.weight(all_stats.catcher, 1)
all_stats.awareness.weight(all_stats.outfield, 0.5)
all_stats.awareness.weight(all_stats.pitcher_special, .75)

all_stats.calling = Rating('calling')
all_stats.calling.personality = all_stats.insight
all_stats.calling.category = all_stats.defense
all_stats.calling.abbreviate('CAL')
all_stats.calling.weight(all_stats.defense, 0.5)
all_stats.calling.weight(all_stats.pitching, 0.25)
all_stats.calling.weight(all_stats.overall_fielding, 0.25)
all_stats.calling.weight(all_stats.catcher, 3)

all_stats.force = Rating('force')
all_stats.force.personality = all_stats.determination
all_stats.force.category = all_stats.pitching
all_stats.force.abbreviate("FOR")
all_stats.force.weight(all_stats.pitching, 2)
all_stats.force.weight(all_stats.overall_fastball, 2)
all_stats.force.weight(all_stats.pitcher_speed, 2)
all_stats.force.weight(all_stats.pitcher_generic, 2)

all_stats.trickery = Rating('trickery')
all_stats.trickery.personality = all_stats.insight
all_stats.trickery.category = all_stats.pitching
all_stats.trickery.abbreviate("TRK")
all_stats.trickery.weight(all_stats.pitching, 1.5)
all_stats.trickery.weight(all_stats.overall_trickery, 2)
all_stats.trickery.weight(all_stats.overall_utility, 0.25)
all_stats.trickery.weight(all_stats.pitcher_movement, 2)
all_stats.trickery.weight(all_stats.pitcher_generic, 1.5)

all_stats.accuracy = Rating('accuracy')
all_stats.accuracy.personality = all_stats.stability
all_stats.accuracy.category = all_stats.pitching
all_stats.accuracy.abbreviate('ACC')
all_stats.accuracy.weight(all_stats.pitching, 1)
all_stats.accuracy.weight(all_stats.overall_fastball, 1)
all_stats.accuracy.weight(all_stats.overall_trickery, 1)
all_stats.accuracy.weight(all_stats.pitcher_accuracy, 2)
all_stats.accuracy.weight(all_stats.pitcher_generic, 1)

all_stats.leadership = Rating('leadership')
all_stats.leadership.personality = all_stats.determination
all_stats.leadership.category = all_stats.edge
all_stats.leadership.abbreviate("LED")
all_stats.leadership.weight(all_stats.edge, 0.5)
all_stats.leadership.weight(all_stats.overall_captaincy, 1)

all_stats.heckling = Rating('heckling')
all_stats.heckling.personality = all_stats.enthusiasm
all_stats.heckling.category = all_stats.edge
all_stats.heckling.abbreviate('HCK')
all_stats.heckling.weight(all_stats.edge, 0.5)
all_stats.heckling.weight(all_stats.overall_captaincy, 0.5)

all_stats.sparkle = Rating('sparkle')
all_stats.sparkle.personality = all_stats.insight
all_stats.sparkle.category = all_stats.edge
all_stats.sparkle.abbreviate('SPK')
all_stats.sparkle.weight(all_stats.edge, 1.5)
all_stats.sparkle.weight(all_stats.total_offense, 0.25)
all_stats.sparkle.weight(all_stats.total_defense_pitching, 0.25)
all_stats.sparkle.weight(all_stats.overall_trickery, 0.25)
all_stats.sparkle.weight(all_stats.overall_utility, 1.5)
all_stats.sparkle.weight(all_stats.utility_hitter, 1)
all_stats.sparkle.weight(all_stats.pitcher_special, 2)

all_stats.infotech = Rating('i.t.')
all_stats.infotech.personality = all_stats.stability
all_stats.infotech.category = all_stats.edge
all_stats.infotech.abbreviate('I.T')
all_stats.infotech.weight(all_stats.edge, 1)
all_stats.infotech.weight(all_stats.overall_utility, 1)

all_stats.endurance = Rating('endurance')
all_stats.endurance.personality = all_stats.determination
all_stats.endurance.category = all_stats.vitality
all_stats.endurance.abbreviate("EDR")
all_stats.endurance.weight(all_stats.vitality, 1)

all_stats.energy = Rating('energy')
all_stats.energy.personality = all_stats.enthusiasm
all_stats.energy.category = all_stats.vitality
all_stats.energy.abbreviate("ENG")
all_stats.energy.weight(all_stats.vitality, 1)

all_stats.positivity = Rating('positivity')
all_stats.positivity.personality = all_stats.stability
all_stats.positivity.category = all_stats.vitality
all_stats.positivity.abbreviate("POS")
all_stats.positivity.weight(all_stats.vitality, 1)

all_stats.recovery = Rating('recovery')
all_stats.recovery.personality = all_stats.insight
all_stats.recovery.category = all_stats.vitality
all_stats.recovery.abbreviate("RCV")
all_stats.recovery.weight(all_stats.vitality, 1)

all_stats.cool = Rating('cool')
all_stats.cool.personality = all_stats.determination
all_stats.cool.category = all_stats.social
all_stats.cool.abbreviate("COO")
all_stats.cool.weight(all_stats.social, 1)
all_stats.cool.weight(all_stats.overall_utility, 0.5)

all_stats.hangouts = Rating('hangouts')
all_stats.hangouts.personality = all_stats.enthusiasm
all_stats.hangouts.category = all_stats.social
all_stats.hangouts.abbreviate("HNG")
all_stats.hangouts.weight(all_stats.social, 1)
all_stats.hangouts.weight(all_stats.overall_support, 1)

all_stats.support = Rating('support')
all_stats.support.personality = all_stats.stability
all_stats.support.category = all_stats.social
all_stats.support.abbreviate("SUP")
all_stats.support.weight(all_stats.social, 1)
all_stats.support.weight(all_stats.overall_support, 2)

all_stats.teaching = Rating('teaching')
all_stats.teaching.personality = all_stats.insight
all_stats.teaching.category = all_stats.social
all_stats.teaching.abbreviate("TCH")
all_stats.teaching.weight(all_stats.social, 1)
all_stats.teaching.weight(all_stats.overall_captaincy, 1)

for stat in all_stats['rating']:
    stat.default = 0


# Descriptors

all_stats.overall_descriptor = Calculatable('overall descriptor', StatKinds.descriptor)
all_stats.overall_descriptor.default = "The Observed"

all_stats.offense_descriptor = Calculatable('offense descriptor', StatKinds.descriptor)
all_stats.offense_descriptor.default = "Unevaluated Hitter"

all_stats.defense_descriptor = Calculatable('defense descriptor', StatKinds.descriptor)
all_stats.defense_descriptor.default = "Unable To Catch A Cold"

all_stats.personality_descriptor = Calculatable('personality descriptor', StatKinds.descriptor)
all_stats.personality_descriptor.default = "Smol Bean"

all_stats.offense_position = Calculatable('offense position', StatKinds.descriptor)
all_stats.offense_position.default = 'Bench'

all_stats.defense_position = Calculatable('defense position', StatKinds.descriptor)
all_stats.defense_position.default = 'Bullpen'



all_stats.vibes = Stat('vibes', StatKinds.condition)
all_stats.vibes.abbreviate("VIB")
all_stats.vibes.default = 1.0

all_stats.stamina = Stat('stamina', StatKinds.condition)
all_stats.stamina.abbreviate('STA')
all_stats.stamina.default = 1.0

all_stats.mood = Stat('mood', StatKinds.condition)
all_stats.mood.abbreviate("MOD")
all_stats.mood.default = 1.0

all_stats.soul = Stat('soul', StatKinds.condition)
all_stats.soul.abbreviate("SOL")
all_stats.soul.default = 1.0


all_stats.name = Stat('name', StatKinds.character)
all_stats.name.abbreviate("NAME")
all_stats.name.default = "WYATT MASON"

all_stats.team = Stat('team', StatKinds.character)
all_stats.team.abbreviate("TEAM")
all_stats.team.default = "DETROIT DEFAULT"

all_stats.number = Stat('number', StatKinds.character)
all_stats.number.abbreviate("#")
all_stats.number.default = "-1"

all_stats.fingers = Stat('fingers', StatKinds.character)
all_stats.fingers.default = 9

all_stats.is_pitcher = Stat('is pitcher', StatKinds.character)
all_stats.is_pitcher.default = False

all_stats.clutch = Stat('clutch', StatKinds.character)
all_stats.clutch.default = 0.2
all_stats.clutch.abbreviate("CLT")

all_stats.pull = Stat('pull', StatKinds.character)
all_stats.pull.default = -1

all_stats.element = Stat('element', StatKinds.character)
all_stats.element.default = "Basic"
all_stats.element.abbreviate("ELE")

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


if __name__ == "__main__":
    for p in all_stats[StatKinds.personality]:
        print(p.name.upper())
        for s in all_stats[p]:
            print(f"\t{s}")
    print("\n")
    for c in all_stats[StatKinds.category]:
        print(c.name.upper())
        for s in all_stats[c]:
            print(f"\t{s}")

    print("\r\n\r\n")
    for weight in all_stats[StatKinds.weight]:
        if "overall" not in weight.name and "total" not in weight.name:
            print(weight.nice_string())
    print('\r\n')
    for weight in all_stats[StatKinds.weight]:
        if "overall" in weight.name and "total" not in weight.name:
            print(weight.nice_string())
    print('\r\n')
    for weight in all_stats[StatKinds.weight]:
        if "total" in weight.name:
            print(weight.nice_string())

    print("\r\n\r\nPersonality Report:")
    print("TBR")

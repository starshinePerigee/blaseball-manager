"""
Stats are classes that define a stat's behavior. This module contains the code that defines types of stats,
without describing any specific stats.

this module also handles definitions for kinds and dependencies - although those should probably be moved out at some
point?
"""

from enum import Enum, auto
from typing import Union, Callable, Dict, Tuple, List, Optional
from numpy.random import rand

from loguru import logger

from blaseball.stats.playerbase import PlayerBase


# a stat kind is the relative type of stat; these are used for categorization and dependencies
class Kinds(Enum):
    # the number in this enum
    character = auto()  # a player's character stats, such as name and fingers
    personality = auto()  # core personality types
    category = auto()  # stat categories, like "batting"
    rating = auto()  # 0-2 numeric ratings that govern a player's ball ability
    weight = auto()  # a weight is a stat representing a summary of several other stats.
    total_weight = auto()  # a summary weight that depends on other weights
    descriptor = auto()  # english derived stat descriptors based on a weight
    condition = auto()  # a player's condition stats, such as mood and soul
    performance = auto()  # a tracked performance metric, such as number of hits
    derived = auto()  # a derived, non-averaging statistic such as at-bats
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

BASE_DEPENDENCIES_GLOBAL = {
    # make sure you include all dependencies, include dependencies of dependencies.
    # Listed in recalculation order!
    Kinds.category: [Kinds.rating],
    Kinds.weight: [Kinds.rating, Kinds.category],
    Kinds.total_weight: [Kinds.rating, Kinds.category,
                         Kinds.weight],
    Kinds.descriptor: [Kinds.rating, Kinds.character, Kinds.personality, Kinds.category,
                       Kinds.weight, Kinds.total_weight],
    Kinds.derived: [Kinds.performance],
    Kinds.averaging: [Kinds.performance, Kinds.derived],
}

BASE_DEPENDENCIES_TEST = {
    Kinds.test_dependent: [Kinds.test]
}

# recalculation order matters for stats which depend on other stats, so it's defined here.
# Stats which share a Kind are recalculated in the order they are first created - usually the order they are
# defined in stats.py

RECALCULATION_ORDER_GLOBAL = [
    Kinds.character,
    Kinds.personality,
    Kinds.rating,
    Kinds.category,
    Kinds.weight,
    Kinds.total_weight,
    Kinds.descriptor,
    Kinds.condition,
    Kinds.performance,
    Kinds.derived,
    Kinds.averaging,
]

RECALCULATION_ORDER_TEST = [
    Kinds.test,
    Kinds.test_dependent
]


# this is the default dictionary; which is a big dictionary for indexing / filtering methods
# if you need a second dictionary you can create and pass one.
all_base = PlayerBase(RECALCULATION_ORDER_GLOBAL, BASE_DEPENDENCIES_GLOBAL)


class Stat:
    """This is the top level class for a stat. This doesn't carry any numeric info, but it's a key to the
    PlayerBase and has a number of useful functions to create and maintain the PlayerBase.

    This is not a abstract base class, but it does have some abstract functions and members.

    """
    def __init__(
            self,
            name: str,
            kind: Kinds,
            default=None,
            initial_function=None,
            value_function=None,
            playerbase: PlayerBase = None
    ):
        self.name = name

        if playerbase is None:
            playerbase = all_base

        if name in playerbase.stats:
            raise KeyError(f"Stat {name} already defined!")

        self.display_name = None

        self.kind = kind
        self.abbreviation = None  # the abbreviation for this stat
        self.default = default  # default sets the default value of this column.
        # Default also sets the default TYPE of that column! Don't use an int default if you're going to put
        # floats in it later!!
        self.initial_function = initial_function
        self.value_function = value_function

        self._linked_playerbase = playerbase
        playerbase.add_stat(self)

    def __getitem__(self, player_index: int):
        return self._linked_playerbase[player_index][self]

    def calculate_initial(self, player_index):
        """Calculate the initial value for this based on its default value.
        Default can be function with parameters 'playerbase df' and 'cid'"""
        if self.initial_function is not None:
            return self.initial_function(self._linked_playerbase, player_index)
        else:
            return self.default

    def calculate_value(self, player_index):
        """Calculate the current value for this stat based on its current value"""
        if self.value_function is not None:
            return self.value_function(self._linked_playerbase, player_index)
        else:
            logger.debug(f"abstract calculate_value called for {self}")
            return self._linked_playerbase.df.at[player_index, self]

    def abbreviate(self, abbreviation: str):
        """Add an abbreviation for this stat, making sure it's not clobbering an exsiting one."""
        for stat in self._linked_playerbase.stats.values():
            if stat.abbreviation == abbreviation:
                raise KeyError(f"Duplicate Abbreviation {abbreviation}! "
                               f"Collision between {stat.name} and {self.name}")
        self.abbreviation = abbreviation

    def weight(self, weight: "Weight", value: float):
        """Add this stat to a Weight"""
        weight.add(self, value)

    def __str__(self):
        if self.display_name is None:
            return self.name.title()
        else:
            return self.display_name.title()

    def __repr__(self):
        return f"{type(self).__name__}({self.name}, {self.kind.name})"

    def __eq__(self, other):
        if isinstance(other, Stat):
            return self.name == other.name
        else:
            return self.name == other

    def __hash__(self):
        # this lets us index dataframes by stat or by name
        return hash(self.name)


class Calculatable(Stat):
    """
    A Calculatable is any stat that depends on other stats for its value.
    For instance, a players Batting Average depends on Hits and At-Bats.
    """
    def __init__(
            self,
            name: str,
            kind: Kinds,
            value_formula: Callable = None,
            playerbase: PlayerBase = None,
    ):
        super().__init__(name, kind, -1.0, None, value_formula, playerbase)

        if len(self._linked_playerbase.df) > 0:
            # create default values
            initial_values = [self.calculate_initial(i) for i in self._linked_playerbase.df.index]
            self._linked_playerbase.df[name] = initial_values


class Weight(Stat):
    """a Weight is a special stat meant to represent a weighted average of several other stats.
     It is a Stat, not a Calculatable, because it's defined by its own built-in functions instead of
     wrapped ones.

     Because it is created in advance, it starts stale; so the initial value is set to something
     obvious and breaking. Make sure it is recalculated prior to use.
     """
    def __init__(
            self,
            name: str,
            kind: Kinds = Kinds.weight,
            playerbase: PlayerBase = None
    ):
        super().__init__(name, kind, -1.0, None, None, playerbase)

        self.stats = {}
        self.extra_weight = 0

    def add(self, stat: Stat, value: Union[float, int]):
        """Add a stat to the total weight.
        To add extra weight, access the attribute directly."""
        self.stats[stat] = float(value)

    def calculate_initial(self, player_index):
        logger.debug(f"Initial call for Weight {self.name} called!")
        return self.default

    def calculate_value(self, player_index):
        weight = sum(self.stats.values()) + self.extra_weight
        total = sum([self._linked_playerbase[player_index][stat] * self.stats[stat] for stat in self.stats])
        if total == 0:
            return 0
        elif weight == 0:
            return self.default
        else:
            return total / weight

    def nice_string(self) -> str:
        nice = self.name + ":"
        for v, s in sorted(zip(self.stats.values(), self.stats.keys()), reverse=True, key=lambda x: x[0]):
            nice += f" {s} {v}"
        if self.extra_weight != 0:
            nice += f" extra {self.extra_weight}"
        return nice


class Descriptor(Stat):
    """Descriptors are text string representations of ratios of weights.
    Effectively, they're a way of translating lots of different stats into a single user-understandable string.

    The process goes like this:
    Stats get bundled and weighted into a Weight, which is a number.
    Weights get bundled and compared into a descriptor, which is a string.

    Creating a descriptor is changing a ton from the previous version, now it's nice and stats/class-based.
    """
    def __init__(
            self,
            name: str,
            kind: Kinds = Kinds.descriptor,
            default: str = None,
            playerbase: PlayerBase = None
    ):
        if default is None:
            default = f"{name.upper()}_DEFAULT"
        super().__init__(name, kind, default, None, None, playerbase)

        self.weights = {}
        self.all = None
        self.secondary_threshold = 0.0  # what percentage of the primary stat the next biggest needs to be counted.

    def add_weight(
            self,
            stat: Stat,
            value: Union[str, Dict]
    ):
        """This is how you add a weight. There are a lot of options here!
        value can be one of the following:
        - a string
        - a float-keyed dict
        - a stat-keyed dict of dicts
        -- these second layer dicts must either be strings or float-keyed dicts
        """
        self.weights[stat] = value

    def add_all(self, value: Union[str, Dict]):
        """Add an 'all stats' weight option"""
        self.all = value

    @staticmethod
    def _parse_value_dict(value_dict: Dict[float, str], value: float) -> str:
        for key in sorted(value_dict.keys()):
            if value <= key:
                return value_dict[key]
        logger.warning(f"Could not build a descriptor! "
                       f"Max threshold value: {value} vs keys: {value_dict}")
        return value_dict[sorted(value_dict.keys())[-1]]

    @staticmethod
    def _parse_second_level(first_level_result, highest_stat, highest_value, player_index, secondary_threshold):

        if isinstance(first_level_result, str):
            #  Dict[Stat: str]
            return first_level_result

        # pull a key at random to check its type
        result_key_instance = next(iter(first_level_result))

        if isinstance(result_key_instance, (int, float)):
            # this is a value dictionary
            return Descriptor._parse_value_dict(first_level_result, highest_value)

        # if we reach here, current_level_result is a second dictionary of stat: value pairs
        # ie: there's another level
        # check to make sure it's not a single dict element tho lmao
        if len(first_level_result) < 2:
            raise RuntimeError(f"Bad first level resul in descriptor! result dict: '{first_level_result}'")

        # build another tuple list
        second_stat_pairs = [(weight[player_index], weight) for weight in first_level_result]
        second_stat_pairs.sort(key=lambda x: x[0], reverse=True)

        first_is_above_zero = second_stat_pairs[0][0] > 0
        first_in_secondary = highest_stat in first_level_result
        if first_is_above_zero and first_in_secondary:
            second_is_above_threshold = second_stat_pairs[1][0] / highest_value > secondary_threshold
        else:
            second_is_above_threshold = False

        if second_is_above_threshold:
            # we use the secondary
            final_result = first_level_result[second_stat_pairs[1][1]]
        else:
            final_result = first_level_result[second_stat_pairs[0][1]]

        if isinstance(final_result, str):
            return final_result
        else:
            return Descriptor._parse_value_dict(final_result, highest_value)

    def calculate_value(self, player_index):
        """
        This crunches through an arbitrarily-nested dict of weights to generate a descriptor.
        See add_weight() for description on how to format it.

        This works like so:
        there are four options. The first pass is always going to be a stats: foo dictionary pair.
        foo is one of several things
            - if it's a string, find the largest stat and return its string
            - if it's a number-keyed dict, call _parse_value_dict() to use the top level value
            - if it's another stat-keyed dict, find the largest and second largest stat. and parse
            appropriately

        this has gotten out of hand, and probably needs another refactor in the future :c
        """
        # first, catch some dumb cases
        if len(self.weights) == 0:
            logger.warning(f"Called get_descriptor() of uninitialized weight {self}")
            return self.default
        elif len(self.weights) == 1:
            highest_stat = list(self.weights)[0]
            return self._parse_second_level(
                list(self.weights.values())[0],
                highest_stat,
                highest_stat[player_index],
                player_index,
                self.secondary_threshold
            )

        # build a (value, stat) tuple list
        value_stat_pairs = [(weight[player_index], weight) for weight in self.weights]
        value_stat_pairs.sort(key=lambda x: x[0], reverse=True)

        # handle some special cases
        if value_stat_pairs[0][0] == 0:
            # if highest_stat is 0, that means everything is zero (or the stats go negative)
            # either way, we need to avoid a div/0 error
            if self.all is not None:
                # use 'all' if it's an option
                highest_stat = 'all'
                current_level_result = self.all
            else:
                # pick something arbitrarily lol
                highest_stat = value_stat_pairs[0][1]
                current_level_result = self.weights[value_stat_pairs[0][1]]
        # check for the 'all' condition:
        elif self.all is not None and value_stat_pairs[-1][0] / value_stat_pairs[0][0] > self.secondary_threshold:
            highest_stat = 'all'
            current_level_result = self.all
        else:
            # this is basically the 'nominal' case
            highest_stat = value_stat_pairs[0][1]
            current_level_result = self.weights[value_stat_pairs[0][1]]

        return self._parse_second_level(
            current_level_result,
            highest_stat,
            value_stat_pairs[0][0],
            player_index,
            self.secondary_threshold
        )


class Rating(Stat):
    """A rating is one of a player's "fixed" "core" stats, such as their speed.
    It is not a Calculatable, becuase it doesn't get updated in the same way.
    Instead it's meant to handle the overhead that's built into a rating, such as
    creating it's base_ version, init, and update.

    """
    def __init__(
            self,
            name: str,
            personality: Stat = None,
            category: Stat = None,
            playerbase: PlayerBase = None,
            kind: Kinds = Kinds.rating
    ):
        super().__init__(
            name,
            kind,
            default=-1.0,
            initial_function=None,
            value_function=None,
            playerbase=playerbase
        )

        self.personality = personality  # the personality stat that governs this stat (applies to ratings)
        self.category = category  # the stat category this applies to

    def calculate_initial(self, player_index):
        """
        Rolls this stat based on the relevant personality, and updates the base value.
        """
        personality_value = self._linked_playerbase.df.at[player_index, self.personality.name]
        scale_factor = max(min(personality_value, 1.0), 0.5)
        # traits can result in personalities higher than 1. if this happens, it's cool, so
        # this bit makes sure you get that bonus
        if personality_value > 1:
            return rand() * scale_factor + personality_value - 1
        else:
            return rand() * scale_factor

    def calculate_value(self, player_index):
        """Modifiers are calculated and saved by the player class!"""
        return self._linked_playerbase.df.at[player_index, self]


def build_averaging(
        count_stat: Stat,
        average_stat_name: str,
        total_stat_name: Optional[str] = None,
        average_kind: Kinds = Kinds.averaging,
        total_kind: Kinds = Kinds.performance,
        playerbase: Optional[PlayerBase] = None
) -> Tuple[Calculatable, Stat]:
    if total_stat_name is None:
        total_stat_name = average_stat_name.replace('average', 'total')

    total_stat = Stat(
        total_stat_name,
        total_kind,
        0,
        playerbase=playerbase
    )

    def averaging_function(pb_, cid):
        count = count_stat[cid]
        if count == 0:
            return 0.0
        else:
            return total_stat[cid] / count_stat[cid]

    averaging_stat = Calculatable(
        average_stat_name,
        average_kind,
        averaging_function,
        playerbase=playerbase
    )

    return averaging_stat, total_stat

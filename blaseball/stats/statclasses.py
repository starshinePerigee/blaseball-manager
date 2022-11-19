"""
defines stats for use in other classes

does not handle caching! that's handled in Player. But some of the logic is defined here, via Kinds
"""

from enum import Enum, auto
from typing import Union, Callable, Dict, Tuple, List, Optional
from numpy.random import rand

from loguru import logger

from blaseball.util.dfmap import dataframe_map
from blaseball.stats.playerbase import PlayerBase


# a stat kind is the relative type of a stat; these are used for categorization and dependencies
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
    Kinds.averaging: [Kinds.performance],
}

BASE_DEPENDENCIES_TEST = {
    Kinds.test_dependent: [Kinds.test]
}

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
    Kinds.averaging,
    Kinds.test,
    Kinds.test_dependent
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
        logger.debug(f"abstract calculate_value called for {self}")
        return self._linked_playerbase.df.at[player_index, self]

    def abbreviate(self, abbreviation: str):
        for stat in self._linked_playerbase.stats.values():
            if stat.abbreviation == abbreviation:
                raise KeyError(f"Duplicate Abbreviation {abbreviation}! "
                               f"Collision between {stat.name} and {self.name}")
        self.abbreviation = abbreviation

    def weight(self, weight: "Weight", value: float):
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
            initial_formula: Callable = None,
            value_formula: Callable = None,
            playerbase: PlayerBase = None,
    ):
        super().__init__(name, kind, -1.0, None, playerbase)

        # default and value should either be a mappable callable (via dfmap), constant, or None
        if initial_formula is not None:
            self._wrapped_initial = dataframe_map(initial_formula, self._linked_playerbase.df)
        else:
            self._wrapped_initial = dataframe_map(lambda: None, self._linked_playerbase.df)

        if value_formula is not None:
            self._wrapped_value = dataframe_map(value_formula, self._linked_playerbase.df)
        else:
            self._wrapped_value = dataframe_map(lambda: None, self._linked_playerbase.df)

        if len(self._linked_playerbase.df) > 0:
            # create default values
            initial_values = [self.calculate_initial(i) for i in self._linked_playerbase.df.index]
            self._linked_playerbase.df[name] = initial_values

    def calculate_initial(self, player_index):
        return self._wrapped_initial(player_index)

    def calculate_value(self, player_index):
        return self._wrapped_value(player_index)


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
        super().__init__(name, kind, -1.0, None, playerbase)

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
        if weight == 0:
            return self.default

        total = sum([self._linked_playerbase.df.at[player_index, stat.name] * self.stats[stat] for stat in self.stats])
        return total / weight

    def nice_string(self) -> str:
        nice = self.name + ":"
        for v, s in sorted(zip(self.stats.values(), self.stats.keys()), reverse=True):
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
        super().__init__(name, kind, default, None, playerbase)

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
            if value < key:
                return value_dict[key]
        raise RuntimeError(f"Could not build a descriptor! "
                           f"Max threshold value: {value} vs keys: {value_dict}")

    def get_descriptor(self, player_index):
        """
        This crunches through an arbitrarily-nested dict of weights to generate a descriptor.
        See add_weight() for description on how to format it.

        This works like so:
        there are four options. The first pass is always going to be a stats: foo dictionary pair.
        foo is one of several things
            - if it's a string, find the largest stat and return it's string
            - if it's a number-keyed dict, call _parse_value_dict() to use the top level value
            - if it's another stat-keyed dict, find the largest and second largest stat. then,
            -- if the second largest is above
        """
        # first index the top level
        # check for the 'all' condition
        value_stat_dict = {weight[player_index]: weight for weight in self.weights}
        highest_stat_value = max(value_stat_dict)

        if self.all is not None and min(value_stat_dict) / highest_stat_value > self.secondary_threshold:
            highest_stat = 'all'
            current_level_result = self.all
        else:
            highest_stat = value_stat_dict.pop(highest_stat_value)
            current_level_result = self.weights[highest_stat]

        if isinstance(current_level_result, str):
            #  Dict[Stat: str]
            return current_level_result

        # pull a key at random to check its type
        result_key_instance = next(iter(current_level_result))

        if isinstance(result_key_instance, (int, float)):
            # this is a value dictionary
            return self._parse_value_dict(current_level_result, highest_stat_value)

        # if we reach here, current_level_result is a dictionary of stat: value pairs
        # ie: there's another level

        # first we need to find the second level largest stat and value
        second_level_value_stat_dict = {weight[player_index]: weight for weight in current_level_result}
        highest_second_level_value = max(second_level_value_stat_dict)

        if second_level_value_stat_dict[highest_second_level_value] is highest_stat and \
                len(second_level_value_stat_dict) > 1:
            second_level_value_stat_dict.pop(highest_second_level_value)
            next_highest_value = max(second_level_value_stat_dict)
        else:
            next_highest_value = highest_second_level_value

        # calculate the next highest to top level ratio
        try:
            if next_highest_value / highest_stat_value >= self.secondary_threshold:
                # we are within the ratio, so we're taking the secondary stat fork
                final_stat = second_level_value_stat_dict[next_highest_value]
            else:
                final_stat = highest_stat
        except ZeroDivisionError:  # can happen if one of the items is 0.
            final_stat = highest_stat

        second_level_result = current_level_result[final_stat]
        if isinstance(second_level_result, str):
            return second_level_result
        else:
            return self._parse_value_dict(second_level_result, highest_stat_value)

    def calculate_value(self, player_index):
        if len(self.weights) == 0:
            return self.default  # return default if uninitialized descriptor
        else:
            return self.get_descriptor(player_index)


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

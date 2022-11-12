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


# this is the default dictionary; which is a big dictionary for indexing / filtering methods
# if you need a second dictionary you can create and pass one.
all_base = PlayerBase()


# a stat kind is the relative type of a stat; these are used for categorization and dependencies
# this is not ordered. Stats are generated in column order (ie: the order they're defined in Stats)
class Kinds(Enum):
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


class Stat:
    """This is the top level class for a stat. This doesn't carry any numeric info, but it's a key to the
    PlayerBase and has a number of useful functions to create and maintain the PlayerBase.

    This is not a abstract base class, but it does have some abstract functions and members.

    """
    running_id = 0

    def __init__(
            self,
            name: str,
            kind: Kinds,
            default=None,
            pb: PlayerBase = None
    ):
        self.name = name

        if pb is None:
            pb = all_base

        if name in pb.stats:
            raise KeyError(f"Stat {name} already defined!")

        self._hash = hash(f"{name}_{Stat.running_id}")
        Stat.running_id += 1

        self.kind = kind
        self.abbreviation = None  # the abbreviation for this stat
        self.default = default

        self._linked_dataframe = pb.df
        self._linked_dict = pb.stats
        pb.add_stat(self)

    def __getitem__(self, player_index: int):
        return self._linked_dataframe.at[player_index, self.name]

    def calculate_initial(self, player_index):
        """Calculate the initial value for this based on its default value.
        Default can be function with parameters 'playerbase df' and 'cid'"""
        if isinstance(self.default, Callable):
            return self.default(self._linked_dataframe, player_index)
        else:
            return self.default

    def calculate_value(self, player_index):
        """Calculate the current value for this stat based on its current value"""
        logger.debug(f"abstract calculate_value called for {self.name}")
        return self._linked_dataframe.at[player_index, self.name]

    def abbreviate(self, abbreviation: str):
        for stat in self._linked_dict.values():
            if stat.abbreviation == abbreviation:
                raise KeyError(f"Duplicate Abbreviation {abbreviation}! "
                               f"Collision between {stat.name} and {self.name}")
        self.abbreviation = abbreviation

    def weight(self, weight: "Weight", value: float):
        weight.add(self, value)

    def __str__(self):
        return self.name.title()

    def __repr__(self):
        return f"{type(self).__name__}({self.name}, {self.kind.name}) x{self._hash}"

    def __hash__(self):
        return self._hash


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
    Kinds.rating: [Kinds.base_rating],
    Kinds.category: [Kinds.rating, Kinds.base_rating],
    Kinds.weight: [Kinds.rating, Kinds.base_rating, Kinds.category],
    Kinds.total_weight: [Kinds.rating, Kinds.base_rating, Kinds.category,
                         Kinds.weight],
    Kinds.descriptor: [Kinds.rating, Kinds.base_rating, Kinds.character, Kinds.category,
                       Kinds.weight, Kinds.total_weight],
    Kinds.averaging: [Kinds.performance],
    Kinds.test_dependent: [Kinds.test]
}

recalculation_order = BASE_DEPENDENCIES.keys()

dependencies = BASE_DEPENDENCIES
# fill in everything that's not a dependent
for kind_ in Kinds:
    if kind_ not in dependencies:
        dependencies[kind_] = []

# invert the array so we know what to look up / set the stale flag for when we write
dependents = {kind: [] for kind in Kinds}
for kind_ in Kinds:
    for dependency in dependencies[kind_]:
        dependents[dependency] += [kind_]


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
            pb: PlayerBase = None,
    ):
        super().__init__(name, kind, None, pb)

        # default and value should either be a mappable callable (via dfmap), constant, or None
        if initial_formula is not None:
            self._wrapped_initial = dataframe_map(initial_formula, self._linked_dataframe)
        else:
            self._wrapped_initial = dataframe_map(lambda: None, self._linked_dataframe)

        if value_formula is not None:
            self._wrapped_value = dataframe_map(value_formula, self._linked_dataframe)
        else:
            self._wrapped_value = dataframe_map(lambda: None, self._linked_dataframe)

        if len(self._linked_dataframe) > 0:
            # create default values
            initial_values = [self.calculate_initial(i) for i in self._linked_dataframe.index]
            self._linked_dataframe[name] = initial_values

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
            pb: PlayerBase = None
    ):
        super().__init__(name, kind, -1, pb)

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
        total = sum([self._linked_dataframe.at[player_index, stat.name] * self.stats[stat] for stat in self.stats])
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
            pb: PlayerBase = None
    ):
        super().__init__(name, kind, f"{name.upper()}_DEFAULT", pb)

        self.weights = {}
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

    @staticmethod
    def _parse_value_dict(value_dict: Dict[float, str], value: float) -> str:
        for key in sorted(value_dict.keys()):
            if value < key:
                return value_dict[key]
        raise RuntimeError(f"Could not build a descriptor! "
                           f"Max threshold value: {value} vs keys: {value_dict}")

    def get_descriptor(self, player_index, weights_dict):
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
        value_stat_dict = {weight[player_index]: weight for weight in weights_dict}
        highest_stat_value = max(value_stat_dict)

        highest_stat = value_stat_dict.pop(highest_stat_value)
        current_level_result = weights_dict[highest_stat]

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

        # first we need to find the second largest stat and value

        # check for size because if multiple values are equal, they'll clobber and we can run out
        # remember that value_stat_dict gets popped earlier
        if len(value_stat_dict) > 0:
            next_highest_value = max(value_stat_dict)
            next_highest_stat = value_stat_dict[next_highest_value]
        else:
            # this can happen if multiple values are equal; they'll collide when weight_values gets generated.
            next_highest_value = 0
            next_highest_stat = current_level_result

        # calculate the next highest to top level ratio
        try:
            if next_highest_value / highest_stat_value >= self.secondary_threshold:
                # we are within the ratio, so we're taking the secondary stat fork
                final_stat = next_highest_stat
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
        return self.get_descriptor(player_index, self.weights)


class Rating(Stat):
    """A rating is one of a player's "fixed" "core" stats, such as their speed.
    It is not a Calculatable, becuase it doesn't get updated in the same way.
    Instead it's meant to handle the overhead that's built into a rating, such as
    creating it's base_ version, init, and update.

    """
    def __init__(
            self,
            name: str,
            personality: Stat,
            category: Stat,
            base: Stat,
            pb: PlayerBase = None
    ):
        super().__init__(
            name,
            Kinds.rating,
            default=-1,
            pb=pb
        )

        self.personality = personality  # the personality stat that governs this stat (applies to ratings)
        self.category = category  # the stat category this applies to
        self.base_stat = base

    def calculate_initial(self, player_index):
        return self._linked_dataframe.at[player_index, self.base_stat.name]

    def calculate_value(self, player_index):
        return self._linked_dataframe.at[player_index, self.name]


class BaseRating(Stat):
    def __init__(
            self,
            name: str,
            personality: Stat,
            pb: PlayerBase = None
    ):
        super().__init__(
            name,
            Kinds.base_rating,
            default=-1,
            pb=pb
        )
        self.personality = personality

    def calculate_initial(self, player_index):
        """
        Rolls this stat based on the relevant personality, and updates the base value.
        """
        personality_value = self._linked_dataframe.at[player_index, self.personality.name]
        scale_factor = max(min(personality_value, 1), 0.5)
        # traits can result in personalities higher than 1. if this happens, it's cool, so
        # this bit makes sure you get that bonus
        if personality_value > 1:
            return rand() * scale_factor + personality_value - 1
        else:
            return rand() * scale_factor


def build_rating(
        name: str,
        personality: Stat,
        category: Optional[Stat],
        pb: PlayerBase = None
) -> Tuple[Rating, BaseRating]:
    base_rating = BaseRating("base " + name, personality, pb)
    rating = Rating(name, personality, category, base_rating, pb)
    return rating, base_rating


"""
defines stats for use in other classes

does not handle caching! that's handled in Player. But some of the logic is defined here, via Kinds
"""

from enum import Enum, auto
from typing import Union, Callable
from blaseball.stats.playerbase import PlayerBase

from loguru import logger

from blaseball.util.dfmap import dataframe_map



# this is the default dictionary; which is a big dictionary for indexing / filtering methods
# if you need a second dictionary you can create and pass one.
all_base = PlayerBase()


# a stat kind is the relative type of a stat; these are used for categorization and dependencies
# this is ordered! this is the order these will be generated
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

        pb.stats[name] = self
        self._linked_dict = pb.stats

        pb.df[name] = default
        self.default = default
        self._linked_dataframe = pb.df

        self.kind = kind

        # these are optional stat attributes
        self.abbreviation = None  # the abbreviation for this stat

    def __getitem__(self, player_index: int):
        return self._linked_dataframe.at[player_index, self.name]

    def calculate_initial(self, player_index):
        """Calculate the initial value for this based on its default value"""
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

    def weight(self, weight: "Weight", value: Union[float, int]):
        weight.add(self, value)

    def __str__(self):
        return self.name.title()

    def __repr__(self):
        return f"Stat({self.name}, {self.kind.name})"

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

#
# class Weight(Stat):
#     """a Weight is a special stat which is derived from a number of other stats using methods described in
#     util.descriptors. (this might move). """
#     def __init__(self, name: str, kind: Kinds = Kinds.weight):
#         super().__init__(name, kind)
#
#         self.stats = {}
#         self.extra_weight = 0
#         self._linked_dataframe = None
#
#     def add(self, stat: Stat, value: Union[float, int]):
#         """Add a stat to the total weight.
#         To add extra weight, access the attribute directly."""
#         self.stats[stat.name] = value
#
#     def initialize_functions(self, df: pd.DataFrame):
#         self._linked_dataframe = df
#
#     def calculate_initial(self, player_index):
#         return self.calculate_value(player_index)
#
#     def calculate_value(self, player_index):
#         weight = sum(self.stats.values()) + self.extra_weight
#         total = sum([self._linked_dataframe.at[player_index, stat.name] * self.stats[stat] for stat in self.stats])
#         return total / weight
#
#     def nice_string(self) -> str:
#         nice = self.name + ":"
#         for v, s in sorted(zip(self.stats.values(), self.stats.keys()), reverse=True):
#             nice += f" {s} {v}"
#         if self.extra_weight != 0:
#             nice += f" extra {self.extra_weight}"
#         return nice
#
#     def __str__(self):
#         return f"Weight {self.name.capitalize()}"
#
#
# class Rating(Calculatable):
#     def __init__(self, name: str, personality: Stat, category: Stat):
#         super().__init__(name, Kinds.rating)
#
#         self.personality = personality  # the personality stat that governs this stat (applies to ratings)
#         self.category = category  # the stat category this applies to
#         self.base_stat = Stat(('base_' + name), Kinds.base_rating)
#
#         setattr(all_stats, self.base_stat.name, self.base_stat)
#
#         self.formula = self.calculate_rating
#
#     def calculate_rating(self, player: 'Player'):
#         # TODO
#         return player.pb.df.at[player.cid, self.base_stat.name]
#
# #

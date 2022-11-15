"""
Contains database info and stats for a blaseball player and the playerbase.

Typical workflow:
maintain a single collection of players in the single PlayerBase. Player
info is pulled as Player instances. Player methods should update the
playerbase entries as-needed (and vice versa)
"""

import random
from collections.abc import Mapping
from typing import Union, List

import pandas as pd
# from numpy.random import normal
# from loguru import logger

from blaseball.stats import playerbase, statclasses, modifiers
from blaseball.stats import stats as s


class Player(Mapping):
    """
    A representation of a single player.

    This includes a link to a line in a PlayerBase, which uses a pandas
    dataframe to store the bulk of numeric ratings and stats. However, player is
    implemented as a separate class to support advanced functionality best not
    stored in a dataframe (like play logs, special ability functions, etc.)
    """

    player_class_id = 1000  # unique ID for each generation of a player,
    # used to verify uniqueness

    @staticmethod
    def new_cid() -> int:
        Player.player_class_id += 1
        return Player.player_class_id

    def __init__(self, pb: playerbase.PlayerBase, cid: int = None) -> None:
        self.pb = pb  # pointer to the playerbase containing this player's stats
        if cid is None:
            self.cid = Player.new_cid()  # players "Character ID", a unique identifier
            self.pb.new_player(self)
        else:
            # this player was already created as a row
            self.cid = cid

        self._stale_dict = statclasses.create_blank_stale_dict(True)
        self.modifiers = self.roll_traits()

        # you MUST call initialize after this.

    @staticmethod
    def roll_traits() -> List[modifiers.Modifier]:
        trait_list = []
        for i in range(0, random.randrange(3, 6)):
            trait_list += [modifiers.default_personality_deck.draw()]
        return trait_list

    def initialize(self):
        """Initialize/roll all stats for this player. This duplicates playerbase.initialize_all!"""
        for stat in self.pb.stats.values():
            self[stat] = stat.calculate_initial(self.cid)
        for kind in self._stale_dict:
            self._stale_dict[kind] = False

    def recalculate(self):
        for stat in s.pb.stats.values():
            if self._stale_dict[stat.kind]:
                if isinstance(stat.kind, statclasses.Rating):
                    self[stat] = self.calculate_rating(stat)
                else:
                    self[stat] = stat.calculate_value(self.cid)
        for kind in self._stale_dict:
            self._stale_dict[kind] = False

    def calculate_rating(self, rating: statclasses.Rating) -> float:
        """Calculate the value of a rating after modifiers"""
        base_value = rating.base_stat.calculate_value(self.cid)
        # this is really junk performance, but we can optimize when we know how frequent
        # cache misses are.
        modifier_value = sum([mod[rating] for mod in self.modifiers])
        return base_value + modifier_value

    # def randomize(self) -> None:
    #     """Generate random values for applicable stats.
    #     Call initialize() first.
    #     Counts as a new player."""
    #     self["name"] = Player.generate_name()
    #     self["number"] = self.generate_player_number()
    #
    #     for stat in all_stats['personality']:
    #         self[stat.name] = random.random()
    #
    #     self['clutch'] = random.random()
    #     handedness = random.choice([55, 55, 55, 45])
    #     while 0 < self['pull'] < 90:
    #         self['pull'] = normal(handedness, 10)
    #
    #     self["element"] = get_descriptor(self, 'element', extras=False)
    #
    #     for stat in all_stats['rating']:
    #         self[stat.name] = random.random() * max(min(self[stat.personality], 1), 0.5)
    #         # traits can result in personalities higher than 1. if this happens, it's cool, so
    #         # this bit makes sure you get that bonus
    #         if self[stat.personality] > 1:
    #             self[stat.name] += self[stat.personality] - 1
    #
    #     self.derive()
    #
    # def get_weight(self, weight: str) -> float:
    #     return all_stats.weights[weight].calculate_weighted(self)
    #
    # def write_descriptors(self) -> None:
    #     """Updates the descriptor fields for this player"""
    #
    #     self["overall descriptor"] = get_descriptor(self, 'overall', False)
    #     self["offense descriptor"] = get_descriptor(self, 'offense')
    #     if self["is pitcher"]:
    #         self["defense descriptor"] = get_descriptor(self, 'pitching')
    #     else:
    #         self["defense descriptor"] = get_descriptor(self, 'fielding')
    #     self['personality descriptor'] = get_descriptor(self, 'personality')
    #
    # def derive(self) -> None:
    #     for stat in ["batting", "baserunning", "defense", "pitching", "edge",
    #                  "vitality", "social", "total_offense", "total_off_field"]:
    #         self[stat] = all_stats.weights[stat].calculate_weighted(self)
    #
    #     self["is pitcher"] = self["pitching"] > self["defense"] * 1.1
    #
    #     if self["is pitcher"]:
    #         self['total defense'] = all_stats.weights['total_defense_pitching'].calculate_weighted(self)
    #     else:
    #         self['total defense'] = all_stats.weights['total_defense_fielding'].calculate_weighted(self)
    #
    #     self['total offense'] = all_stats.weights['total_offense'].calculate_weighted(self)
    #
    #     self.write_descriptors()
    #
    #     self["fingers"] += 1
    #
    # def set_all_stats(self, value):
    #     for stat in all_stats['personality'] + all_stats['rating']:
    #         self[stat.name] = value
    #     self['clutch'] = value
    #     self.traits = []
    #     self.derive()
    #
    # def reset_tracking(self):
    #     """Reset all tracking stats to 0"""
    #     for stat in all_stats['performance'] + all_stats['averaging']:
    #         self[stat.name] = 0
    #
    # def add_trait(self, trait: traits.Trait, derive=True) -> None:
    #     # TODO: stale out stats
    #     self.traits += [trait]
    #     for stat in trait:
    #         self[stat] += trait[stat]
    #     if derive:
    #         self.derive()
    #
    # def remove_trait(self, trait: traits.Trait) -> None:
    #     # TODO: stale out stats
    #     if trait not in self.traits:
    #         raise KeyError(f"Trait {trait} not on player {self}")
    #     else:
    #         for stat in trait:
    #             self[stat] -= trait[stat]
    #     self.traits.remove(trait)
    #     self.derive()

    def assign(self, values: Union[dict, pd.Series, 'Player']) -> None:
        """Update multiple stats from another plyaer, series, or dictionary"""
        if isinstance(values, Player):
            self.assign(values.stat_row())
            return
        elif isinstance(values, pd.Series):
            keys = values.index
        else:
            keys = values.keys()

        for key in keys:
            self[key] = values[key]

    def stat_row(self) -> pd.Series:
        return self.pb.df.loc[self.cid]

    def __getitem__(self, item: Union[statclasses.Stat, str]) -> Union[float, int, str]:
        if isinstance(item, statclasses.Stat):
            if self._stale_dict[item.kind]:
                # cached value is stale
                if isinstance(item, statclasses.Rating):
                    # if this is a rating, we have to check modifiers
                    return self.calculate_rating(item)
                else:
                    return item.calculate_value(self.cid)
            else:
                return self.pb.df.at[self.cid, item.name]
        elif item == 'cid':
            return self.cid
        elif isinstance(item, str):
            try:
                return s.pb.stats[item]
            except KeyError:
                raise KeyError(f"No results found via string lookup for {item}")
        else:
            raise KeyError(f"Invalid indexer provided to Player: {item} of type {type(item)}")

    def __setitem__(self, item: Union[statclasses.Stat, str], value) -> None:
        if isinstance(item, statclasses.Stat):
            self.pb.df.at[self.cid, item.name] = value
            for kind in statclasses.dependents[item.kind]:
                self._stale_dict[kind] = True
        else:
            self[self.pb.stats[item]] = value

    def __iter__(self) -> iter:
        return iter(self.stat_row())

    def __len__(self) -> int:
        return len(self.stat_row())

    def __eq__(self, other: Union['Player', pd.Series, dict,]) -> bool:
        if isinstance(other, Player):
            return self == other.stat_row()
        if isinstance(other, pd.Series):
            keys = other.index
        elif isinstance(other, dict):
            keys = other.keys()
        else:
            raise TypeError(f"Invalid type comparison: Player vs {type(other)} (other: {other})")

        for stat in keys:
            try:
                if self[stat] != other[stat]:
                    return False
            except (KeyError, TypeError):
                return False
        return True

    def __hash__(self):
        return self.cid

    # @staticmethod
    # def _to_stars(stat: float) -> str:
    #     """converts a 0 - 2 float number into a star string"""
    #     stars = int(stat * 5)
    #     half = (stat * 5) % 1 >= 0.5
    #     star_string = "*" * stars + ('-' if half else '')
    #     if len(star_string) > 5:
    #         star_string = star_string[0:5] + " " + star_string[5:]
    #     elif len(star_string) == 0:
    #         return "0"
    #     return star_string
    #
    # def total_stars(self) -> str:
    #     # """Return a string depiction of this player's stars"""
    #     return self._to_stars((self["total offense"] + self["total defense"]) / 2)
    #
    # def text_breakdown(self) -> str:
    #     text = (
    #         f"{self['name']} {self.total_stars()}\r\n"
    #         f"\r\n~ ~ ~ ~ ~ \r\n\r\n"
    #         f"{self['number']}: {self['name']}\r\n"
    #         f"{self.total_stars()} {self['overall descriptor']}\r\n"
    #         f"{self['offense position']}\r\n{self['defense position']}\r\n"
    #         f"RBI: ?? OPS: ???\r\nERA: --- WHIP: ---\r\n\r\n"
    #         f"Personality: {self['personality descriptor']}\r\n"
    #         f"Offense: {self._to_stars(self['total offense'])} {self['offense descriptor']}\r\n"
    #         f"Defense: {self._to_stars(self['total defense'])} {self['defense descriptor']}\r\n"
    #         f"Off-Field: {self._to_stars(self['total off-field'])}\r\n"
    #         f"Element: {self['element'].title()}\r\n"
    #         f"\r\n"
    #         f"Vibes: {self['vibes']}\r\n"
    #         f"\r\n~ ~ ~ ~ ~\r\n\r\n"
    #     )
    #     text += "Key Ratings\r\n\r\n"
    #     text += "\r\n".join(
    #         [f"{r.title()}: {self[r] * 100:.0f}%" for r in ["stamina", "mood", "soul"]])
    #     text += "\r\n\r\n"
    #     text += "\r\n".join(
    #         [f"{r.title()}: {self._to_stars(self[r])}" for r in [
    #             "batting", "baserunning", "defense", "pitching", "edge", "vitality", "social"
    #         ]]
    #     )
    #     text += "\r\n\r\n"
    #     text += "\r\n".join(
    #         [f"{r}: {self._to_stars(self[r.name])}" for r in all_stats['personality']]
    #     )
    #     text += "\r\n\r\n~ ~ ~ ~ ~\r\n\r\n"
    #     text += "Traits and Conditions\r\n\r\n"
    #     text += "\r\n".join([
    #         trait.nice_string() for trait in self.traits
    #     ])
    #     text += "\r\n\r\n~ ~ ~ ~ ~\r\n\r\n"
    #     text += "Deep Ratings\r\n"
    #
    #     for category in all_stats['category']:
    #         if 'total' in category.name:
    #             continue
    #         text += f"\r\n{category}:\r\n"
    #         for rating in all_stats['rating']:
    #             if rating.category == category.name:
    #                 text += f"{rating} {self._to_stars(self[rating.name])}\r\n"
    #
    #     return text

    def __str__(self) -> str:
        return(f"[{self.cid}] "
               f"'{self['name']}' ({self['team']}) "
               # f"{self.total_stars()}"
               )

    def __repr__(self) -> str:
        return (f"<{self.__module__}.{self.__class__.__name__} "
                f"[{self.cid}] "
                f"'{self['name']}' "
                f"(c{self.cid}) at {hex(id(self))}>")

#
#
# if __name__ == "__main__":
#     pb = PlayerBase(10)
#     print(pb)
#     print(pb[1001].text_breakdown())
#
#     for p in pb:
#         print(p)

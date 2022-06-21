"""
Contains database info and stats for a blaseball player and the playerbase.

Typical workflow:
maintain a single collection of players in the single PlayerBase. Player
info is pulled as Player instances. Player methods should update the
playerbase entries as-needed (and vice versa)
"""

import random
from collections.abc import Mapping, MutableMapping, Hashable
from typing import Union, List

import pandas as pd
from numpy import integer
from numpy.random import normal

from data import playerdata
from blaseball.stats.stats import all_stats, Stat
from blaseball.stats import traits
from blaseball.util.descriptors import get_descriptor


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
    def generate_name() -> str:
        """Creates a random name from the playerdata lists.
        Guaranteed to be great."""
        first_name = random.choice(playerdata.PLAYER_FIRST_NAMES)
        last_name = random.choice(playerdata.PLAYER_LAST_NAMES)
        return f"{first_name} {last_name}".title()

    @staticmethod
    def new_cid() -> int:
        Player.player_class_id += 1
        return Player.player_class_id

    def __init__(self) -> None:
        self._cid = Player.new_cid()  # players "Character ID", a unique identifier
        self.pb = None  # pointer to the playerbase containing this player's stats
        self.traits = []
        # you MUST call initialize after this.

    def initialize(self, playerbase: 'PlayerBase') -> None:
        """Create / reset all stats to default values.
        Counts as a new player"""
        self.pb = playerbase
        for stat in all_stats:
            self[stat.name] = stat.default
        self.traits = []

    def generate_player_number(self) -> int:
        """dumb fun function to create a player number based partially on CID"""
        unusual = random.random() < 0.10

        low_thresh = max(random.randrange(-20, 20, 2), (-20 if unusual else 0))
        high_thresh = random.randrange(45, random.randrange(50, (1000 if unusual else 100)))
        base = self._cid % 100

        if (base < high_thresh) and (base > low_thresh) and not unusual:
            return base
        else:
            ones = base % 10
            tens = int(((base % high_thresh) + low_thresh) / 10) * 10
            return ones + tens

    def randomize(self) -> None:
        """Generate random values for applicable stats.
        Call initialize() first.
        Counts as a new player."""
        self["name"] = Player.generate_name()
        self["number"] = self.generate_player_number()

        for stat in all_stats['personality']:
            self[stat.name] = random.random()

        self['clutch'] = random.random()
        handedness = random.choice([55, 55, 55, 45])
        while 0 < self['pull'] < 90:
            self['pull'] = normal(handedness, 10)

        self["element"] = get_descriptor(self, 'element', extras=False)

        for i in range(0, random.randrange(3, 6)):
            self.add_trait(traits.personality_traits.draw(), derive=False)

        for stat in all_stats['rating']:
            self[stat.name] = random.random() * max(min(self[stat.personality], 1), 0.5)
            # traits can result in personalities higher than 1. if this happens, it's cool, so
            # this bit makes sure you get that bonus
            if self[stat.personality] > 1:
                self[stat.name] += self[stat.personality] - 1

        self.derive()

    def get_weight(self, weight: str) -> float:
        return all_stats.weights[weight].calculate_weighted(self)

    def write_descriptors(self) -> None:
        """Updates the descriptor fields for this player"""

        self["overall descriptor"] = get_descriptor(self, 'overall', False)
        self["offense descriptor"] = get_descriptor(self, 'offense')
        if self["is pitcher"]:
            self["defense descriptor"] = get_descriptor(self, 'pitching')
        else:
            self["defense descriptor"] = get_descriptor(self, 'fielding')
        self['personality descriptor'] = get_descriptor(self, 'personality')

    def derive(self) -> None:
        for stat in ["batting", "baserunning", "defense", "pitching", "edge",
                     "vitality", "social", "total_offense", "total_off_field"]:
            self[stat] = all_stats.weights[stat].calculate_weighted(self)

        self["is pitcher"] = self["pitching"] > self["defense"] * 1.1

        if self["is pitcher"]:
            self['total defense'] = all_stats.weights['total_defense_pitching'].calculate_weighted(self)
        else:
            self['total defense'] = all_stats.weights['total_defense_fielding'].calculate_weighted(self)

        self['total offense'] = all_stats.weights['total_offense'].calculate_weighted(self)

        self.write_descriptors()

        self["fingers"] += 1

    def set_all_stats(self, value):
        for stat in all_stats['personality'] + all_stats['rating']:
            self[stat.name] = value
        self['clutch'] = value
        self.traits = []
        self.derive()

    def reset_tracking(self):
        for stat in all_stats['performance'] + all_stats['averaging']:
            self[stat.name] = 0

    def add_trait(self, trait: traits.Trait, derive=True) -> None:
        self.traits += [trait]
        for stat in trait:
            self[stat] += trait[stat]
        if derive:
            self.derive()

    def remove_trait(self, trait: traits.Trait) -> None:
        if trait not in self.traits:
            raise KeyError(f"Trait {trait} not on player {self}")
        else:
            for stat in trait:
                self[stat] -= trait[stat]
        self.traits.remove(trait)
        self.derive()

    def assign(self, values: Union[dict, pd.Series, 'Player']) -> None:
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
        if self.pb is None:
            raise RuntimeError(f"{self} not linked to a valid PlayerBase! Call player.initialize"
                               f"before using this player!")
        else:
            return self.pb.df.loc[self._cid]

    def df_index(self) -> int:
        """get the CID / dataframe index of this player."""
        if self.stat_row().name == self._cid:
            return self._cid
        else:
            raise RuntimeError(f"Warning! Playerbase Dataframe index {self.stat_row().name} "
                               f"does not match player CID {self._cid}, likely playerbase corruption.")

    def __getitem__(self, item) -> Union[float, str]:
        if item == 'cid':
            return self._cid
        elif isinstance(item, Stat):
            return self.stat_row()[item.name]
        else:
            return self.stat_row()[item]

    def __setitem__(self, item: Hashable, value: object) -> None:
        self.pb.df.loc[self._cid][item] = value

    def add_average(self, item: Union[List, str], value: Union[List, Union[int, float]]) -> None:
        """Updates a stat which is a running average, such as batting average. Pass one or more stats and values in
        and it'll update the linked counting stat and the averages."""
        if isinstance(item, list):
            count_stat = all_stats[item[0]].total_stat
        else:
            count_stat = all_stats[item].total_stat
            item = [item]
            value = [value]

        self[count_stat] += 1

        for i, v in zip(item, value):
            self[i] += (v - self[i]) / self[count_stat]

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
            raise TypeError("Invalid type comparison: Player vs {type(other)} (other: {other})")

        for stat in keys:
            try:
                if self[stat] != other[stat]:
                    return False
            except (KeyError, TypeError):
                return False
        return True

    @staticmethod
    def _to_stars(stat: float) -> str:
        """converts a 0 - 2 float number into a star string"""
        stars = int(stat * 5)
        half = (stat * 5) % 1 >= 0.5
        star_string = "*" * stars + ('-' if half else '')
        if len(star_string) > 5:
            star_string = star_string[0:5] + " " + star_string[5:]
        elif len(star_string) == 0:
            return "0"
        return star_string

    def total_stars(self) -> str:
        # """Return a string depiction of this player's stars"""
        return self._to_stars((self["total offense"] + self["total defense"]) / 2)

    def text_breakdown(self) -> str:
        text = (
            f"{self['name']} {self.total_stars()}\r\n"
            f"\r\n~ ~ ~ ~ ~ \r\n\r\n"
            f"{self['number']}: {self['name']}\r\n"
            f"{self.total_stars()} {self['overall descriptor']}\r\n"
            f"{self['offense position']}\r\n{self['defense position']}\r\n"
            f"RBI: ?? OPS: ???\r\nERA: --- WHIP: ---\r\n\r\n"
            f"Personality: {self['personality descriptor']}\r\n"
            f"Offense: {self._to_stars(self['total offense'])} {self['offense descriptor']}\r\n"
            f"Defense: {self._to_stars(self['total defense'])} {self['defense descriptor']}\r\n"
            f"Off-Field: {self._to_stars(self['total off-field'])}\r\n"
            f"Element: {self['element'].title()}\r\n"
            f"\r\n"
            f"Vibes: {self['vibes']}\r\n"
            f"\r\n~ ~ ~ ~ ~\r\n\r\n"
        )
        text += "Key Ratings\r\n\r\n"
        text += "\r\n".join(
            [f"{r.title()}: {self[r] * 100:.0f}%" for r in ["stamina", "mood", "soul"]])
        text += "\r\n\r\n"
        text += "\r\n".join(
            [f"{r.title()}: {self._to_stars(self[r])}" for r in [
                "batting", "baserunning", "defense", "pitching", "edge", "vitality", "social"
            ]]
        )
        text += "\r\n\r\n"
        text += "\r\n".join(
            [f"{r}: {self._to_stars(self[r.name])}" for r in all_stats['personality']]
        )
        text += "\r\n\r\n~ ~ ~ ~ ~\r\n\r\n"
        text += "Traits and Conditions\r\n\r\n"
        text += "\r\n".join([
            trait.nice_string() for trait in self.traits
        ])
        text += "\r\n\r\n~ ~ ~ ~ ~\r\n\r\n"
        text += "Deep Ratings\r\n"

        for category in all_stats['category']:
            if 'total' in category.name:
                continue
            text += f"\r\n{category}:\r\n"
            for rating in all_stats['rating']:
                if rating.category == category.name:
                    text += f"{rating} {self._to_stars(self[rating.name])}\r\n"

        return text

    def __str__(self) -> str:
        return(f"[{self._cid}] "
               f"'{self['name']}' ({self['team']}) "
               f"{self.total_stars()}"
               )

    def __repr__(self) -> str:
        return (f"<{self.__module__}.{self.__class__.__name__} "
                f"[{self._cid}] "
                f"'{self['name']}' "
                f"(c{self._cid}) at {hex(id(self))}>")


class PlayerBase(MutableMapping):
    """this class contains the whole set of players and contains operations
    to execute actions on batches of players

    It has two parts: a dataframe df, which contains the actual stats
        with players as rows and stats as columns,
    and players, a dict indext by CID which contains pointers to the Players objects.
    """
    def __init__(self, num_players: int = 0) -> None:
        self.df = pd.DataFrame(columns=[s.name for s in all_stats])
        self.players = {}

        if num_players > 0:
            self.new_players(num_players)

    def new_players(self, num_players: int) -> List[Player]:
        """batch create new players. Returns the new players as a list
        of Player"""

        finished_players = []
        for i in range(num_players):
            # create a set of new players:
            player = Player()
            self.df.loc[player._cid] = None  # noqa - this is the one time we're setting _cid
            player.initialize(self)
            player.randomize()

            self.players[player.df_index()] = player

            finished_players.append(player)
        return finished_players

    def verify_players(self) -> bool:
        """Because we have a dataframe with player stats, and a separate
        list of player objects that are linked, it's important to make sure
        these two data sources don't get out of sync with each other.

        This function performs a validation to make sure that each Player
        links to a valid dataframe row and each dataframe row has a valid
        Player.
        """
        try:
            for key in self.players.keys():
                if self.players[key]._cid != key:
                    raise RuntimeError(
                        f"Player CID and key mismatch:"
                        f"key {key}, "
                        f"player {self.players[key]}"
                    )
                if self[key] != self.players[key]:
                    raise RuntimeError(
                        f"Player verification failure! "
                        f"Player {key} mismatch: "
                        f"{self[key]} vs {self.players[key]}"
                    )
            for key in self.df.index:
                if self.players[key] != self.df.loc[key]:
                    raise RuntimeError(
                        f"Player verification failure! "
                        f"Dataframe row key {key} mismatch: "
                        f"{self.df.loc[key]['name']} "
                        f"vs {self.players[key]}"
                    )
        except KeyError as e:
            raise RuntimeError(f"KeyError during verification: {e}")
        return True

    def __len__(self) -> int:
        if len(self.players) != len(self.df.index):
            raise RuntimeError(
                f"Player/df mismatch!"
                f"{len(self.players)} players vs "
                f"{len(self.df.index)} dataframe rows."
            )
        return len(self.df.index)

    def __getitem__(self, key: Hashable) -> Union[Player, List[Player]]:
        """Get a player or range of players by name(s) or cid(s)"""
        if isinstance(key, str):
            item_row = self.df.loc[self.df['name'] == key.title()]
            if len(item_row) > 1:
                # you have duplicate names!
                pass
            item_row = item_row.iloc[0]
            return self.players[item_row.name]
        elif isinstance(key, (int, integer)):
            return self.players[key]
        elif isinstance(key, (range, list)):
            return [self[i] for i in key]
        else:
            raise KeyError(f"Could not index by type {type(key)}, expected CID int or name string.")

    def iloc(self, key: Union[int, slice, range]) -> Union[Player, List[Player]]:
        """
        You should not be able to do this. This is a mapping, so order doesn't matter.
        But dang it, sometimes you just need a player or a handful, and you don't care who you get.
        Don't expect this to be anything but a random selection!
        """
        all_cids = list(self.players.keys())

        if isinstance(key, int):
            return self[all_cids[key]]
        if isinstance(key, range):
            key = slice(key.start, key.stop, key.step)

        return_players = []
        for cid in all_cids[key]:
            return_players.append(self[cid])
        return return_players

    def __setitem__(self, key: Hashable, value: Union[Player, pd.Series]) -> None:
        """
        If the value player is in the playerbase, that player will be duplicated!
        Take care with this function!
        """
        self[key].assign(value)

    def __delitem__(self, key: Hashable) -> None:
        del self.players[key]
        self.df.drop(key)

    def __str__(self) -> str:
        return_str = f"PlayerBase {len(self)} players x "
        return_str += (f"{len(list(self.df.columns))} cols"
                      f"\r\n{list(self.df.columns)}")

        if len(self) <= 10:
            for player in self.iloc(range(len(self))):
                return_str += "\r\n" + str(player)
        else:
            for player in self.iloc(range(0, 5)):
                return_str += "\r\n" + str(player)
            return_str += "\r\n..."
            for player in self.iloc(range(len(self)-5, len(self))):
                return_str += "\r\n" + str(player)
        return return_str

    def __repr__(self) -> str:
        return(f"<{self.__module__}.{self.__class__.__name__} "
               f"[{len(self)} rows x "
               f"{len(self.df.columns)} cols] "
               f"at {hex(id(self))}>")

    def __iter__(self) -> iter:
        return iter(self.players.values())


if __name__ == "__main__":
    pb = PlayerBase(10)
    print(pb)
    print(pb[1001].text_breakdown())

    for p in pb:
        print(p)

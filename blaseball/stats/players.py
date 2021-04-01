"""
Contains database info and stats for a blaseball player and the playerbase.

Typical workflow:
maintain a single collection of players in the single PlayerBase. Player
info is pulled as Player instances. Player methods should update the
playerbase entries as-needed (and vice versa)
"""

import random
from collections import Hashable
from collections.abc import Mapping, MutableMapping
from typing import Union, List

import pandas as pd

from data import playerdata


class Player(Mapping):
    """
    A representation of a single player.

    This includes a link to a line in a PlayerBase, which uses a pandas
    dataframe to store the bulk of numeric statistics. However, player is
    implemented as a separate class to support advanced functionality best not
    stored in a dataframe (like play logs, special ability functions, etc.)
    """

    # default values
    CORE_STATS = {
        "name": "UNDEFINED PLAYER",
        "team": "N/A TEAM",
    }
    BASE_STATS = {
        "hitting": 0,  # base hitting ability
        "fielding": 0,  # base defense ability
        "pitching": 0,  # base pitching ability
        "charisma": 0, # base off-field ability
        "power": 0,
        # for pitchers: pitch speed/power,
        # for hitters: clean hit power
        # for defense: throw speed
        "technique": 0,
        # for pitchers: pitch accuracy
        # for batters: hit "direction" - reduce chance of fly out
        # for defence: chance of misplay
        "strategy": 0,
        # for pitchers: pitch choice
        # for batters: pitch prediction
        # for defense: chance of incorrect fielder's choice,
        "speed": 0,
        # for batters: fastball defense,
        # for runners: base speed,
        # for pitchers: stealing defense
        # for defenders: ground out chances
        "durability": 0,  # stat loss per game
    }
    BONUS_STATS = {
        "fingers": 9,
        "element": "Basic",
        "sleepy": 0,
        "vibes": 0,
        "dread": 0,
    }
    ALL_STATS_KEYS = list(CORE_STATS.keys()) + list(BASE_STATS.keys()) \
        + list(BONUS_STATS.keys())
    COMBINED_STATS = [CORE_STATS, BASE_STATS, BONUS_STATS]

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

    def __init__(self, df_row: pd.Series) -> None:
        self.stat_row = df_row  # pointer to the row of playerbase containing this player's stats
        self.cid = -1  # players "Character ID", a unique identifier
        self.initialize()

    def initialize(self) -> None:
        """Create / reset all stats to default values.
        Counts as a new player"""
        for statset in Player.COMBINED_STATS:
            for stat in list(statset.keys()):
                self.stat_row[stat] = statset[stat]
        self.cid = Player.new_cid()

    def randomize(self) -> None:
        """Generate random values for applicable stats.
        Call initialize() first.
        Counts as a new player."""
        self.stat_row["name"] = Player.generate_name()
        for stat in Player.BASE_STATS:
            self.stat_row[stat] = random.random()
        self.stat_row["fingers"] += 1
        self.stat_row["element"] = random.choice(playerdata.PLAYER_ELEMENTS)
        self.cid = Player.new_cid()

    def df_index(self) -> int:
        """get the CID / dataframe index of this player."""
        if self.stat_row.name == self.cid:
            return self.cid
        else:
            raise RuntimeError(f"Warning! Playerbase Dataframe index {self.stat_row.name}"
                               f"does not match player CID {self.cid}, likely playerbase corruption.")

    def __getitem__(self, item) -> object:
        return self.stat_row[item]

    def __setitem__(self, item: Hashable, value: object) -> None:
        self.stat_row[item] = value

    def __iter__(self) -> iter:
        return iter(self.stat_row)

    def __len__(self) -> int:
        return len(self.stat_row)

    def __eq__(self, other: Union['Player', pd.Series]) -> bool:
        if isinstance(other, Player):
            return self.df_index() == other.df_index() and self.cid == other.cid
        elif isinstance(other, pd.Series):
            for key in other.keys():
                if self[key] != other[key]:
                    return False
            return True
        else:
            return False

    def total_stars(self) -> str:
        """Return a string depiction of this player's stars"""
        average = (self.stat_row[Player.BASE_STATS].sum()
                   / len(Player.BASE_STATS)) * 5  # 0-5 star rating
        stars = int(average)
        half = average % 1 >= 0.5
        return "*"*stars + ('-' if half else '')

    def __str__(self) -> str:
        return(f"[{self.stat_row.name}] "
               f"'{self['name']}' ({self['team']}) "
               f"{self.total_stars()}"
               )

    def __repr__(self) -> str:
        return (f"<{self.__module__}.{self.__class__.__name__} "
                f"'{self['name']}' "
                f"id {self.stat_row.name} "
                f"(c{self.cid}) at {hex(id(self))}>")


class PlayerBase(MutableMapping):
    """this class contains the whole set of players and contains operations
    to execute actions on batches of players"""
    def __init__(self, num_players: int=0) -> None:
        self.df = pd.DataFrame(columns=Player.ALL_STATS_KEYS)
        self.players = {}

        if num_players > 0:
            self.new_players(num_players)

    def new_players(self, num_players: int) -> List[Player]:
        """batch create new players. Returns the new players as a list
        of Player"""

        # add new players as empty rows:
        old_len = len(self)
        self.df = self.df.reindex(self.df.index.tolist()
                                  + list(range(old_len, old_len+num_players)))
        new_players = self.df.iloc[old_len:old_len + num_players]

        # breathe life into them:
        finished_players = []
        for new_player in new_players.iterrows():
            player = Player(new_player[1])
            player.randomize()
            self.players[player.df_index()] = player
            finished_players.append(player)
        return finished_players

    def verify_players(self) -> bool:
        """Becasue we have a dataframe with player stats, and a separate
        list of player objects that are linked, it's important to make sure
        these two data sources don't get out of sync with each other.

        This function performs a validation to make sure that each Player
        links to a valid dataframe row and each dataframe row has a valid
        Player.
        """
        for key in self.players.keys():
            if self[key] != self.players[key]:
                raise RuntimeError(f"Player verification failure! "
                                   f"Player {key} mismatch:"
                                   f"{self[key]} vs {self.players[key]}")
        for row in self.df.iterrows():
            if self.players[row[1].name] != row[1]:
                raise RuntimeError(f"Player verification failure! "
                                   f"Dataframe row {row[0]} mismatch:"
                                   f"{repr(row[1])} vs {self.players[row[1].name]}")
        return True

    def __len__(self) -> int:
        if len(self.players) != len(self.df.index):
            raise RuntimeError(f"Player/df mismatch!"
                               f"{len(self.players)} players vs "
                               f"{len(self.df.index)} dataframe rows.")
        return len(self.df.index)

    def __getitem__(self, item: Hashable) -> Union[Player, List[Player]]:
        if isinstance(item, str):
            name_index = self.df['name'].index[
                self.df['name'].tolist().index(item)]
            return self.players[self.df.index[name_index]]
        elif isinstance(item, int):
            return self.players[item]
        elif isinstance(item, slice):
            start = 0 if item.start is None else item.start
            stop = len(self) if item.stop is None else item.stop
            step = 1 if item.step is None else item.step
            return self[range(start, stop, step)]
        elif isinstance(item, (range, list)):
            return [self[i] for i in item]
        else:
            return self.df.iloc[item]

    def __setitem__(self, item: Hashable, value: Union[Player, Series]) -> None:
        item_index = self[item].df_index()
        if isinstance(value, Player):
            self.players[item_index] = value
            self.df.loc[item_index] = value.stat_row.copy()
            self.players[item_index].stat_row = self.df.loc[item_index]
            self.players[item_index].cid = value.cid
        elif isinstance(value, pd.Series):
            self.df.loc[item_index] = value
            self.players[item_index] = Player(self.df.loc[item_index])
        self.verify_players()

    def __delitem__(self, item: Hashable) -> None:
        del self.players[item]
        self.df.drop(item)
        self.verify_players()

    def __str__(self) -> str:
        return_str = f"PlayerBase {len(self)} players x "
        return_str += (f"{len(list(self.df.columns))} cols"
                      f"\r\n{list(self.df.columns)}")
        if len(self) <= 10:
            for i in range(0, len(self)):
                return_str += "\r\n" + self[i].__str__()
        else:
            for i in range(0, 5):
                return_str += "\r\n" + self[i].__str__()
            return_str += "\r\n..."
            for i in range(len(self)-5, len(self)):
                return_str += "\r\n" + self[i].__str__()
        return return_str

    def __repr__(self) -> str:
        return(f"<{self.__module__}.{self.__class__.__name__} "
               f"[{len(self)} rows x "
               f"{len(self.df.columns)} cols] "
               f"at {hex(id(self))}")

    def __iter__(self) -> iter:
        return iter(self.players.values())


if __name__ == "__main__":
    pb = PlayerBase(10)
    print(pb)
    p = Player()


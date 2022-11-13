"""
Playerbase contains all the statisitical information for all players in the game.

At its core, it's a pandas DataFrame with a number of utility function wrappers.
The indexes are player CIDs.

"""
from collections.abc import MutableMapping, Hashable

import pandas as pd
from numpy import integer
from loguru import logger

from typing import TYPE_CHECKING, Union, List, Tuple
if TYPE_CHECKING:
    from blaseball.stats.players import Player
    from blaseball.stats.statclasses import Stat, Kinds


class PlayerBase(MutableMapping):
    """this class contains the whole set of players and contains operations
    to execute actions on batches of players

    It has two parts: a dataframe df, which contains the actual stats
        with players as rows and stats as columns,
    and players, a dict indext by CID which contains pointers to the Players objects.
    """
    def __init__(self) -> None:
        self.df = pd.DataFrame()
        self.stats = {}  # dict of Stats
        self._default_stat_list = []
        self.players = {}  # dict of Players

        logger.debug("Initialized new playerbase.")

    def new_player(self, player: 'Player'):
        self.players[player.cid] = player
        self.df.loc[player.cid] = self._default_stat_list

    def __len__(self) -> int:
        if len(self.players) != len(self.df.index):
            raise RuntimeError(
                f"Player/df mismatch! "
                f"{len(self.players)} players vs "
                f"{len(self.df.index)} dataframe rows."
            )
        if len(self.stats) != len(self.df.columns):
            raise RuntimeError(
                f"stats/df mismatch! "
                f"{len(self.stats)} stats vs "
                f"{len(self.df.columns)} dataframe columns."
            )
        return len(self.df.index)

    def __getitem__(self, key: Hashable) -> Union['Player', List['Player']]:
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

    def iloc(self, key: Union[int, slice, range]) -> Union['Player', List['Player']]:
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

    def __setitem__(self, key: Hashable, value: Union['Player', pd.Series]) -> None:
        """
        If the value player is in the playerbase, that player will be duplicated!
        Take care with this function!
        """
        # self[key].assign(value
        raise NotImplementedError("MERP")

    def __delitem__(self, key: Hashable) -> None:
        del self.players[key]
        self.df.drop(key)

    def __str__(self) -> str:
        return_str = f"PlayerBase {len(self)} players x "
        return_str += f"{len(self.df.columns)} stats"

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
        return(f"PlayerBase: "
               f"[{len(self)} rows x "
               f"{len(self.df.columns)} cols] "
               f"at {hex(id(self))}>")

    def __iter__(self) -> iter:
        return iter(self.players.values())

    def add_stat(self, stat: 'Stat'):
        """This adds a stat to the playerbase. This is called by the Stat's init method!!"""
        self.stats[stat.name] = stat
        self.df[stat.name] = stat.default
        self._default_stat_list += [stat.default]

    # stat indexing functions
    def get_stats_with_kind(self, kind: 'Kinds') -> List['Stat']:
        stats = [x for x in self.stats.values() if x.kind == kind]
        if len(stats) == 0:
            raise KeyError(f"Could not locate any stats with kind {kind}!")
        return stats

    def get_stats_with_personality(self, personality: 'Stat') -> List['Stat']:
        stats = [x for x in self.stats.values() if x.personality == personality]
        if len(stats) == 0:
            raise KeyError(f"Could not locate any stats with personality {personality}!")
        return stats

    def get_stats_with_category(self, category: 'Stat') -> List['Stat']:
        stats = [x for x in self.stats.values() if x.category == category]
        if len(stats) == 0:
            raise KeyError(f"Could not locate any stats with category {category}!")
        return stats

    def get_stats_by_name(self, identifier: str) -> List['Stat']:
        if identifier in self.stats:
            return [self.stats[identifier]]

        stats = [x for x in self.stats.values() if x.abbreviation == identifier]
        if len(stats) == 0:
            stats = [self.stats[x] for x in self.stats if identifier in x]
            if len(stats) == 0:
                raise KeyError(f"Could not locate any stats with identifier {identifier}!")
        return stats
    #
    # def get_stats(self, item: Union['Stat', 'Kinds', str]) -> Union['Stat', List['Stat']]:
    #     """Get stats that match a criteria.
    #     Do not use this in core loops, index by dot directly."""
    #     if isinstance(item, Stat):
    #         if item.kind is Kinds.personality:
    #             return self.get_stats_with_personality(item)
    #         elif item.kind is Kinds.category:
    #             return self.get_stats_with_category(item)
    #     elif isinstance(item, Kinds):
    #         return self.get_stats_with_kind(item)
    #     elif isinstance(item, str):
    #         if item in self.stats:
    #             return self.stats[item]
    #         else:
    #             return self.get_stats_by_name_partial(item)
    #     else:
    #         raise KeyError(f"Invalid key! Key '{item}' with type {type(item)}")
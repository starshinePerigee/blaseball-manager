"""
Playerbase contains all the statisitical information for all players in the game.

At its core, it's a pandas DataFrame with a number of utility function wrappers.
The indexes are player CIDs.

"""
from collections.abc import MutableMapping, Hashable

import pandas as pd
from numpy import integer
from loguru import logger

from typing import TYPE_CHECKING, Union, List, Dict
if TYPE_CHECKING:
    from blaseball.stats import statclasses, players


class PlayerBase(MutableMapping):
    """this class contains the whole set of players and contains operations
    to execute actions on batches of players

    It has two parts: a dataframe df, which contains the actual stats
        with players as rows and stats as columns,
    and players, a dict indext by CID which contains pointers to the Players objects.
    """
    def __init__(
            self,
            recalculation_order: List['statclasses.Kinds'],
            base_dependencies: Dict['statclasses.Kinds', List['statclasses.Kinds']]
    ) -> None:
        self.df = pd.DataFrame()
        self.stats = {}  # dict of Stats
        self._default_stat_list = []
        self.players = {}  # dict of Players

        self.recalculation_order = recalculation_order

        self._base_dependencies = base_dependencies
        self.dependencies = {}
        # fill in everything that's not a dependent
        for kind in self.recalculation_order:
            if kind not in base_dependencies:
                self.dependencies[kind] = []
            else:
                self.dependencies[kind] = base_dependencies[kind]

        self.dependents = {kind: [] for kind in self.recalculation_order}
        for kind in self.recalculation_order:
            for dependency in self.dependencies[kind]:
                self.dependents[dependency] += [kind]

        logger.debug("Initialized new playerbase.")

    def create_blank_stale_dict(self, state=True):
        """Creates a fresh blank stale dictionary. If state is True, this dict starts entirely stale.
        Otherwise, it starts fresh."""
        stale_dict = {kind: False for kind in self.recalculation_order}
        if state:
            for kind in self._base_dependencies.keys():
                stale_dict[kind] = True
        return stale_dict

    def new_player(self, player: 'players.Player'):
        self.players[player.cid] = player
        self.df.loc[player.cid] = self._default_stat_list

    def clear_players(self):
        self.players = {}
        self.df = self.df.drop(self.df.index)

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

    def __getitem__(self, key: Hashable) -> Union['players.Player', List['players.Player']]:
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

    def iloc(self, key: Union[int, slice, range]) -> Union['players.Player', List['players.Player']]:
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

    def __setitem__(self, key: Hashable, value: Union['players.Player', pd.Series]) -> None:
        """
        If the value player is in the playerbase, that player will be duplicated!
        Take care with this function!
        """
        # self[key].assign(value
        raise NotImplementedError("MERP")

    def __delitem__(self, key: Union[int, 'players.Player']) -> None:
        try:
            del self[key.cid]
        except AttributeError:
            del self.players[key]
            self.df.drop(key, inplace=True)

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

    def recalculate_all(self):
        for kind in self.recalculation_order:
            try:
                for stat in self.get_stats_with_kind(kind):
                    self.df[stat] = [stat.calculate_value(cid) for cid in self.df.index]
            except KeyError:
                # TODO: once we don't have any dummy kinds, we can remove this.
                pass
        for player in self.players.values():
            player._stale_dict = self.create_blank_stale_dict(False)

    def add_stat(self, stat: 'statclasses.Stat'):
        """This adds a stat to the playerbase. This is called by the Stat's init method!!"""
        if stat.kind not in self.recalculation_order:
            raise RuntimeError(f"Invalid stat kind! {stat.kind} not in {self.recalculation_order}!")
        self.stats[stat.name] = stat
        self.df[stat.name] = stat.default
        self._default_stat_list += [stat.default]

    def remove_stat(self, stat: 'statclasses.Stat'):
        del self.stats[stat.name]
        column_pos = list(self.df.columns).index(stat.name)
        self.df.drop(columns=[stat.name], inplace=True)
        self._default_stat_list.pop(column_pos)

    # stat indexing functions
    def get_stats_with_kind(self, kind: 'statclasses.Kinds') -> List['statclasses.Stat']:
        stats = [x for x in self.stats.values() if x.kind == kind]
        if len(stats) == 0:
            raise KeyError(f"Could not locate any stats with kind {kind}!")
        return stats

    def get_stats_with_personality(self, personality: 'statclasses.Stat') -> List['statclasses.Stat']:
        # this lazily evaluates so we should only call x.personality if it has it:
        ratings = [x for x in self.stats.values() if hasattr(x, 'personality') and x.personality == personality]
        if len(ratings) == 0:
            raise KeyError(f"Could not locate any stats with personality {personality}!")
        return ratings

    def get_stats_with_category(self, category: 'statclasses.Stat') -> List['statclasses.Stat']:
        stats = [x for x in self.stats.values() if hasattr(x, 'category') and x.category == category]
        if len(stats) == 0:
            raise KeyError(f"Could not locate any stats with category {category}!")
        return stats

    def get_stats_by_name(self, identifier: str) -> List['statclasses.Stat']:
        if identifier in self.stats:
            return [self.stats[identifier]]

        stats = [x for x in self.stats.values() if x.abbreviation == identifier]
        if len(stats) == 0:
            stats = [self.stats[x] for x in self.stats if identifier in x]
            if len(stats) == 0:
                raise KeyError(f"Could not locate any stats with identifier {identifier}!")
        return stats

    def verify(self) -> None:
        """Checks the stat and player indicies and throws an error if discrepancies are found."""
        try:
            # check self.players
            for player_cid in self.players.keys():
                # make sure all players are listed in the right index:
                if self.players[player_cid].cid != player_cid:
                    raise RuntimeError(f"Player CID and key mismatch: key {player_cid}, "
                                       f"player {self.players[player_cid]}")
                # make sure player is in the dataframe:
                if player_cid not in self.df.index:
                    raise RuntimeError(f"Player {player_cid} not listed in df index!")
            # check df index
            for index_cid in self.df.index:
                if index_cid not in self.players.keys():
                    raise RuntimeError(f"Player index {index_cid} not in player listing!")
            # check self.stats
            for stat_name in self.stats.keys():
                if self.stats[stat_name].name != stat_name:
                    raise RuntimeError(f"Stat key and name mismatch!"
                                       f"key {stat_name}, stat {self.stats[stat_name]}")
                if stat_name not in self.df.columns:
                    raise RuntimeError(f"Stat {stat_name} not in df columns!")
            for column_name in self.df.columns:
                if column_name not in self.stats:
                    raise RuntimeError(f"Column {stat_name} not in stats listing!")
        except KeyError as e:
            raise RuntimeError(f"KeyError during verification: {e}")

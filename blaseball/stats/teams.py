"""
Contains info for handling team actions and team statistics.
"""

from collections.abc import MutableSequence, Sequence
from typing import Union

from blaseball.settings import Settings
from blaseball.stats.players import Player, PlayerBase


class Team(MutableSequence):  # should probably be a mutablemapping
    """
    Represents a single team, with team stats and team methods.
    """
    def __init__(self, name: str, starting_players: [Player] = None) -> None:
        self.name = name
        self.players = starting_players
        for player in self.players:
            player["team"] = name

    def __len__(self) -> int:
        return len(self.players)

    def get_player_index(self, key: Union[Player, str, int, slice]) -> Union[int, slice]:
        if isinstance(key, (int, slice)):
            return key  # assume we already have a key, this is kind of a hack tu support get/set later
        elif isinstance(key, Player):
            for i, player in enumerate(self.players):
                if player.cid == key.cid:
                    return i
        elif isinstance(key, str):
            key_case = key.title()
            for i, player in enumerate(self.players):
                if player["name"] == key_case:
                    return i
        else:
            raise IndexError(f"Invalid index type: {type(key)}, expected Player, str, int, or slice")
        raise KeyError(f"Could not locate {key} on team {self}!")

    def __getitem__(self, key: Union[str, int, slice, Player]) -> Player:
        return self.players[self.get_player_index(key)]

    def __setitem__(self, key: Union[str, int, slice, Player], value: Player) -> None:
        self.players[self.get_player_index(key)] = value

    def __delitem__(self, key: Union[str, int, slice, Player]):
        self.players.remove(self.get_player_index(key))

    def insert(self, index: int, player: Player) -> None:
        self.players.insert(index, player)

    def __str__(self):
        return f"{self.name} ({len(self)})"

    def __repr__(self):
        return (f"<{self.__module__}.{self.__class__.__name__} "
                f"'{self.name}' "
                f"at {hex(id(self))}>")


class League(Sequence):
    """
    This contains links to every team and contains functions for whole-league
    manipulations.
    """
    def __init__(self, playerbase: PlayerBase, team_names: [str] = None) -> None:
        self.teams = []
        for team_name in team_names:
            self.teams.append(Team(
                team_name,
                playerbase.new_players(Settings.players_per_team))
            )

    def __len__(self) -> int:
        return len(self.teams)

    def __getitem__(self, key: Union[str, int, slice]) -> Team:
        if isinstance(key, str):
            key_l = key.lower()
            for team in self.teams:
                if team.name.lower() == key_l:
                    return team
            raise KeyError(f"Could not find team {key} in {self}")
        else:
            return self.teams[key]

    def __str__(self) -> str:
        return f"THE LEAGUE ({len(self)})"

    def __repr__(self) -> str:
        return (f"<{self.__module__}.{self.__class__.__name__} "
                f"'THE LEAGUE' ({len(self)})"
                f"at {hex(id(self))}>")

    # def __iter__(self):
    #     return iter(self.teams)


if __name__ == "__main__":
    from blaseball.stats import players
    from data import teamdata
    pb = players.PlayerBase()
    l = League(pb, teamdata.TEAMS_99)
    print(l)
    for p in pb:
        print(p)

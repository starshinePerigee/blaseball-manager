"""
Contains info for handling team actions and team statistics.
"""

from collections.abc import Collection, Sequence
from typing import Union

from blaseball.settings import Settings
from blaseball.stats import players, statclasses, playerbase
from blaseball.stats import stats as s


class Team(Collection):  # should probably be a mutablemapping
    """
    Represents a single team, with team stats and team methods.
    """
    def __init__(self, name: str, starting_players: [players.Player] = None) -> None:
        self.name = name
        if starting_players is None:
            self.players = []
        else:
            self.players = starting_players
        for player in self.players:
            player[s.team] = name

    def __len__(self) -> int:
        return len(self.players)

    def __iter__(self) -> iter:
        return iter(self.players)

    def __contains__(self, item) -> bool:
        return item in self.players

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
    def __init__(self, pb: playerbase.PlayerBase, team_names: [str] = None) -> None:
        self.teams = []
        for team_name in team_names:
            team_comp = []
            for __ in range(Settings.players_per_team):
                new_player = players.Player(pb)
                new_player.initialize()
                team_comp += [new_player]
            self.teams += [Team(team_name, team_comp)]
        pb.recalculate_all()

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
    from blaseball.stats import stats as s
    from data import teamdata
    l = League(s.pb, teamdata.TEAMS_99)
    print(l)
    for p in s.pb:
        print(p)

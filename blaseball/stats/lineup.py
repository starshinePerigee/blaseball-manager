"""
This function manages a single lineup - ie, a team configuration that is going to go play
a game of blaseball.
"""

from collections.abc import Collection
from typing import Union, List
from random import shuffle
import re

from blaseball.settings import Settings
from blaseball.stats import players, teams
from blaseball.util.geometry import Coords


class Defense:
    """
    An arrangement of players for a team on defense, including the catcher but excluding the pitcher.

    Defense is meant to help organize positions and fielding. At its core, it's lists of (player, coord) pairs
    that describe where a player is on the field. Some positions have extra utility as well.
    """
    def __init__(self):
        self.catcher = None  # catcher communicates with the pitcher
        self.shortstop = None  # shortstop is a fielder who hangs out in the infield
        self.basepeeps = []  # each basepeep can man a base
        self.fielders = []  # fielders can only catch the ball
        self.extras = []  # extras do nothing

    def all_players(self) -> List[players.Player]:
        """List all players as a list in sensible order."""
        return [self.catcher] + [self.shortstop] + self.basepeeps + self.fielders + self.extras

    def to_flat_dict(self, cids=True):
        """Convert the defense (a collection of lists) into a single level dictionary."""
        if cids:
            reference = 'cid'
        else:
            reference = 'name'

        def_dict = {}  # noqa
        def_dict[self.catcher[reference]] = "catcher"
        def_dict[self.shortstop[reference]] = "shortstop"
        for i, player in enumerate(self.basepeeps):
            def_dict[player[reference]] = f"basepeep {i}"
        for i, player in enumerate(self.fielders):
            def_dict[player[reference]] = f"fielder {i}"
        for i, player in enumerate(self.extras):
            def_dict[player[reference]] = "extra"
        return def_dict

    def find(self, key: Union[str, int, players.Player]) -> str:
        """Get the player in a defense """
        if isinstance(key, players.Player):
            key = key.cid
        if isinstance(key, int):  # also catches players - do not convert to elif
            return self.to_flat_dict()[key]
        elif isinstance(key, str):
            return self.to_flat_dict(False)[key.title()]
        raise KeyError(f"Unsupported type: {type(key)}")

    def __getitem__(self, key: str) -> Union[players.Player, List[players.Player]]:
        # if key == "catcher":
        #     return self.catcher
        # elif key == "shortstop":
        #     return self.shortstop
        # elif
        # hacky:
        return vars(self)[key]

    def __len__(self) -> int:
        return len(self.all_players())


class Lineup(Collection):
    running_number = 0

    @staticmethod
    def new_num() -> int:
        Lineup.running_number += 1
        return Lineup.running_number

    def __init__(self, name: str = None) -> None:
        if name is None:
            self.name = "new lineup " + str(Lineup.new_num())
        else:
            self.name = name

        self.batting_order = []
        self.pitcher = None
        self.defense = Defense()

    def get_all_players(self) -> [players.Player]:
        all_players = [self.pitcher]
        all_players += self.batting_order
        return all_players

    def generate(self, team: teams.Team, fuzz: float = 0, in_order: bool = False):
        """
        Creates a new lineup, trying to be as optimal as possible. Fuzz is added to the stats
        randomly to increase randomess - higher fuzz means base stats matter less.
        """
        available_players = team.players.copy()
        if not in_order:
            shuffle(available_players)
        self.pitcher = available_players[0]
        self.batting_order = available_players[1:Settings.min_lineup+1]
        batters = self.batting_order.copy()
        if not in_order:
            shuffle(batters)
        for i, batter in enumerate(batters):
            if i == 0:
                self.defense.catcher = batter
            elif i == 1:
                self.defense.shortstop = batter
            elif i <= Settings.base_count + 1:
                self.defense.basepeeps.append(batter)
            elif i <= Settings.base_count*2 + 1:
                self.defense.fielders.append(batter)
            else:
                self.defense.extras.append(batter)

    def validate(self) -> (bool, str):
        """
        Make sure a lineup is still valid:
        - lineup has a pitcher
        - all lineup players have positions
        - all positions are in lineup
        - there's a basepeep for every base
        - lineup has at least min_players players
        - all players are on the same team
        - all players are in playing condition (TBD)
        """
        return False, "Not yet implimented"

    def string_summary(self):
        to_print = ""
        to_print += f"Pitcher: {self.pitcher['name']} {self.pitcher.total_stars()}\r\n"
        to_print += "Batting order:"
        for i, player in enumerate(self.batting_order):
            to_print+=f"\r\n\t[{i+1}] {player['name']} {player.total_stars()}   " \
                      f"{self.defense.find(player).title()}"
        return to_print

    def __len__(self) -> int:
        return len(self.get_all_players())

    def __contains__(self, item) -> bool:
        return item in self.get_all_players()

    def __iter__(self) -> iter:
        return iter(self.get_all_players())

    def __str__(self) -> str:
        return f"Lineup '{self.name}' " \
               f"with pitcher {self.pitcher} " \
               f"and lead-off hitter {self.batting_order[0]}"

    def __repr__(self) -> str:
        return f"Lineup '{self.name}' at {hex(id(self))}"

    def __getitem__(self, key: str) -> Union[players.Player, List[players.Player]]:
        key_l = key.lower()
        if key_l == "pitcher":
            return self.pitcher
        elif key_l == "batters" or key_l == "batting_order":
            return self.batting_order
        else:
            return self.defense[key]


if __name__ == "__main__":
    from blaseball.stats import players, teams
    from data import teamdata
    pb = players.PlayerBase()
    l = teams.League(pb, teamdata.TEAMS_99[0:1])

    lu = Lineup("main lineup")
    lu.generate(l[0])
    print(str(lu))
    print(repr(lu))
    print(lu.string_summary())
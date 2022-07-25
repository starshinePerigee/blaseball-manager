"""
This function manages a single lineup - ie, a team configuration that is going to go play
a game of blaseball.
"""

from blaseball.settings import Settings
from blaseball.stats.players import Player
from blaseball.stats.teams import Team
from blaseball.stats.stadium import Stadium
from blaseball.util.geometry import Coord

from collections.abc import Collection, MutableMapping
from typing import Union, List, Tuple
from math import atan, radians
from random import shuffle


def place_basepeep(instance, base_count) -> Coord:
    basepeep_angle = abs((90 * instance / (base_count - 1)) - 5)
    basepeep_distance_factor = max(atan(radians(basepeep_angle)), atan(radians(90 - basepeep_angle)))
    return Coord(Stadium.BASEPATH_LENGTH / basepeep_distance_factor, basepeep_angle, True)


FIELDER_DISTANCE = 290


def place_fielder(instance, fielder_count) -> Coord:
    fielder_angles = 90 * (instance + 1) / (fielder_count + 1)
    return Coord(FIELDER_DISTANCE, fielder_angles, True)


LOCATIONS = {
    'catcher': Coord(0, 0),
    'shortstop': Coord(140, 60, True),
    'pitcher': Coord(60.5, 45, True)
}

for i in range(0, Stadium.NUMBER_OF_BASES):
    LOCATIONS[f'basepeep {i + 1}'] = place_basepeep(i, Stadium.NUMBER_OF_BASES)

NUMBER_OF_FIELDERS = 3

for i in range(0, NUMBER_OF_FIELDERS):
    LOCATIONS[f'fielder {i + 1}'] = place_fielder(i, NUMBER_OF_FIELDERS)

for i in range(0, 3):
    LOCATIONS[f'extra {i + 1}'] = None


class Position:
    """Represents a single position on the field."""
    def __init__(self, position: str, player: Player, location: Coord = None):
        self.position = position
        self.player = player
        if location is not None:
            self.location = location
        else:
            self.location = LOCATIONS[position]
        if " " in position:
            self.group = position.split(" ")[0]
        else:
            self.group = None
        
    def __repr__(self):
        return f"<Position {self.position}: {self.player} at {self.location}>"

    def __str__(self):
        return f"{self.position}: {self.player['name']}"


class Defense(MutableMapping):
    """
    An arrangement of players for a team on defense, including the catcher but excluding the pitcher.

    Defense is meant to help organize positions and fielding. Defense is trying to answer the following questions:
    "Who is at what position?"
    "Who has position-based duties, such as pitching?"
    "Where is every player? Who is the closest to x location?"
    "Who is the shortstop?"

    There's a lot of optimization here if we're making a TON of calls to this, because these lookups are all
    iterative except for the position one, but we could in the future pre-generate and manage mulitple lookup dicts.
    """

    def __init__(self):
        self.positions = {}
        self.groups = {}  # a defense group is a set of positions that represent a group

    def add(self, position: str, player: Player, location: Coord = None):
        new_position = Position(position, player, location)
        self.positions[position] = new_position
        if new_position.group:
            if new_position.group in self.groups:
                self.groups[new_position.group] += [new_position]
            else:
                self.groups[new_position.group] = [new_position]

    def all_positions(self) -> List[Position]:
        """List all players as a list in sensible order."""
        return [self['catcher']] + [self['shortstop']] + self['basepeep'] + self['fielder'] + self['extra']

    def all_players(self) -> List[Player]:
        return [__.player for __ in self.all_positions()]

    def rank_closest(self, coord: Coord) -> List[Tuple[Position, float]]:
        closest = [(self[position], coord.distance(self[position].location))
                   for position in self
                   if self[position].location is not None]
        closest.sort(key=lambda x: x[1])
        return closest

    def closest(self, coord: Coord) -> Tuple[Position, float]:
        return self.rank_closest(coord)[0]

    def find(self, player: Union[str, Player]) -> Position:
        """Finds a player's position based on that player's player object, CID, or name."""
        if isinstance(player, Player):
            player = player['name']
        for position in self.positions:
            if self.positions[position].player['name'] == player or self.positions[position].player.cid == player:
                return self.positions[position]
        raise KeyError(f"Player {player} not found in defense with length {len(self)}")

    def __getitem__(self, key: Union[str, Player]) -> Union[Position, List[Position]]:
        """Key can be the following items:
        a position string
        a group string
        a player object, a player CID, or a player Name
        """
        if key in self.positions:
            return self.positions[key]
        elif key in self.groups:
            return self.groups[key]
        else:
            return self.find(key)

    def __setitem__(self, key: str, value: Position) -> None:
        if key not in self.positions:
            raise KeyError(f"Could not locate key {key} in positions dictionary!")
        self.positions[key] = value

    def __delitem__(self, key: str) -> None:
        if key not in self.positions:
            raise KeyError(f"Could not locate key {key} in positions dictionary!")
        del(self.positions[key])

    def __iter__(self):
        return iter(self.positions)

    def __len__(self) -> int:
        return len(self.positions)


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

    def get_all_players(self) -> [Player]:
        all_players = [self.pitcher]
        all_players += self.batting_order
        return all_players

    def generate(self, team: Team, fuzz: float = 0, in_order: bool = False):
        """
        Creates a new lineup, trying to be as optimal as possible. Fuzz is added to the stats
        randomly to increase randomess - higher fuzz means base stats matter less.
        """
        available_players = team.players.copy()
        if not in_order:
            shuffle(available_players)
        self.pitcher = available_players[0]
        self.defense.add("pitcher", self.pitcher)
        self.batting_order = available_players[1:Settings.min_lineup+1]
        batters = self.batting_order.copy()
        if not in_order:
            shuffle(batters)
        for i, batter in enumerate(batters):
            if i == 0:
                self.defense.add("catcher", batter)
            elif i == 1:
                self.defense.add("shortstop", batter)
            elif i <= Stadium.NUMBER_OF_BASES + 1:  # 3 + 1 = 4; 2 - 4
                self.defense.add(f"basepeep {i - 1}", batter)
            elif i <= Stadium.NUMBER_OF_BASES*2 + 1:  # 3 * 2 + 1 = 7, 5 - 7
                self.defense.add(f"fielder {i - (Stadium.NUMBER_OF_BASES + 1)}", batter)
            else:
                self.defense.add(f"extra {i - (Stadium.NUMBER_OF_BASES*2 + 1)}", batter)

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
        return True, "Not yet implimented"

    def string_summary(self):
        to_print = ""
        to_print += f"Pitcher: {self.pitcher['name']} {self.pitcher.total_stars()}\r\n"
        to_print += "Batting order:"
        for i, player in enumerate(self.batting_order):
            to_print += f"\r\n\t[{i+1}] {player['name']} {player.total_stars()}   " \
                        f"{self.defense.find(player).position}"
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

    def __getitem__(self, key: str) -> Union[Player, List[Player]]:
        key_l = key.lower()
        if key_l == "pitcher":
            return self.pitcher
        elif key_l == "team":
            return self.pitcher['team']
        elif key_l == "batters" or key_l == "batting_order":
            return self.batting_order
        elif 'batter ' in key_l:
            batter = int(key_l.split(' ')[1]) - 1  # zero indexed
            return self.batting_order[batter]
        else:
            return self.defense[key].player


if __name__ == "__main__":
    from blaseball.util import quickteams
    l = quickteams.league

    lu = Lineup("main lineup")
    lu.generate(l[0])
    print(str(lu))
    print(repr(lu))
    print(lu.string_summary())

    print(lu.defense['basepeep 2'])
    print("")

    for pos in lu.defense.all_positions():
        print(f"{pos.position}: {pos.location}")

    print("")

    print(lu.defense.closest(Coord(300, 170)))
    for pos in lu.defense.rank_closest(Coord(90, 90)):
        print(f"{pos[1]:.0f}: {pos[0]}")

    print("x")

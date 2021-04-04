"""
This takes two teams with lineups and makes them play ball against each other!

what happens in a ball game?

inner loop:
pitcher throws a pitch with speed, accuracy, and difficulty
batter decides to swing or not
if swing:
    either they hit or they miss
    if they hit:
        if it's a foul, play resets - nothing happens
        otherwise, it's a live ball
if not:
    if in strike zone, it's a strike looking
    if outside strike zone, it's a ball

if it's a live ball:
    baserunners advance
    fielders attempt to throw them out

    how does this work?
        1. determine power and angle of hit
        2. determine if fielder catches it (fly out)
        if fly out:
            runner is out
            basepeeps tag home
            chance for stealing (advance / score on the sacrifice)
        if ground:
            determine catch time
            set baserunner positions
            fielder decides throw location
            makes throw:
                calc time (with error)
                advance runners, see if safe
                if runners reach base, they can decide if they want to continue

during idle play:
    stealing attempts
    pitch

"""

from collections.abc import MutableSequence
from typing import Hashable, Union, List

from blaseball.stats import lineup
from blaseball.settings import Settings


class BallGame:
    """
    This is a single game of blaseball.

    The goal is to generate a BallGameSummary
    """
    def __init__(self, home: lineup.Lineup, away: lineup.Lineup, print_events: bool=False) -> None:
        self.home_team = home
        self.away_team = away

        self.teams = [home, away]

        self.inning = 1
        # away always bats first!
        self.inning_half = 1  # index of the at_bat_number and scores, COUNTS DOWN
        self.outs = 0
        self.strikes = 0
        self.balls = 0

        self.at_bat_numbers = [0, 0]  # home, away
        self.scores = [0.0, 0.0]  # home, away

        self.bases = [None] * Settings.base_count

        self.summary = BallGameSummary(print_events)
        self.complete = False

    def offense_i(self) -> int:
        return self.inning_half

    def defense_i(self) -> int:
        return self.inning_half + 1 % 2

    def batter_out(self) -> None:
        self.outs += 1
        self.balls = 0
        self.at_bat_numbers[self.offense_i()] += 1
        if self.outs > 2:
            self.outs = 0
            self.strikes = 0
            self.inning_half -= 1
            if self.inning_half < 0:
                self.inning_half = 1
                self.inning += 1
                if self.inning > 9 and max(self.scores) != min(self.scores):
                    self.complete = True
                    self.summary += f"Game over! Final score: " \
                                    f"{self.teams[0]['pitcher']['team']} {self.scores[0]}, " \
                                    f"{self.teams[1]['pitcher']['team']} {self.scores[1]}."
                    return
            else:
                if self.inning_half == 0:
                    half_str = "bottom"
                else:
                    half_str = "top"
                self.summary += f"{half_str.title()} of inning {self.inning}, " \
                                f"{self.teams[self.defense_i()]['pitcher']['name']} of the " \
                                f"{self.teams[self.defense_i()]['pitcher']['team']} pitching."

    def next(self) -> None:
        if self.complete:
            return

        current_pitcher = self.teams[self.defense_i()]["pitcher"]
        current_batter = self.teams[self.offense_i()]["batting_order"][self.at_bat_numbers[self.offense_i()]]
        if current_batter["hitting"] >= current_pitcher["pitching"]:
            # it's a good hit
            self.scores[self.offense_i()] += 1
            self.at_bat_numbers[self.offense_i()] += 1
            self.summary += f"{current_batter['name']} scores! score is {self.scores[0]}-{self.scores[1]}"
        else:
            # strikeout
            self.summary += f"{current_batter['name']} is struck out by {current_pitcher['name']}! " \
                            f"{self.outs+1} outs."
            self.batter_out()


class BallGameSummary(MutableSequence):
    """
    This is the summary of a ball game.

    While BallGame is meant to simulate a game, this class is meant to record it.
    BallGame is transient, this is stored and saved.
    """
    def __init__(self, print_events: bool = True) -> None:
        self.s = []
        self.print_events = print_events

    def __iadd__(self, other:str) -> None:
        if self.print_events:
            print(other)
        self.s.append(other)

    def __len__(self) -> int:
        return len(self.s)

    def __getitem__(self, key: Union[int, slice]) -> Union[str, List[str]]:
        return self.s[key]

    def __setitem__(self, key: Union[int, slice], value: Union[str, List[str]]) -> None:
        self.s[key] = value

    def __delitem__(self, key: Union[int, slice]) -> None:
        if isinstance(key, int):
            self.s.remove(key)
        else:
            for i in key:
                self.s.remove(i)

    def insert(self, index: int, item: Union[str, List[str]]) -> None:
        self.s.insert(index, item)


if __name__ == "__main__":
    from random import shuffle
    from time import sleep
    from blaseball.stats import players, teams, lineup
    from data import teamdata
    pb = players.PlayerBase()
    team_names = teamdata.TEAMS_99
    shuffle(team_names)

    league = teams.League(pb, team_names[0:2])

    l1 = lineup.Lineup("Home Lineup")
    l1.generate(league[0])

    l2 = lineup.Lineup("Away Lineup")
    l2.generate(league[1])

    print(league[0])
    print(l1.string_summary())
    print("\r\n\t\t* * * VS * * *\r\n")
    print(league[1])
    print(l2.string_summary())

    sleep(1)

    g = BallGame(l1, l2, True)
    while not g.complete:
        g.next()


"""This module contains two classes responsible for managing games as they are played:

BallGame, which manages a single game of Blaseball.
AllGames, which creates and manages multiple BallGames.
"""


from random import random
from decimal import Decimal

from blaseball.playball.event import Update
from blaseball.playball.basepaths import Basepaths
from blaseball.stats.players import Player
from blaseball.stats.lineup import Lineup
from blaseball.stats.stadium import Stadium


class BallGame:
    """The manager for a game of blaseball."""


    def increment_batting_order(self):
        self.at_bat_count += 1
        at_bat_length = len(self.teams[self.offense_i()]['batting_order'])
        self.at_bat_numbers[self.offense_i()] = (self.at_bat_numbers[self.offense_i()] + 1) % at_bat_length
        if self.at_bat_count > 255:
            self.summary += f"Time Out! {self.teams[self.offense_i()]['pitcher']['team']} cashes out the perfect inning!"
            self.scores[self.offense_i()] += Decimal('0.1')
            self.next_inning()

    def next_inning(self) -> None:
        self.outs = 0
        self.strikes = 0
        self.at_bat_count = 0
        self.inning_half -= 1
        if self.inning_half < 0:
            self.inning_half = 1
            self.inning += 1
            game_over = self.inning > 9 and max(self.scores) != min(self.scores)
            if game_over or self.inning > 255:
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

    def batter_out(self) -> None:
        self.outs += 1
        self.balls = 0
        self.increment_batting_order()
        if self.outs > 2:
            self.next_inning()

    def add_strike(self) -> Update:
        return Update("0-1")

    def add_ball(self) -> Update:
        return Update("1-0")

    def add_foul(self) -> Update:
        return Update("0-1")

    def add_runs(self, runs: int) -> Update:
        return Update(f"{self.home_team.name} {runs}, {self.away_team} 0")

    def home_run(self) -> Update:
        return self.add_runs(len(self.bases))  # TODO

    def add_out(self) -> Update:
        return Update()

    def next(self) -> None:
        if self.complete:
            return

        current_pitcher = self.teams[self.defense_i()]["pitcher"]
        current_batter = self.teams[self.offense_i()]["batting_order"][self.at_bat_numbers[self.offense_i()]]
        if current_batter["hitting"] >= current_pitcher["pitching"] + random():
            # it's a good hit
            self.scores[self.offense_i()] += 1
            self.summary += f"{current_batter['name']} scores! score is {self.scores[0]}-{self.scores[1]}"
            self.increment_batting_order()
        else:
            # strike
            self.strikes += 1
            if self.strikes < 3:
                self.summary += f"Strike, swinging. {self.strikes}-0."
            else:
                self.summary += f"{current_batter['name']} is struck out by {current_pitcher['name']}! " \
                                f"{self.outs+1} {'outs' if self.outs+1 > 1 else 'out'}."
                self.batter_out()
#
#
# class BallGameSummary(MutableSequence):
#     """
#     This is the summary of a ball game.
#
#     While BallGame is meant to simulate a game, this class is meant to record it.
#     BallGame is transient, this is stored and saved.
#     """
#     def __init__(self, print_events: bool = True) -> None:
#         self.s = []
#         self.print_events = print_events
#
#     def __iadd__(self, other: str) -> 'BallGameSummary':
#         if self.print_events:
#             print(other)
#         self.s.append(other)
#         return self
#
#     def __len__(self) -> int:
#         return len(self.s)
#
#     def __getitem__(self, key: Union[int, slice]) -> Union[str, List[str]]:
#         return self.s[key]
#
#     def __setitem__(self, key: Union[int, slice], value: Union[str, List[str]]) -> None:
#         self.s[key] = value
#
#     def __delitem__(self, key: Union[int, slice]) -> None:
#         if isinstance(key, int):
#             self.s.remove(key)
#         else:
#             for i in key:
#                 self.s.remove(i)
#
#     def insert(self, index: int, item: Union[str, List[str]]) -> None:
#         self.s.insert(index, item)

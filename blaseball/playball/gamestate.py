"""
This is a data class (but not a dataclass) that represents a single moment in blaseball. It use used as a frequent messenge / input
to the various ballgame listeners.

"""

from dataclasses import dataclass
from decimal import Decimal

from blaseball.stats.players import Player
from blaseball.stats.lineup import Lineup
from blaseball.stats.stadium import Stadium

from typing import List


@dataclass
class GameRules:
    """This tracks game constants"""
    ball_count: int = 4
    strike_count: int = 3
    outs_count: int = 3
    innings: int = 9


class GameState:
    """
    This is a single moment of baseball.

    The goal is to generate a BallGameSummary. this gets created and shuffled a lot, so there's a lot of optimization
    that we're leaving on the table - this is due to its origin as the game manager, in addition to the game state.
    """

    def __init__(self, home: Lineup, away: Lineup, stadium: Stadium, rules: GameRules) -> None:
        """Init will only get called once at the start of the game. BallGame maintains its own instance,
        and sends out copies as the game progresses."""
        self.rules = rules
        self.stadium = stadium

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
        self.scores = [Decimal('0.0')] * 2  # home, away

        self.bases = {i: None for i in range(0, stadium.NUMBER_OF_BASES + 1)}

    def offense_i(self) -> int:
        """Returns the index of the offense for this class' sequence structures"""
        return self.inning_half

    def offense(self) -> Lineup:
        """Get the offense lineup"""
        return self.teams[self.offense_i()]

    def batter(self, next_in_order=0) -> Player:
        at_bat_number = self.at_bat_numbers[self.offense_i()]
        at_bat_number += next_in_order
        at_bat_number = at_bat_number % len(self.offense().batting_order)
        return self.offense()['batting_order'][at_bat_number]

    def defense_i(self) -> int:
        """Returns the index of the defense for this class' sequence structures"""
        return (self.inning_half + 1) % 2

    def defense(self) -> Lineup:
        return self.teams[self.defense_i()]

    def boolean_base_list(self) -> List[bool]:
        return [self.bases[i] for i in range(1, self.stadium.NUMBER_OF_BASES + 1)]

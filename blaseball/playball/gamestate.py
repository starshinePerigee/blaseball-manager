"""
This is a data class (but not a dataclass) that represents a single moment in blaseball. It use used as a frequent messenge / input
to the various ballgame listeners.

"""

from dataclasses import dataclass
from enum import Enum
from decimal import Decimal
from collections.abc import Collection

from blaseball.stats.players import Player
from blaseball.stats.lineup import Lineup
from blaseball.stats.stadium import Stadium

from typing import List, Union


@dataclass
class GameRules:
    """This tracks game constants"""
    ball_count: int = 4
    strike_count: int = 3
    outs_count: int = 3
    innings: int = 9


class BaseSummary(Collection):
    """A simple class meant to transmit / update bases without throwing BasePaths around.
    It's basically a constant-length list
    index 0 is home plate"""
    def __init__(self, total_bases=None, basepaths=None):

        if basepaths is not None:
            self.number_of_bases = basepaths.number_of_bases
            self.bases = [runner.player if runner is not None else None for runner in basepaths.to_base_list()]
        elif total_bases is not None:
            self.number_of_bases = total_bases
            self.bases = [None] * (total_bases + 1)
        else:
            raise RuntimeError("Must initialize BaseSummary with either base count or Basepaths!")

    def __len__(self):
        return sum([1 for base in self.bases if base is not None])

    def __contains__(self, key):
        return key in self.bases

    def __iter__(self):
        for base in self.bases:
            yield base

    def __getitem__(self, key: Union[int, slice]):
        return self.bases[key]

    def __delitem__(self, key: Union[int, slice]):
        if isinstance(key, int):
            self.bases[key] = None
        else:
            for i in range(key.start, key.stop, key.step):
                self.bases[i] = None

    def __setitem__(self, key: int, value: Player):
        self.bases[key] = value  # noqa - not sure what this is on about.


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

        self.at_bat_count = 0

        self.bases = BaseSummary(total_bases=stadium.NUMBER_OF_BASES)

    def offense_i(self) -> int:
        """Returns the index of the offense for this class' sequence structures"""
        return self.inning_half

    def offense(self) -> Lineup:
        """Get the offense lineup"""
        return self.teams[self.offense_i()]

    def batter(self, next_in_order=0) -> Player:
        """Returns the player who is at-bat (if next_in_order is 0) or is n positions away from being at bat"""
        at_bat_number = self.at_bat_numbers[self.offense_i()]
        at_bat_number += next_in_order
        at_bat_number = at_bat_number % len(self.offense().batting_order)
        return self.offense()['batting_order'][at_bat_number]

    def increment_batting_order(self, increment=1) -> bool:
        """Increment the batting order, return True if it rolled over"""
        at_bat_length = len(self.teams[self.offense_i()]['batting_order'])
        new_bat_number = self.at_bat_numbers[self.offense_i()] + increment
        if new_bat_number >= at_bat_length:
            self.at_bat_numbers[self.offense_i()] = new_bat_number % at_bat_length
            return True
        else:
            self.at_bat_numbers[self.offense_i()] = new_bat_number
            return False

    def defense_i(self) -> int:
        """Returns the index of the defense for this class' sequence structures"""
        return (self.inning_half + 1) % 2

    def defense(self) -> Lineup:
        return self.teams[self.defense_i()]

    def boolean_base_list(self) -> List[bool]:
        return [self.bases[i] is not None for i in range(1, self.stadium.NUMBER_OF_BASES + 1)]

    def half_str(self):
        if self.inning_half:
            return "top"
        else:
            return "bottom"

    def count_string(self):
        return f"{self.balls} - {self.strikes}"

    def score_string(self):
        score_h = self.scores[0]
        if score_h % 1 == 0:
            score_h = f"{score_h:.0f}"
        score_a = self.scores[1]
        if score_a % 1 == 0:
            score_a = f"{score_a:.0f}"
        team_h = self.home_team['team']
        team_a = self.away_team['team']
        return f"{team_h}: {score_h} - {team_a}: {score_a}"


class GameTags(Enum):
    state_ticks = 'state ticks <GameState>'
    new_batter = 'new player up to bat <Player>'
    new_inning = 'new inning reached <int>'
    new_half = 'new inning half reached <int>'
    game_over = 'game is complete <Update>'
    game_start = 'first message of a new game. <Update>'

    game_updates = 'game updates <Update>'
    pitch = 'pitch was thrown <Pitch>'
    swing = 'swing was swung <Swing>'
    hit_ball = 'ball is hit <HitBall>'
    bases_update = 'basepath update <BaseSummary>'
    player_walked = 'player walked to first <Player>'
    home_run = 'home run was hit <int>'
    cycle_batting_order = 'every batter hit <Lineup>'
    runs_scored = 'runs were scored <int/Decimal>'
    strike = 'strike was thrown <bool: strike swinging?>'
    ball = 'ball was thrown <None>'
    foul = 'foul was hit <None>'
    outs = 'players out for any cause <int>'

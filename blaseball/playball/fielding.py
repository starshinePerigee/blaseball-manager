"""
This handles fielding, with the end goal of creating an event
which captures everything that has happened.
"""

from blaseball.playball.runner import Runner, Basepaths
from blaseball.playball.ballgame import BallGame
from blaseball.playball.liveball import LiveBall
from blaseball.playball.event import Update
from blaseball.stats.players import Player
from blaseball.stats.lineup import Defense
from blaseball.util.geometry import Coord

from numpy.random import normal, rand
from typing import List


ERROR_TIME_STDV = 3
ERROR_TIME_MEDIAN = 2


def roll_error_time(factor: float) -> float:
    time = -1
    while time < 0:
        time = normal(ERROR_TIME_MEDIAN * factor, ERROR_TIME_STDV)
    return time


THROW_ERROR_MEAN = -3
THROW_ERROR_STDV = 2  # throwing standard deviation
THROW_ERROR_THROW_FACTOR = -0.3


def roll_throw_difficulty(throwing: float) -> float:
    return normal(THROW_ERROR_MEAN, THROW_ERROR_STDV + THROW_ERROR_THROW_FACTOR * throwing)


THROW_SPEED_BASE = 0.01  # worst case throwing speed in seconds/foot
THROW_SPEED_FACTOR = 0.0025  # how much faster a throw is for 1 throwing, in seconds/foot
SECONDS_PER_MPH = (60 * 60) / 5280


def throw_duration_base(throwing: float, distance: float) -> float:
    """calculates the time of a throw assuming no errors."""
    inv_throw_speed = THROW_SPEED_BASE - (THROW_SPEED_FACTOR * throwing)
    return distance * inv_throw_speed


class Throw(Update):
    """A single throw from one player to another."""
    def __init__(self,
                 start_player: Player,
                 start_location: Coord,
                 end_player: Player,
                 end_location: Coord
                 ):
        self.distance = start_location.distance(end_location)
        self.difficulty = roll_throw_difficulty(start_player['throwing'])
        error_magnitude = self.difficulty - end_player['grabbiness']
        self.error = error_magnitude < 0
        if self.error:
            self.error_time = roll_error_time(error_magnitude)
        else:
            self.error_time = 0
        self.duration = throw_duration_base(start_player['throwing'], self.distance) + self.error_time

        super().__init__(self.description_string(start_player, end_player))

    def description_string(self, start_player: Player, end_player: Player):
        if self.error:
            if self.error_time > 4:
                descriptor = "misses it horribly!"
            elif self.error_time > 2:
                descriptor = "misses it!"
            else:
                descriptor = "just misses it!"
            text = f", but {end_player['name'].split(' ')[0]} {descriptor}"
        else:
            text = ""
        return f"{start_player['name']} throws to {end_player['name']}{text}"

    def __str__(self):
        return f"{self.distance:.0f}' throw with difficulty {self.difficulty:.2f} and net time {self.duration:.2f}s"


REACH_MINIMUM = 0  # how close a ball must land to someone with 0 reach to not take a penalty
REACH_MAXIMUM = 60  # how close a ball must land to someone with 1 reach to not take a penalty
REACH_SLOPE_MINIMUM = 40  # how much further past


def reach_difficulty(distance, reach) -> float:
    # reach sets the no-penalty grabbiness range:
    reach_maximum = reach * REACH_MAXIMUM
    grab_distance = max(reach_maximum - distance, 0)
    return grab_distance / (REACH_SLOPE_MINIMUM + reach_maximum)
    # TODO: probably should manage ground speed also somewhere, grounders are neglected throughout basically


GRABBINESS_CATCHING_FACTOR = 10


def roll_to_catch(difficulty, grabbiness) -> bool:
    # TODO: this is a hack and weird with grab:
    grab_modifier = (grabbiness - 1) * GRABBINESS_CATCHING_FACTOR
    total_difficulty = min(difficulty + grab_modifier, 0.98)
    return rand() < total_difficulty


class Catch(Update):
    """A player's attempt to catch a LiveBall"""
    def __init__(self, ball: LiveBall, defense: Defense):
        super().__init__()

        self.fielder_position, self.distance = defense.closest(ball.ground_location())
        self.difficulty = reach_difficulty(self.distance, self.fielder_position.player['reach'])
        self.caught = roll_to_catch(self.difficulty, self.fielder_position.player['grabbiness'])
        self.duration = ball.flight_time()
        if self.caught:
            self.text = f"{self.fielder_position.player['name']} caught it for a fly out."
        else:
            self.duration += roll_error_time(self.difficulty)

    def __str__(self):
        return f"Catch with difficulty {self.difficulty} and duration {self.duration}"


DECISION_FUZZ_STDV = 1
PROBABILITY_WINDOW = 1  # how much time you need to be 100% confident of a throw


def prioritize_runner(runner: Runner, fielder: Player, start_position: Coord, base_coords: List[Coord]) -> float:
    """Determines a weight for a runner"""
    # base weight (pun intended):
    next_base = runner.next_base()

    # modify by odds of throw
    duration = throw_duration_base(fielder['throwing'], start_position.distance(base_coords[next_base]))

    time_fuzz = normal(0, DECISION_FUZZ_STDV * (2 - fielder['awareness']))
    runner_time = runner.time_to_base() + time_fuzz

    # if runner time >>> duration, this evaluates to 0. if duration >>> runner time, this evaluate to 1.
    # if 0 < delta < PROBABILITY_WINDOW this evalutes to somewhere between 0 and 1 continuously
    net_time = (duration - runner_time) * PROBABILITY_WINDOW
    odds = max(0.0, min(1.0, net_time))
    return odds


def fielders_choice(fielder: Player, location: Coord, active_runners: List[Runner], base_coords: List[Coord]) -> int:
    """Decide which base to throw to based on the list of runners"""
    runners = [(prioritize_runner(runner, fielder, location, base_coords), runner) for runner in active_runners]
    runners.sort(key = lambda x: x[0])
    return runners[0][1].next_base()


class ThrownOut(Update):
    pass


class Rundown(Update):
    pass



class FieldBall:
    """
    This is EARLYFIELDING: as simple as possible so we can build a game and then a UI, since tuning fielding needs UI
    work.

    This does not currently take into account:
    - multiple fielders
    - ball bouncing
    - z axis catchability
    - errors as new balls

    this will spit out a series of Updates, a new base list, and a bunch of game updates.
    """
    def __init__(self, game: BallGame, bases: Basepaths, live: LiveBall):
        self.live = live
        self.bases = bases
        pitcher = game.defense().defense['pitcher']
        catcher = game.defense().defense['catcher']
        batter = game.batter()
        base_coords = game.stadium.BASES

        self.updates = []

        self.catch = Catch(self.live, pitcher)
        self.updates += [self.catch]

        self.outs = 0

        if self.catch and live.catchable:
            self.updates += [game.add_out()]
            self.bases.tag_up_all()
        else:
            self.bases += batter
            runs = self.bases.advance_all(self.catch.duration)
            if runs > 0:
                self.updates += [game.add_runs(runs)]
            while self.bases:
                pass


if __name__ == "__main__":
    from blaseball.stats import players, teams, stats
    from blaseball.stats.lineup import Lineup
    from blaseball.stats.stadium import Stadium, ANGELS_STADIUM
    from data import teamdata

    pb = players.PlayerBase()
    team_names = teamdata.TEAMS_99
    league = teams.League(pb, team_names[5:7])
    print('setup complete..\r\n')

    l1 = Lineup("Home Lineup")
    l1.generate(league[0])
    l2 = Lineup("Away Lineup")
    l2.generate(league[1])
    s = Stadium(ANGELS_STADIUM)

    g = BallGame(l1, l2, s, False)

    t = Throw(
        g.defense().defense['pitcher'].player,
        g.defense().defense['pitcher'].location,
        g.defense().defense['basepeep 1'].player,
        g.defense().defense['basepeep 1'].location,
    )

    print(t)
    print(t.text)
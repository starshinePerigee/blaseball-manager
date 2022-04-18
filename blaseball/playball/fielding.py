"""
This handles fielding, with the end goal of creating an event
which captures everything that has happened.
"""


from blaseball.playball.ballgame import BallGame
from blaseball.playball.liveball import LiveBall
from blaseball.playball.event import Update
from blaseball.stats.players import Player
from blaseball.stats.lineup import Defense
from blaseball.util.geometry import Coord

from numpy.random import normal, rand


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


class Throw(Update):
    """A single throw from one player to another."""
    def __init__(self,
                 start_player: Player,
                 start_location: Coord,
                 end_player: Player,
                 end_location: Coord
                 ):
        inv_throw_speed = THROW_SPEED_BASE - (THROW_SPEED_FACTOR * start_player['throwing'])
        self.distance = start_location.distance(end_location)
        self.difficulty = roll_throw_difficulty(start_player['throwing'])
        error_magnitude = self.difficulty - end_player['grabbiness']
        self.error = error_magnitude < 0
        if self.error:
            self.error_time = roll_error_time(error_magnitude)
        else:
            self.error_time = 0
        self.duration = self.distance * inv_throw_speed + self.error_time

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

    this will spit out a series of Updates.
    """
    def __init__(self, game: BallGame, live: LiveBall):
        self.live = live

        self.updates = []

        self.catch = Catch(self.live, game.defense().defense)
        self.updates += [self.catch]

        if self.catch:
            game.batter_out()
        


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
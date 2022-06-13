"""
This handles fielding, for a very specific narrow definition of "fielding" - this handles the
actual mechanics of a player catching and throwing a ball. The actual motion - and coordination with
BasePaths - happens in inplay.py.
"""

from blaseball.playball.liveball import LiveBall
from blaseball.playball.event import Update
from blaseball.stats.players import Player

from numpy.random import normal, rand

# TODO: add stats, probably once we do the big stats overhaul

# ref https://baseballsavant.mlb.com/statcast_catch_probability


REACH_MINIMUM_DISTANCE = 10  # how close a ball must land to someone with 0 reach to not take a penalty
REACH_MAXIMUM_DISTANCE = 60  # how close a ball must land to someone with 1 reach to not take a penalty


def calc_reach_odds(distance, reach) -> float:
    """Distance x reach give base odds for catching a ball.
    This ranges from 1 (within the REACH MINIMUM DISTANCE) to 0 (at the edge of reach * reach_maximum_distance"""
    max_distance = REACH_MAXIMUM_DISTANCE * reach
    net_distance = max_distance - distance
    odds = net_distance / (max_distance - REACH_MINIMUM_DISTANCE)
    return max(min(odds, 1), 0)
    # TODO: probably should manage ground speed also somewhere, grounders are neglected throughout basically


MIN_GRABBINESS_ODDS = 0.95  # chance of a fielding error at 0 grab
MAX_GRABBINESS_ODDS = 1  # chance of a fielding error at 2 grab
GRABBINESS_MIDPOINT = (MAX_GRABBINESS_ODDS-MIN_GRABBINESS_ODDS) / 2


def calc_grabbiness_odds(grabbiness) -> float:
    return MIN_GRABBINESS_ODDS + GRABBINESS_MIDPOINT * grabbiness


def roll_to_catch(odds) -> bool:
    """This function mostly exists for testing purposes, to be mocked later."""
    return rand() <= odds


ERROR_TIME_STDV_INITIAL = 5.0
ERROR_TIME_AVERAGE_MINIMUM = 1  # average error time for a 100% odds throw
ERROR_TIME_AVERAGE_MAXIMUM = 6  # average error time for a 0% odds throw
# needed for the math, because we re-add error time average minimum at the end:
ERROR_TIME_FACTOR = ERROR_TIME_AVERAGE_MAXIMUM - ERROR_TIME_AVERAGE_MINIMUM
ERROR_TIME_EXPONENT = 0.5  # how fast error time accumulates as you move from 100% down.


def roll_error_time(odds: float) -> float:
    """Calculate the time added by an error for throwing or catching.
    the worse the odds, the wider the throw/catch and thus the worse the penalty"""
    # TODO: this function defs needs to get revisited to use better factors

    error_time_median = (1 - odds) ** ERROR_TIME_EXPONENT * ERROR_TIME_FACTOR + ERROR_TIME_AVERAGE_MINIMUM

    # ugly hack:
    # note that because we drop negative values, you can only get the average so low because the stdv
    # this is a fun method but I haven't run the odds on this
    working_stdv = min(ERROR_TIME_STDV_INITIAL, ERROR_TIME_STDV_INITIAL * 2 * (1-odds) + 1)

    for __ in range(0, 20):
        time = normal(error_time_median, working_stdv)
        if time > 0:
            return time
        working_stdv *= 0.7
    return 0


class Catch(Update):
    """A player's attempt to catch a LiveBall"""
    def __init__(self, ball: LiveBall, fielder: Player, distance: float):
        super().__init__()

        self.reach_odds = calc_reach_odds(distance, fielder['reach'])
        self.grab_odds = calc_grabbiness_odds(fielder['grabbiness'])
        self.total_odds = self.reach_odds * self.grab_odds

        self.duration = ball.flight_time()
        self.player_name = fielder['name']

        if roll_to_catch(self.total_odds):
            if ball.catchable:
                self.text = f"{self.player_name} caught it for a fly out."
                self.caught = True
            else:
                self.caught = False
        else:
            self.caught = False
            self.duration += roll_error_time(self.total_odds)

    def __str__(self):
        return f"Catch by {self.player_name} with odds {self.total_odds:.2f} and duration {self.duration:.2f}"

    def __repr__(self):
        return f"<Catch by {self.player_name} duration {self.duration:.2f}>"


# Throwing:

# TODO: we've junked a ton of previous work for throwing as part of getting rid of "difficulty".
# we might want to restore difficulty to both this and catching, but right now we're
# maintaining parity with the logic for Catch.
# check previous commits from before June if you're going to work through this.

THROW_BONUS_SLOPE = 0.1  # how much to scale bonus throwing above 1.
MAX_THROW_ODDS_BONUS = 1.05  # maximum value for throw odds; keep in mind throw odds are multiplied with the
# reciever's grabbiness odds.
# for a grabbiness of 0 (grab odds of 0.95), throw odds of 1.05 are needed to result in a 100% throw chance.
STDV_AT_200_FT = 0.10  # throw odd standard deviation for a long but not crazy long throw
STDV_PER_FOOT = STDV_AT_200_FT / 200
AVERAGE_PER_1_THROW = 0.1  # how much to shift the average per 1 throwing, very sensitive as stdv is low.


def roll_throw_odds_modifier(throwing: float, distance: float) -> float:
    distance_stdv = STDV_PER_FOOT * distance
    throw_loc = 1 + throwing * AVERAGE_PER_1_THROW
    throw_odds = normal(throw_loc, distance_stdv)

    # this does do a weird thing where long throws (with a high stdv) are much more likely to have high bonuses?
    # good enough for now though. consider it a long bounce ball that you have a ton of time to get in front of.
    if throw_odds > 1:
        throw_odds = 1 + (throw_odds - 1) * THROW_BONUS_SLOPE

    return max(min(MAX_THROW_ODDS_BONUS, throw_odds), 0)


THROW_SPEED_BASE = 0.01  # worst case throwing speed in seconds/foot
THROW_SPEED_FACTOR = 0.0025  # how much faster a throw is for 1 throwing, in seconds/foot
SECONDS_PER_MPH = (60 * 60) / 5280


def calc_throw_duration_base(throwing: float, distance: float) -> float:
    """calculates the time of a throw assuming no errors."""
    inv_throw_speed = THROW_SPEED_BASE - (THROW_SPEED_FACTOR * throwing)
    return distance * inv_throw_speed


MAX_GRAB_THINK_TIME = 2  # max added time for a throw based on the thrower's grabbiness
MIN_GRAB_THINK_TIME = 0  # min time at 2 grab
GRAB_THINK_FACTOR = (MAX_GRAB_THINK_TIME - MIN_GRAB_THINK_TIME) / 2


def calc_decision_time(grabbiness:float) -> float:
    return grabbiness * GRAB_THINK_FACTOR


class Throw(Update):
    """A single throw from one player to another."""
    def __init__(
            self,
            start_player: Player,
            end_player: Player,
            distance: float
        ):
        self.distance = distance
        self.throw_odds = roll_throw_odds_modifier(start_player['throwing'], distance)
        self.grab_odds = calc_grabbiness_odds(end_player['grabbiness'])

        self.total_odds = self.throw_odds * self.grab_odds
        self.error = not roll_to_catch(self.total_odds)

        self.duration = calc_throw_duration_base(start_player['throwing'], self.distance)
        self.duration += calc_decision_time(start_player['grabbiness'])
        if self.error:
            self.error_time = roll_error_time(self.total_odds)
            self.duration += self.error_time
        else:
            self.error_time = 0

        self.quick_string = f"from {start_player['name']} to {end_player['name']}"
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
        return f"Throw {self.quick_string} with {self.distance:.0f}', odds {self.total_odds*100:.2f}%," \
               f" and net time {self.duration:.2f}s"

    def __repr__(self):
        return f"<Throw {self.quick_string}>"


if __name__ == "__main__":
    from blaseball.util import quickteams
    g = quickteams.ballgame

    # TODO - quick demo

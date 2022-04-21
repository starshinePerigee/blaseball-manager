"""
This handles fielding, with the end goal of creating an event
which captures everything that has happened.
"""

from blaseball.playball.basepaths import Runner, Basepaths, calc_speed
from blaseball.playball.ballgame import BallGame
from blaseball.playball.liveball import LiveBall
from blaseball.playball.event import Update
from blaseball.stats.players import Player
from blaseball.stats.lineup import Defense
from blaseball.util.geometry import Coord

from numpy.random import normal, rand
from typing import List, Tuple


# TODO: Fielder and Runner should probably inherit from Player instead of containing one

# Catching:


REACH_MINIMUM = 0  # how close a ball must land to someone with 0 reach to not take a penalty
REACH_MAXIMUM = 60  # how close a ball must land to someone with 1 reach to not take a penalty
REACH_SLOPE_MINIMUM = 40  # how much further past


def calc_reach_odds(distance, reach) -> float:
    # reach sets the no-penalty grabbiness range:
    # TODO: this whole function is a fuck
    reach_maximum = reach * REACH_MAXIMUM
    grab_distance = max(reach_maximum - distance, 0)
    return grab_distance / (REACH_SLOPE_MINIMUM + reach_maximum)
    # TODO: probably should manage ground speed also somewhere, grounders are neglected throughout basically


GRABBINESS_CATCHING_FACTOR = 0.1


def roll_to_catch(odds, grabbiness) -> bool:
    # TODO: this is a hack and weird with grab:
    grab_modifier = (grabbiness - 1) * GRABBINESS_CATCHING_FACTOR
    total_difficulty = min(odds + grab_modifier, 0.98)
    return rand() < total_difficulty


ERROR_TIME_STDV = 3
ERROR_TIME_MEDIAN = 2


def roll_error_time(factor: float) -> float:
    """Calculate the time added by an error for throwing or catching."""
    time = -1
    while time < 0:
        time = normal(ERROR_TIME_MEDIAN * factor, ERROR_TIME_STDV)
    return time


class Catch(Update):
    """A player's attempt to catch a LiveBall"""
    def __init__(self, ball: LiveBall, fielder: Player, distance: float):
        super().__init__()

        self.odds = calc_reach_odds(distance, fielder['reach'])
        # TODO: this is a bad hack and I'm not sure what i'm doing here:
        self.difficulty = distance / (0.1 + self.odds) / 500
        self.duration = ball.flight_time()
        self.player_name = fielder['name']

        if roll_to_catch(self.odds, fielder['grabbiness']):
            if ball.catchable:
                self.text = f"{self.player_name} caught it for a fly out."
                self.caught = True
            else:
                self.caught = False
        else:
            self.caught = False
            self.duration += roll_error_time(self.difficulty)

    def __str__(self):
        return f"Catch by {self.player_name} with difficulty {self.difficulty:.2f} and duration {self.duration:.2f}"

    def __repr__(self):
        return f"<Catch by {self.player_name} duration {self.duration:.2f}>"


# Throwing:


THROW_ERROR_MEAN = -3
THROW_ERROR_STDV = 2  # throwing standard deviation
THROW_ERROR_THROW_FACTOR = -0.3


def roll_throw_difficulty(throwing: float) -> float:
    return normal(THROW_ERROR_MEAN, THROW_ERROR_STDV + THROW_ERROR_THROW_FACTOR * throwing)


THROW_SPEED_BASE = 0.01  # worst case throwing speed in seconds/foot
THROW_SPEED_FACTOR = 0.0025  # how much faster a throw is for 1 throwing, in seconds/foot
SECONDS_PER_MPH = (60 * 60) / 5280


def calc_throw_duration_base(throwing: float, distance: float) -> float:
    """calculates the time of a throw assuming no errors."""
    inv_throw_speed = THROW_SPEED_BASE - (THROW_SPEED_FACTOR * throwing)
    return distance * inv_throw_speed


class Throw(Update):
    """A single throw from one player to another."""
    def __init__(self,
                 start_player: Player,
                 end_player: Player,
                 distance: float
                 ):
        self.distance = distance
        self.difficulty = roll_throw_difficulty(start_player['throwing'])
        error_magnitude = self.difficulty - end_player['grabbiness']
        self.error = error_magnitude < 0
        if self.error:
            self.error_time = roll_error_time(error_magnitude)
        else:
            self.error_time = 0
        self.duration = calc_throw_duration_base(start_player['throwing'], self.distance) + self.error_time

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
        return f"Throw {self.quick_string} with {self.distance:.0f}', difficulty {self.difficulty:.2f}," \
               f" and net time {self.duration:.2f}s"

    def __repr__(self):
        return f"<Throw {self.quick_string}>"


class Fielder:
    """This class trakcs the current fielder - it changes the player it points to over the course of a live ball.
    Only one fielder should ever exist at any one time."""
    def __init__(self, defense: Defense, base_locations: List[Coord]):
        self.defense = defense
        self.base_locations = base_locations

        self.fielder = None
        self.location = None

    def catch(self, ball: LiveBall) -> Catch:
        self.location = ball.ground_location()
        fielder_position, distance = self.defense.closest(self.location)
        self.fielder = fielder_position.player
        catch = Catch(ball, self.fielder, distance)
        return catch

    def throw(self, target_base: int) -> Tuple[Update, float]:
        target_location = self.base_locations[target_base]
        position, distance = self.defense.closest(target_location)
        receiver = position.player

        if receiver is self.fielder:
            # tag the base?
            run_time = distance / calc_speed(self.fielder['speed'])
            return Update(f"{self.fielder['name']} tags base {target_base}"), run_time

        throw = Throw(self.fielder, receiver, distance)
        self.location = target_location
        self.fielder = receiver

        return throw, throw.duration

    DECISION_FUZZ_STDV = 1
    PROBABILITY_WINDOW = 1  # how much time you need to be 100% confident of a throw

    def prioritize_runner(self, runner: Runner) -> float:
        """Determines a weight for a runner"""
        # base weight (pun intended):
        next_base = runner.next_base()

        # modify by odds of throw
        distance = self.location.distance(self.base_locations[next_base])
        duration = calc_throw_duration_base(self.fielder['throwing'], distance)

        time_fuzz = normal(0, Fielder.DECISION_FUZZ_STDV * (2 - self.fielder['awareness']))
        runner_time = runner.time_to_base() + time_fuzz

        # if runner time >>> duration, this evaluates to 0. if duration >>> runner time, this evaluate to 1.
        # if 0 < delta < PROBABILITY_WINDOW this evalutes to somewhere between 0 and 1 continuously
        net_time = (duration - runner_time) * Fielder.PROBABILITY_WINDOW
        odds = max(0.0, min(1.0, net_time))
        return odds

    def fielders_choice(self, active_runners: List[Runner]) -> int:
        """Decide which base to throw to based on the list of runners"""
        runners = [(self.prioritize_runner(runner), runner) for runner in active_runners]
        runners.sort(key=lambda x: x[0])
        return runners[0][1].next_base()

    def __str__(self):
        return f"Fielder, currently {self.fielder['name']} at {self.location}"

    def __repr__(self):
        return f"<{str(self)}>"


class CatchOut(Update):
    def __init__(self, fielder: Player, batter: Player):
        super().__init__(f"{batter['name']} hit a flyout to {fielder['name']}")


class FieldingOut(Update):
    def __init__(self, fielder: Player, runner: Runner, throw: bool = True):
        verb = "thrown" if throw else "tagged"
        if runner.forward:
            base = runner.base + 1
        else:
            base = runner.base
        super().__init__(f"{runner.player['name']} {verb} out at base {base} by {fielder['name']}.")


class Rundown(Update):
    pass


class RunScored(Update):
    def __init__(self, runner: Player):
        super().__init__(f"{runner['name']} scored!")


class FieldBall:
    def __init__(self, batter: Player, defense: Defense, live_ball: LiveBall, basepaths: Basepaths):
        self.runs = 0
        self.outs = 0
        self.updates = []

        fielder = Fielder(defense, basepaths.base_coords)
        catch = fielder.catch(live_ball)
        self.updates += [catch]
        if catch.caught:
            self.updates += [CatchOut(fielder.fielder, batter)]
            self.outs += 1
            basepaths.tag_up_all()
        else:
            basepaths += batter

        distance_to_home = live_ball.ground_location().distance(Coord(0, 0))
        throw_time = calc_throw_duration_base(fielder.fielder['throwing'], distance_to_home) - 1  # cut it a little short
        runs, scoring_runners = basepaths.advance_all(catch.duration, throw_time)
        self.runs += runs
        self.updates += [RunScored(runner) for runner in scoring_runners]

        while basepaths:
            active_runners = [runner for runner in basepaths.runners if runner]
            target = fielder.fielders_choice(active_runners)

            # a rundown occurs when:
            # fielder is on a base
            # throwing it one base forward or backwards
            # with a player in between
            # who is not out

            updates, throw_duration = fielder.throw(target)
            self.updates += [updates]

            outs, players_out = basepaths.check_out(target)
            self.outs += outs
            self.updates += [FieldingOut(fielder.fielder, runner, not tagable) for runner, tagable in players_out]

            new_runs, runners_scoring = basepaths.advance_all(throw_duration)
            self.runs += new_runs
            self.updates += [RunScored(runner) for runner in runners_scoring]

        if len(self.updates) < 2:
            self.updates += [self.filler_text(basepaths.runners[-1])]

    def filler_text(self, runner: Runner) -> Update:
        BASE_LENGTH = {
            1: "single.",
            2: "double.",
            3: "triple!",
            4: "quadruple!!"
        }
        return Update(f"{runner.player['name']} hit a {BASE_LENGTH[runner.base]}")

if __name__ == "__main__":
    from blaseball.stats import players, teams
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

    infield_fly = LiveBall(30, 70, 90)


    def field_ball(ball, batter):
        fb = FieldBall(g.batter(batter), g.defense().defense, ball, g.bases)

        for update in fb.updates:
            print(update.text)
        print(g.bases.nice_string())
        print("")

    field_ball(infield_fly, 0)
    field_ball(infield_fly, 1)
    field_ball(infield_fly, 2)

    close_ground = LiveBall(-30, 15, 90)

    field_ball(close_ground, 3)
    field_ball(close_ground, 4)
    field_ball(close_ground, 5)

# TODO: no one seems to get thrown out? :c

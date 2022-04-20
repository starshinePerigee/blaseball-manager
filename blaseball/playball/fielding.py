"""
This handles fielding, with the end goal of creating an event
which captures everything that has happened.
"""

from blaseball.playball.ballgame import BallGame
from blaseball.playball.liveball import LiveBall
from blaseball.playball.event import Update
from blaseball.stats.players import Player
from blaseball.stats.stadium import Stadium
from blaseball.stats.lineup import Defense
from blaseball.util.geometry import Coord

from numpy.random import normal, rand
from typing import List, Tuple


# Running:


LEADOFF_BRAVERY_FACTOR = 0.1 * 90
LEADOFF_BASE = 0.05 * 90
PITCHER_AWARENESS_FACTOR = 2 * 0.1 * 90
PITCHER_THROWING_FACTOR = 1 * 0.1 * 90
PITCHER_ANTI_FEAR_FACTOR = 1.5 * 0.1 * 90


def calc_leadoff(runner: Player, pitcher: Player, catcher: Player) -> float:
    """Calculate the leadoff distance for a player in feet."""
    bravery = runner['bravery']
    throwing = pitcher['throwing']
    awareness = max(pitcher['awareness'], catcher['awareness'])
    base_leadoff = LEADOFF_BRAVERY_FACTOR * bravery + LEADOFF_BASE
    pitcher_fear = -PITCHER_ANTI_FEAR_FACTOR
    pitcher_fear += PITCHER_AWARENESS_FACTOR * awareness
    pitcher_fear += PITCHER_THROWING_FACTOR * throwing
    return base_leadoff + pitcher_fear


SPEED_FACTOR = 0.01  # seconds per foot gained for 1 speed
BASE_SPEED = 0.05  # base speed in seconds per foot


def calc_speed(speed: float) -> float:
    """Calculate a player's speed in feet per second."""
    return 1 / (BASE_SPEED - SPEED_FACTOR * speed)


class Runner:
    """A runner on the basepaths
    It's a little silly to instantiate these every time we field, but I don't want to roll this into Game rn
    """
    def __init__(self, player: Player, basepath_length: float):
        self.player = player
        self.basepath_length = basepath_length

        self.speed = calc_speed(player['speed'])

        self.base = 0  # last base touched by this player
        self.remainder = 0  # how far down the basepath they've gone, in feet
        self.forward = True  # is the runner trying to return to base
        self.force = True  # runner is forced to move forward
        self.safe = False  # is the runner done running?

    def tag_up(self):
        self.forward = False

    def hold(self):
        self.remainder = 0
        self.safe = True

    def reset(self, base: int, pitcher: Player, catcher: Player) -> None:
        self.base = base
        self.remainder = calc_leadoff(self.player, pitcher, catcher)
        self.forward = True
        self.force = False
        self.safe = False

    DECISION_FUZZ_STDV = 3
    TIME_REQUIRED_BEFORE_BRAVERY = 2
    TIME_REQUIRED_FACTOR = 1

    def decide(self, duration: float) -> bool:
        """Decide if a player is going to advance or return, given a throw expected in duration time"""
        # TODO: team and game state effects
        # high timing, high bravery: advance or retreat perfectly
        # low timing, high bravery: always advance
        # low timing, low bravery: never advance
        # high timing, low bravery: advance only when it's absolutely safe

        if self.remainder / self.basepath_length > 0.5:
            # the closest base is the next base, so go for it always.
            return True

        if self.player['timing'] > 1:
            effective_timing = 1 + (self.player['timing'] - 1) / 2  # scale timing down as you get higher
        else:
            effective_timing = self.player['timing']
        effective_timing *= Runner.DECISION_FUZZ_STDV / 1.5
        duration_fuzz = normal(0, effective_timing)
        effective_duration = duration + duration_fuzz  # the runner guesses at how much time they have

        time_required = effective_duration - self.time_to_base()  # how much extra time a player has -
        # a negative time required means a player doens't have enough time.

        decision_threshold = Runner.TIME_REQUIRED_BEFORE_BRAVERY - self.player['bravery'] * Runner.TIME_REQUIRED_FACTOR
        # a less-brave player needs more of an assurance before running. This should be 0 at maximum bravery.

        return time_required < decision_threshold

    def advance(self, duration: float) -> Tuple[int, float]:
        """moves a player forward on the basepaths for a """
        total_distance = self.speed * duration + self.remainder
        advanced_bases = int(total_distance / self.basepath_length)
        remainder = total_distance % self.basepath_length
        remainder_time = remainder / self.speed  # ugly hack to get this back
        # if self.decide(remainder_time):

        return advanced_bases, remainder

    def time_to_base(self) -> float:
        """Calculate long it will take this runner to reach their next base"""
        if self.safe:
            distance_remaining = 0
        elif self.forward:
            distance_remaining = self.basepath_length - self.remainder
        else:
            distance_remaining = self.remainder
        return distance_remaining / self.speed

    def next_base(self) -> int:
        return self.base + 1 if self.forward and not self.safe else self.base

    def total_distance(self) -> float:
        return self.remainder + self.base * self.basepath_length

    def coords(self, stadium: Stadium) -> Coord:
        """Return the player's current coordinates"""
        # TODO
        return stadium.BASES[self.base]

    def __str__(self):
        if self.safe:
            text = "safe on"
        elif self.forward:
            text = "advancing from"
        else:
            text = "tagging up to"
        return f"{self.player['name']} {text} base {self.base} with remainder {self.remainder:.0f3}"

    def __bool__(self):
        return not self.safe



# Catching:


REACH_MINIMUM = 0  # how close a ball must land to someone with 0 reach to not take a penalty
REACH_MAXIMUM = 60  # how close a ball must land to someone with 1 reach to not take a penalty
REACH_SLOPE_MINIMUM = 40  # how much further past


def calc_reach_difficulty(distance, reach) -> float:
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

        self.difficulty = calc_reach_difficulty(distance, fielder['reach'])
        self.duration = ball.flight_time()

        if roll_to_catch(self.difficulty, fielder['grabbiness']):
            if ball.catchable:
                self.text = f"{fielder['name']} caught it for a fly out."
                self.caught = True
            else:
                self.caught = False
        else:
            self.caught = False
            self.duration += roll_error_time(self.difficulty)

    def __str__(self):
        return f"Catch with difficulty {self.difficulty} and duration {self.duration}"


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


class Fielder:
    """This class trakcs the current fielder - it changes the player it points to over the course of a live ball.
    Only one fielder should ever exist at any one time."""
    def __init__(self, defense: Defense, base_locations: List[Coord]):
        self.defense = defense
        self.base_locations = base_locations

        self.fielder = None
        self.location = None

    def catch(self, ball: LiveBall) -> Tuple[Update, float]:
        self.location = ball.ground_location()
        fielder_position, distance = self.defense.closest(self.location)
        self.fielder = fielder_position.player
        catch = Catch(ball, self.fielder, distance)
        return catch, catch.duration

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


class Basepaths:
    """Stores the bases and basepaths, and manipulates runners on base. Each game should have one Basepaths"""
    def __init__(self, stadium: Stadium):
        self.runners = []  # runners acts as a FIFO queue - the first entry is the furthest down.
        self.number_of_bases = stadium.NUMBER_OF_BASES  # does not count home
        self.basepath_length = stadium.BASEPATH_LENGTH

        self.base_coords = stadium.BASES + [stadium.HOME_PLATE]  # 0 - 3 and then 0 again

    def decide_all(self, fielder: Player, location: Coord) -> List[Runner]:
        advancing_runners = []  # example in comments is a 3-1-0 split
        most_recent_base = self.number_of_bases  # 4
        for i, runner in enumerate(self.runners):  # 0, 1, 2
            runners_left = len(self.runners) - i  # 3, 2, 1
            if runner.base < runners_left:  # 3 < 3: False, 1 < 2: True, 0 < 1: True
                # runner is forced forward
                advancing_runners += [runner]
                if runner.safe:
                    raise RuntimeError(f"Runner forced off base! Runner: {runner} and Basepaths {self}")
                else:
                    runner.force = True
                    runner.forward = True
            else:
                runner.force = False
                if not runner:
                    # runner is already safe
                    pass
                elif runner.base + 1 >= most_recent_base:
                    # the base ahead of the runner is blocked, so you have to go back.
                    runner.tag_up()
                    advancing_runners += [runner]
                else:
                    runner_distance = location.distance(self.base_coords[runner.base])
                    runner_time = throw_duration_base(fielder['throwing'], runner_distance)
                    advancing_runners += [runner]

                    if not runner.decide(runner_time):
                        runner.tag_up()
            most_recent_base = runner.next_base()

        return advancing_runners

    def tag_up_all(self) -> List[Runner]:
        advancing_runners = []
        for runner in self.runners:
            if runner:
                runner.tag_up()
                advancing_runners += [runner]
        return advancing_runners

    def advance_all(self, duration: float) -> int:
        """Moves all runners forward by duration, """
        # TODO: handle decisions when a runner reaches a base
        # TODO: errors on double-occupied bases

        runs = 0
        previous_runner = None
        for runner in self.runners:
            bases, distance = runner.advance(duration)
            # handle a fast runner being kept up by a slow runner:
            if previous_runner is not None:
                if runner.total_distance() > previous_runner.total_distance():
                    runner.base = previous_runner.base
                    runner.remainder = previous_runner.remainder
            # handle people making it home
            # if the previous runner made it home, this runner won't be backed up.
            if bases + runner.base > self.number_of_bases:
                runner.safe = True  # good luck
                self.runners.remove(runner)
                runs += 1
                previous_runner = None
            else:
                previous_runner = runner
        return runs

    def check_out(self):
        # TODO
        pass

    def reset(self, pitcher: Player, catcher: Player):
        """Moves all runners back to their most recently passed base, then sets them at leadoff"""
        most_recent_base = self.number_of_bases + 1
        for runner in self.runners:
            runner.reset(min(runner.base, most_recent_base - 1), pitcher, catcher)
            if runner.base <= 0:
                raise RuntimeError(f"Error: basepaths reset while a player was at home! {len(self)} runners present.")
            most_recent_base = runner.base

    def __add__(self, player: Player):
        self.runners += [Runner(player, self.basepath_length)]

    def __len__(self):
        return len(self.runners)

    def __str__(self):
        # TODO
        return f"Basepaths with {len(self)} runners"

    def __bool__(self):
        return any(self.runners)




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
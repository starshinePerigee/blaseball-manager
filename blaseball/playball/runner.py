"""Handles players out on the basepaths."""

from blaseball.playball.fielding import throw_duration_base
from blaseball.stats.players import Player
from blaseball.stats.stadium import Stadium
from blaseball.util.geometry import Coord

from typing import Tuple, List
from numpy.random import normal, rand


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


class Runner:
    """A runner on the basepaths
    It's a little silly to instantiate these every time we field, but I don't want to roll this into Game rn
    """
    def __init__(self, player: Player, basepath_length: float):
        self.player = player
        self.basepath_length = basepath_length

        self.speed = 1 / (BASE_SPEED - SPEED_FACTOR * player['speed'])  # player speed in feet per second

        self.base = 0
        self.remainder = 0
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
        self.remainder = calc_leadoff(self.player['bravery'], )
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

        time_to_base = (self.basepath_length - self.remainder) / self.speed  # how much time is needed to reach base
        time_required = effective_duration - time_to_base  # how much extra time a player has -
        # a negative time required means a player doens't have enough time.

        decision_threshold = Runner.TIME_REQUIRED_BEFORE_BRAVERY - self.player['bravery'] * Runner.TIME_REQUIRED_FACTOR
        # a less-brave player needs more of an assurance before running. This should be 0 at maximum bravery.

        return time_required < decision_threshold

    def advance(self, duration: float) -> Tuple[int, float]:
        """moves a player forward on the basepaths for a """
        total_distance = self.speed * duration + self.remainder
        advanced_bases = int(total_distance / self.basepath_length)
        remainder = total_distance % self.basepath_length
        return advanced_bases, remainder

    def total_distance(self):
        return self.remainder + self.base * self.basepath_length

    def coords(self, stadium: Stadium) -> Coord:
        """Return the player's current coordinates"""
        # TODO
        return stadium.BASES[self.base]

    def __str__(self):
        return f"{self.player['name']} on base {self.base} with remainder {self.remainder:.0f3}"

    def __bool__(self):
        return not self.safe


class Basepaths:
    """Stores the bases and basepaths, and manipulates runners on base. Each game should have one Basepaths"""
    def __init__(self, stadium:Stadium):
        self.runners = []  # runners acts as a FIFO queue - the first entry is the furthest down.
        self.number_of_bases = stadium.NUMBER_OF_BASES  # does not count home
        self.basepath_length = stadium.BASEPATH_LENGTH

        self.base_coords = stadium.BASES + [stadium.HOME_PLATE] # 0 - 3 and then 0 again

    def decide_advance(self, fielder: Player, location: Coord) -> List[Runner]:
        advancing_runners = []  # example in comments is a 3-1-0 split
        most_recent_base = self.number_of_bases # 4
        for i, runner in enumerate(self.runners):  # 0, 1, 2
            runners_left = len(self.runners) - i  # 3, 2, 1
            if runner.base < runners_left:  # 3 < 3: False, 1 < 2: True, 0 < 1: True
                # runner is forced forward
                most_recent_base = runner.base + 1
                advancing_runners += [runner]
                if runner.safe:
                    raise RuntimeError(f"Runner forced off base! {len(self)} runners present.")
                else:
                    runner.force = True
            else:
                runner.force = False
                if not runner:
                    # runner is already safe, or their next base is occupied (4, 3, 1, 0)
                    most_recent_base = runner.base
                elif runner.base + 1 >= most_recent_base:
                    # the base ahead of the runner is blocked, so you have to go back.
                    runner.tag_up()
                    advancing_runners += [runner]
                    most_recent_base = runner.base
                else:
                    runner_distance = location.distance(self.base_coords[runner.base])
                    runner_time = throw_duration_base(fielder['throwing'], runner_distance)
                    advancing_runners += [runner]

                    if runner.decide(runner_time):
                        # runner goes for it
                        most_recent_base = runner.base + 1
                    else:
                        runner.tag_up()
                        most_recent_base = runner.base

        return advancing_runners

    def advance_all(self, duration: float) -> int:
        """Moves all runners forward by duration, """
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
        return f"Basepaths with {len(self)} runners"

    def __bool__(self):
        return any(self.runners)


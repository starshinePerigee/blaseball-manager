"""This handles players on the basepaths, including Runners"""

from blaseball.playball.event import Update
from blaseball.stats.players import Player
from blaseball.stats.stadium import Stadium
from blaseball.util.geometry import Coord

from numpy.random import normal
from typing import List, Tuple


# Running:


SPEED_FACTOR = 0.01  # seconds per foot gained for 1 speed
BASE_SPEED = 0.05  # base speed in seconds per foot


def calc_speed(speed: float) -> float:
    """Calculate a player's speed in feet per second."""
    return 1 / (BASE_SPEED - SPEED_FACTOR * speed)


LEADOFF_BRAVERY_FACTOR = 0.1 * 90
LEADOFF_BASE = 0.05 * 90
PITCHER_AWARENESS_FACTOR = 2 * 0.1 * 90
PITCHER_THROWING_FACTOR = 1 * 0.1 * 90
PITCHER_ANTI_FEAR_FACTOR = 1.5 * 0.1 * 90


def calc_leadoff(bravery, throwing, max_awareness) -> float:
    """Calculate the leadoff distance for a player in feet."""
    base_leadoff = LEADOFF_BRAVERY_FACTOR * bravery + LEADOFF_BASE
    pitcher_fear = -PITCHER_ANTI_FEAR_FACTOR
    pitcher_fear += PITCHER_AWARENESS_FACTOR * max_awareness
    pitcher_fear += PITCHER_THROWING_FACTOR * throwing
    return base_leadoff + pitcher_fear


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
        self.remainder = 0.0
        self.forward = True
        self.safe = True

    def reset(self, base: int, pitcher: Player, catcher: Player) -> None:
        self.base = base
        max_awareness = max(catcher['awarenss'], pitcher['awarenss'])
        self.remainder = calc_leadoff(self.player['bravery'], pitcher['throwing'], max_awareness)
        self.forward = True
        self.force = False
        self.safe = False

    DECISION_FUZZ_STDV = 3
    TIME_REQUIRED_BEFORE_BRAVERY = 2
    TIME_REQUIRED_FACTOR = 1

    def decide(self, duration: float, min_base: int, max_base: int, hit_duration_bonus: float = 0) -> bool:
        """Decide if a player is going to advance or return, given a throw expected in duration time"""
        # TODO: team and game state effects
        # high timing, high bravery: advance or retreat perfectly
        # low timing, high bravery: always advance
        # low timing, low bravery: never advance
        # high timing, low bravery: advance only when it's absolutely safe

        # the ball was just hit, so in addition to the flight time, there's also a throw coming.
        duration += hit_duration_bonus

        if self.base < min_base:
            # you are forced out
            self.force = True
            return True
        if not self.forward:
            # you are trying to tag up
            self.force = self.base + 1 > max_base
            return True
        if self.base >= max_base:
            # there is someone on a base ahead of you
            self.force = True
            return False

        self.force = False
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

        extra_time_to_base = effective_duration - self.time_to_base()  # how much extra time a player has -
        # a negative time required means a player doens't have enough time.

        decision_threshold = Runner.TIME_REQUIRED_BEFORE_BRAVERY - self.player['bravery'] * Runner.TIME_REQUIRED_FACTOR
        # a less-brave player needs more of an assurance before running. This should be 0 at maximum bravery.

        return extra_time_to_base >= decision_threshold

    def advance(self, duration: float, min_base: int, max_base: int, hit_duration_bonus: float = 0) -> None:
        """moves a player forward on the basepaths for a set amount of duration. check for runs afterwards."""
        # convert distance into time
        while duration >= 0.0:
            if self.decide(duration, min_base, max_base, hit_duration_bonus):
                # you are running
                if self.forward:
                    time_to_next_base = (self.basepath_length - self.remainder) / self.speed
                else:
                    time_to_next_base = self.remainder / self.speed

                if time_to_next_base > duration:
                    if self.forward:
                        self.remainder += duration * self.speed
                    else:
                        self.remainder -= duration * self.speed
                    break
                else:
                    duration -= time_to_next_base
                    if self.forward:
                        self.base += 1
                    else:
                        self.forward = True
                    self.remainder = 0.0
            else:
                if self.remainder <= 1:  # the base is 1 foot wide lol
                    if self.base < min_base:
                        raise RuntimeError(f"Runner {self.player} attempted to tag up to occupied base {self.base}")
                    self.hold()
                    break
                else:
                    self.forward = False

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

    def coords(self, base_locations: List[Coord]) -> Coord:
        """Return the player's current coordinates"""
        start_base = base_locations[self.base]
        next_base = base_locations[self.next_base()]
        distance_ratio = self.remainder / start_base.distance(next_base)
        x = (next_base.x - start_base.x) * distance_ratio + start_base.x
        y = (next_base.y - start_base.y) * distance_ratio + start_base.y
        return Coord(x, y)

    def __str__(self):
        if self.safe:
            text = "safe on"
        elif self.forward:
            text = "advancing from"
        else:
            text = "tagging up to"
        return f"{self.player['name']} {text} base {self.base} with remainder {self.remainder:.0f}"

    def __repr__(self):
        return f"<Runner {self.player['name']} on base {self.base} with remainder {self.remainder:.0f}>"

    def __bool__(self):
        return not self.safe


# TODO: there's defs a bug allowing multiple people to pile on a base.

class Basepaths:
    """Stores the bases and basepaths, and manipulates runners on base. Each game should have one Basepaths"""
    def __init__(self, stadium: Stadium):
        self.runners = []  # runners acts as a FIFO queue - the first entry is the furthest down.
        self.number_of_bases = stadium.NUMBER_OF_BASES  # does not count home
        self.basepath_length = stadium.BASEPATH_LENGTH

        self.base_coords = stadium.BASE_LOCATIONS + [stadium.HOME_PLATE]  # 0 - 3 and then 0 again

    def tag_up_all(self) -> None:
        for runner in self.runners:
            if runner:
                runner.tag_up()

    def advance_all(self, duration: float, hit_duration_bonus: float = 0) -> Tuple[int, List[Player]]:
        """Moves all runners forward by duration, """
        runners_scoring = []
        max_base = self.number_of_bases + 1  # 4 for standard
        for i, runner in enumerate(self.runners):  # we're going to step through a 0-1-3 split
            min_base = len(self.runners) - i  # 3, 2, 1
            # max base:  4, 4,
            runner.advance(duration, min_base, max_base, hit_duration_bonus)
            if runner.base > self.number_of_bases:
                runner.safe = True  # good luck
                self.runners.remove(runner)
                runners_scoring += [runner.player]
                max_base = self.number_of_bases + 1
            else:
                if runner.safe or not runner.forward:
                    max_base = runner.base - 1
                else:
                    max_base = runner.base
        return len(runners_scoring), runners_scoring

    TAG_OUT_DISTANCE = 10

    def check_out(self, base: int) -> Tuple[int, List[Tuple[Runner, bool]]]:
        """Check to see if a runner is thrown out."""
        outs = 0
        runners_out = []
        for runner in self.runners:
            if (runner.forward and runner.base == base - 1) or (not runner.forward and runner.base == base):
                if runner.forward:
                    tagable = (self.basepath_length - runner.remainder) <= Basepaths.TAG_OUT_DISTANCE
                else:
                    tagable = runner.remainder <= Basepaths.TAG_OUT_DISTANCE

                if runner.force or tagable:
                    self.runners.remove(runner)
                    outs += 1
                    runners_out += [(runner, tagable)]

        return outs, runners_out

    def reset(self, pitcher: Player, catcher: Player):
        """Moves all runners back to their most recently passed base, then sets them at leadoff"""
        most_recent_base = self.number_of_bases + 1
        for runner in self.runners:
            runner.reset(min(runner.base, most_recent_base - 1), pitcher, catcher)
            if runner.base <= 0:
                raise RuntimeError(f"Error: basepaths reset while a player was at home! {len(self)} runners present.")
            most_recent_base = runner.base

    def nice_string(self):
        string = ""
        for i in range(1, self.number_of_bases + 1):
            string += f"{i}: "
            for runner in self.runners:
                if runner.base == i:
                    string += runner.player['name']
            string += "\r\n"
        return string

    def __add__(self, player: Player):
        self.runners += [Runner(player, self.basepath_length)]
        return self

    def __len__(self):
        return len(self.runners)

    def __str__(self):
        # TODO
        return f"Basepaths with {len(self)} runners"

    def __bool__(self):
        return any(self.runners)

"""This handles players on the basepaths.

Lots of things can affect players on the basepaths - primarily fielding, but other game actions
(iwalks, bullshit) can have varying effects, so we need to handle this separately and then
command it. In a way, this is the model to inplay's controller - an actual fielded ball
involves a long dialogue between inplay, fielding, and basepaths.

Note that the way this works is runners track their own progression around the basepaths,
managed by the Basepaths class.
"""

from blaseball.stats.players import Player
from blaseball.stats.stadium import Stadium
from blaseball.util.geometry import Coord

from numpy.random import normal
from typing import List, Tuple, Optional, Union
from collections.abc import MutableMapping


# Running:


SPEED_FACTOR = 0.01  # seconds per foot gained for 1 speed
BASE_SPEED = 0.05  # base speed in seconds per foot


def calc_speed(speed: float) -> float:
    """Calculate a player's speed in feet per second."""
    return 1 / (BASE_SPEED - SPEED_FACTOR * speed)


LEADOFF_BRAVERY_FACTOR = 20  # leadoff feet per 1 bravery
LEADOFF_BASE = 10  # base leadoff, static
PITCHER_AWARENESS_FACTOR = 12  # feet penalty/gain for 2/0 max(pitcher catcher) awareness
PITCHER_THROWING_FACTOR = 8   # feet penalty/gain for 2/0 pitcher throwing


def calc_leadoff(bravery, throwing, max_awareness) -> float:
    """Calculate the leadoff distance for a player in feet."""
    base_leadoff = LEADOFF_BRAVERY_FACTOR * bravery + LEADOFF_BASE
    pitcher_fear = PITCHER_AWARENESS_FACTOR * max_awareness + PITCHER_THROWING_FACTOR * throwing
    return max(base_leadoff - pitcher_fear, 0)


DURATION_FUZZ_FACTOR_AT_ONE_TIMING = 0.2  # how much a 1 stdv miss affect estimated duration at 1 timing
# measured in percent multiplier
TIMING_FOR_ZERO_STDV = 2.5
DURATION_BONUS_FACTOR_PER_SEC = 0.01  # how much to fuzz at further distances
MARGIN_REQUIRED_BEFORE_BRAVERY = 0.5  # what percent of base time to base is needed to go for it
MARGIN_REQUIRED_BRAVERY_FACTOR = 0.25  # how much bravery reduces time required


def roll_net_advance_time(duration, time_to_base, timing, bravery) -> float:
    """roll for how he runner feels about advancing - if this number is positive, they believe they
    have enough time to advance."""
    # high timing, high bravery: advance or retreat perfectly
    # low timing, high bravery: always advance
    # low timing, low bravery: never advance
    # high timing, low bravery: advance only when it's absolutely safe

    # this might be better as a class method on Runner?
    # this also might need to get factored around to be cleaner. it's written in intuitive logic,
    # but it might mean breaking it out further gets complicated since both sides of the comparison are modified.

    duration_bonus_fuzz = 1 + (duration * DURATION_BONUS_FACTOR_PER_SEC)
    duration_fuzz_stdv = DURATION_FUZZ_FACTOR_AT_ONE_TIMING * (TIMING_FOR_ZERO_STDV - timing) * duration_bonus_fuzz
    duration_fuzz_factor = normal(1, duration_fuzz_stdv)
    effective_duration = duration * duration_fuzz_factor  # the runner guesses at how much time they have

    net_bravery_factor = 1 + MARGIN_REQUIRED_BEFORE_BRAVERY - bravery * MARGIN_REQUIRED_BRAVERY_FACTOR
    # a less-brave player needs more of an assurance before running. This should be 0 at maximum bravery.

    # net advance time is how long you have minus how long you need
    net_advance_time = effective_duration - time_to_base * net_bravery_factor
    return net_advance_time


class Runner:
    """A runner on the basepaths
    It's a little silly to instantiate these every time we field, but I don't want to roll this into Game rn
    """
    def __init__(self, player: Player, basepath_length: float):
        self.player = player
        self.basepath_length = basepath_length

        self.speed = calc_speed(player['speed'])

        self.base = 0  # last base touched by this player
        self.remainder = 0  # how far down the basepath they've gone, in feet.
        # remainder does not invert if the player starts running backwards - a player 10 feet towards 2nd from first,
        # who is returning to first, has a remainder of 10.

        # these represent runner intents. they do not get set in decide() and advance() but affect it:
        self.tagging_up = False
        self.holding = False
        self.always_run = False

        # these are "dependent variables" - they get set in decide() and advance():
        self.forward = True  # is the runner currently advancing?
        self.force = True  # runner in a forced state: they do not have an option in terms of where they are going.
        self.safe = False  # is the runner done running?
        # tagging up = self.force + not self.forward

    def time_to_base(self) -> float:
        """Calculate long it will take this runner to reach their next base"""
        if self.forward:
            distance_remaining = self.basepath_length - self.remainder
        else:
            distance_remaining = self.remainder
        return distance_remaining / self.speed

    def next_base(self) -> int:
        return self.base + 1 if self.forward and not self.safe else self.base

    def total_distance(self) -> float:
        return self.remainder + self.base * self.basepath_length

    def tag_up(self):
        """Force this runner to turn to their most recent safe base."""
        self.tagging_up = True

        self.forward = False
        self.force = True

    def hold(self):
        """Force the player to stay put at the next base they touch.."""
        self.holding = True

        if self.remainder < 1:
            self.safe = True

    def touch_base(self, base=None):
        """the player has touched a base while the ball is in play."""
        if base is not None:
            self.base = base
        self.remainder = 0.0
        self.tagging_up = False
        self.safe = True
        self.forward = True
        self.force = False

    def reset(self, pitcher: Player, catcher: Player, base: int = None) -> None:
        """Reset a runner's state to the default. call between plays."""
        if base is not None:
            self.base = base

        max_awareness = max(catcher['awareness'], pitcher['awareness'])
        self.remainder = calc_leadoff(self.player['bravery'], pitcher['throwing'], max_awareness)

        self.tagging_up = False
        self.holding = False
        self.always_run = False

        self.forward = True
        self.force = False
        self.safe = False

    def decide(self, duration: float, min_base: int, max_base: int, hit_duration_bonus: float = 0) -> None:
        """Decide if a player is going to advance or retreat/hold, given a throw expected in duration time.
        sets "self.force" and "self.forward" appropriately """
        # TODO: team and game state effects
        # TODO: convert errors into logging and outs

        # the ball was just hit, so in addition to the flight time, there's also a throw coming.
        duration += hit_duration_bonus

        if max_base - min_base < 0:
            raise RuntimeError(f"{self.player['name']} caught in a pickle between {min_base} and {max_base}!")

        if self.tagging_up:
            # player is currently tagging up due to the rules of blaseball (caught fly, etc)
            if self.base == 0:
                raise RuntimeError(f"{self.player['name']} attempting to tag up with base 0!")
            elif self.base < min_base:
                raise RuntimeError(f"{self.player['name']} attempting to tag up to invalid base {min_base}")
            elif self.base > max_base:
                raise RuntimeError(f"{self.player['name']} attempting to tag up past max base {max_base}, "
                                   f"current base {self.base}")
            self.forward = False
            self.force = True
            return

        if self.base >= max_base or self.base <= min_base - 1:
            # player is in a forced state
            self.force = True
            if self.base > max_base:
                raise RuntimeError(f"{self.player['name']} more than two bases ahead! {self.base} vs max {max_base}")
            elif self.base == max_base:
                self.forward = False
            elif self.base < min_base - 1:
                raise RuntimeError(f"{self.player['name']} more than two bases behind! {self.base} vs min {min_base}")
            elif self.base == min_base - 1:
                self.forward = True
            return

        self.force = False

        if self.always_run:
            self.forward = True
        elif self.remainder / self.basepath_length > 0.5:
            # the closest base is the next base, so go for it always.
            self.forward = True
        elif self.holding:
            self.forward = False
        else:
            net_time_to_advance = roll_net_advance_time(
                duration,
                self.time_to_base(),
                self.player['timing'],
                self.player['bravery']
            )
            self.forward = net_time_to_advance > 0

    def advance(
            self,
            duration: float,  # how long this runner has until the next decision point
            min_base: int,  # the first base they can stop at (inclusive)
            max_base: int,  # the last base they can stop at (inclusive)
            hit_duration_bonus: float = 0  # use for if the ball was just hit; because there will be a throw as well
    ) -> None:
        """moves a player forward on the basepaths for a set amount of duration.
        The runner will decide how far to advance given the provided constraints.

        check for runs afterwards."""
        # convert distance into time
        if self.holding and self.safe:
            return

        while duration >= 0.0:
            self.decide(duration, min_base, max_base, hit_duration_bonus)

            if not self.forward and self.remainder <= 1:
                # you are on base and want to stay there
                # (the base is 1 foot wide lol)
                self.touch_base()
                break

            # you need to go somewhere - forward or back.
            self.safe = False
            if self.forward:
                # you are running to the next base
                time_to_next_base = (self.basepath_length - self.remainder) / self.speed
            else:
                # you are returning to base
                time_to_next_base = self.remainder / self.speed

            if time_to_next_base > duration:
                # you need more time than you have to reach the next base, so make progress
                if self.forward:
                    self.remainder += duration * self.speed
                else:
                    self.remainder -= duration * self.speed
                break
            else:
                # you can make it to the next base, so get there and cycle
                duration -= time_to_next_base
                next_base = self.base + 1 if self.forward else self.base
                self.touch_base(next_base)

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

    def __eq__(self, other):
        if isinstance(other, Runner):
            return self is other
        elif isinstance(other, Player):
            return self.player is other
        else:
            raise TypeError(f"Invalid type comparison: Runner vs {type(other)} (other: {other})")

class Basepaths(MutableMapping):
    """Stores the bases and basepaths, and manipulates runners on base. Each game should have one Basepaths

    Iterating over this gives you None entries for empty bases."""
    def __init__(self, stadium: Stadium):
        self.runners = []  # runners acts as a FIFO queue - the first entry is the furthest down. We don't track
        # empty bases here. Is this a hack? is this bad? future self will find out.
        self.number_of_bases = stadium.NUMBER_OF_BASES  # does not count home
        self.basepath_length = stadium.BASEPATH_LENGTH

        self.base_coords = stadium.BASE_LOCATIONS + [stadium.HOME_PLATE]  # 0 - 3 and then 0 again

    def tag_up_all(self) -> None:
        for runner in self.runners:
            if runner:
                runner.tag_up()

    def advance_all(self, duration: float, hit_duration_bonus: float = 0) -> Tuple[int, List[Player]]:
        """Moves all runners forward by duration, having them decide if to advance as needed.
        This iterates from the most forward runner backwards.
        """
        runners_scoring = []
        max_base = self.number_of_bases + 1  # 4 for standard
        for i, runner in enumerate(self.runners):  # we're going to step through a 0-1-3 split
            # current_runner = len(self.runners) - (i + 1)  # 2, 1, 0
            min_base = len(self.runners) - i  # the 3rd (index 2) runner has to end up at the 3rd base.
            # max base:  4,
            runner.advance(duration, min_base, max_base, hit_duration_bonus)
            if runner.base > self.number_of_bases:
                runners_scoring += [runner]
                max_base = self.number_of_bases + 1
            else:
                if runner.safe or not runner.forward:
                    max_base = runner.base - 1
                else:
                    max_base = runner.base

        for runner in runners_scoring:
            runner.safe = True  # good luck
            self.runners.remove(runner)

        return len(runners_scoring), [runner.player for runner in runners_scoring]

    TAG_OUT_DISTANCE = 10

    def check_out(self, base: int) -> Optional[Runner]:
        """Check to see if any runner is out if the ball is at a specific base.
        Note that there's an edge case where two players are valid:
        - a runner on first with a 2 foot leadoff
        - the batter hits a line drive straight to the first baseman that reaches the baseman while the runner on first
          is still in the tag out radius.
        the runner will not be tagged out, as is realistic.
        """
        for runner in self.runners:
            out = False
            if runner.forward:
                if runner.base + 1 == base:
                    tagable = self.basepath_length - runner.remainder <= Basepaths.TAG_OUT_DISTANCE
                    out = tagable or runner.force
            else:
                if runner.base == base:
                    tagable = runner.remainder <= Basepaths.TAG_OUT_DISTANCE
                    out = tagable or runner.force

            if out:
                self.runners.remove(runner)
                return runner
        return None

    def reset_all(self, pitcher: Player, catcher: Player):
        """Moves all runners back to their most recently passed base, then sets them at leadoff"""
        most_recent_base = self.number_of_bases + 1
        for runner in self.runners:
            runner.reset(pitcher, catcher, min(runner.base, most_recent_base - 1), )
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

    def __getitem__(self, key: int) -> Optional[Player]:
        if key < 0 or key > self.number_of_bases:
            raise KeyError(f"Tried to get runner on invalid base {key} against number of bases {self.number_of_bases}")
        for runner in self.runners:
            if runner.base == key:
                return runner
        return None

    def __setitem__(self, key: int, value: Player) -> None:
        """Set the player to base key. Creates a runner for the player and inserts it into the runner list in order."""
        new_runner = Runner(value, self.basepath_length)
        new_runner.base = key

        for i, runner in enumerate(self.runners):
            # remember, runners list is in reverse order (it's from third to first base)
            if runner.base == key:
                raise KeyError(f"Tried to set a runner to base {key} which was already occupied by {runner}")
            if runner.base < key:
                self.runners.insert(i, new_runner)
                return
        self.runners += [new_runner]

    def __delitem__(self, key) -> None:
        for i, runner in enumerate(self.runners):
            if runner.base == key:
                del(self.runners[i])
                return
        raise KeyError(f"Attempted to delete nonexistent player on base {key}!")

    def to_base_list(self):
        return [self[i] for i in range(0, self.number_of_bases+1)]

    def boolean_occupied_list(self):
        return [self[i] is not None for i in range(1, self.number_of_bases+1)]

    def __add__(self, player: Player):
        self.runners += [Runner(player, self.basepath_length)]
        return self

    def __iter__(self):
        for runner in self.runners:
            yield runner

    def __len__(self):
        return len(self.runners)

    def __str__(self):
        # TODO
        return f"Basepaths with {len(self)} runners"

    def __bool__(self):
        return any(self.runners)

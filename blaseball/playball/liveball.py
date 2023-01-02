"""
Governs the flight of a ball after it is hit, errored out, etc.
"""

import math
from numpy.random import normal

from blaseball.playball.event import Update
from blaseball.playball.hitting import Swing
from blaseball.playball.pitching import Pitch
from blaseball.playball.gamestate import GameState, GameTags, BaseSummary
from blaseball.playball.manager import Manager
from blaseball.stats.players import Player
from blaseball.util.geometry import Coord
from blaseball.util.messenger import Messenger
from blaseball.stats import stats as s


DEGSY = u'\N{DEGREE SIGN}'


GRAVITY_MPH = 80000
WIND_RESISTANCE = 16


class LiveBall:
    """A ball live on the field that must be fielded."""
    def __init__(self, launch_angle, field_angle, speed, origin=Coord(0, 0)):
        if launch_angle < 0:  # hack to handle grounders
            self.launch_angle = -launch_angle  # 0 is flat horizontal, 90 is straight up, can go negative
            self.speed = speed / 2
            self.catchable = False
        else:
            self.launch_angle = launch_angle
            self.speed = speed
            self.catchable = True
        self.field_angle = field_angle  # 0 is right to first base, 90 is to third base, can go 360
        self.origin = origin  # the originating point of the ball, from 0,0 for home plate to 1,1 for second base
        # can extend past home base into the field - actual limit depends on the field.

    def _theoretical_distance(self) -> float:
        return self.speed ** 2 * 2 * math.sin(math.radians(self.launch_angle)) / GRAVITY_MPH * 5280

    def flight_time(self) -> float:
        return 2 * self.speed * math.sin(math.radians(self.launch_angle)) / GRAVITY_MPH * 60 * 60

    def distance(self):
        return self._theoretical_distance() - self.flight_time() ** 2 * WIND_RESISTANCE

    def ground_location(self) -> Coord:
        # 0 degs is right along first base
        pos_x = self.distance() * math.cos(math.radians(self.field_angle)) + self.origin.x
        pos_y = self.distance() * math.sin(math.radians(self.field_angle)) + self.origin.y
        return Coord(pos_x, pos_y)  # yes we could initialize with polar coords but we need to handle the origin :c

    def __bool__(self):
        return self.speed > 0

    def __str__(self):
        string = f"launch {self.launch_angle:.0f}{DEGSY} field {self.field_angle:.0f}{DEGSY} speed {self.speed:.0f} mph"
        if self.origin:
            string += f" origin ({self.origin.x:.2f}, {self.origin.y:.2f})"
        return string

    def __repr__(self):
        return f"LiveBall({self.launch_angle}, {self.field_angle}, {self.speed})"


BASE_LAUNCH_ANGLE = 10  # median launch angle for a 0* batter
LAUNCH_ANGLE_POWER_FACTOR = 5  # bonus launch angle for a 5* batter
LAUNCH_ANGLE_BASE_STDEV = 40
LA_HIT_QUALITY_FACTOR = -0.5  # magic factor for launch angle hit quality,
# higher LA_HIT_QUALITY_FACTOR means hit quality matters less for scaling launch angles with good hits,
# LAHQF of 1 means a remainder of 1 cuts launch angle stdev in half.


def roll_launch_angle(quality, batter_power) -> float:
    median_launch_angle = BASE_LAUNCH_ANGLE + batter_power * LAUNCH_ANGLE_POWER_FACTOR
    angle_modifier = LA_HIT_QUALITY_FACTOR / (LA_HIT_QUALITY_FACTOR + quality)
    launch_angle_stdev = LAUNCH_ANGLE_BASE_STDEV * angle_modifier
    launch_angle = normal(loc=median_launch_angle, scale=launch_angle_stdev)
    return launch_angle


PULL_STDV_AT_ONE_QUALITY = 30
PULL_STDV_AT_PT_ONE_QUALITY = 300
inverse_pull_factor = 1/PULL_STDV_AT_PT_ONE_QUALITY


def roll_field_angle(quality, batter_pull) -> float:
    pull_stdv = PULL_STDV_AT_ONE_QUALITY / (quality + inverse_pull_factor)
    field_angle = normal(loc=batter_pull, scale=pull_stdv)
    if (0 <= field_angle <= 90) and quality >= 1:
        # reroll clean hits once
        field_angle = normal(loc=batter_pull, scale=pull_stdv)
    return field_angle


MIN_EXIT_VELOCITY_AVERAGE = 80  # average EV for a player at 0 stars
MAX_EXIT_VELOCITY_AVERAGE = 120  # max for a juiced player at 10 stars
EXIT_VELOCITY_RANGE = MAX_EXIT_VELOCITY_AVERAGE - MIN_EXIT_VELOCITY_AVERAGE
EXIT_VELOCITY_STDEV = 10  # additional fuzz on top of hit quality, should be low
EXIT_VELOCITY_PITY_FACTOR = -0.8  # the higher this is, the less exit velo is reduced with low hit quality.
# This is very sensitive:
# 0 means exit velo is 0 at 0 quality
# 0.1 means exit velo is 56%%
# 0.2 means 66%
EXIT_VELOCITY_QUALITY_EXPONENT = 1 / 4


def roll_exit_velocity(quality, reduction, batter_power) -> float:
    """Determine how fast the ball is going when it leaves the bat.
    There are two factors:
    net power (power - reduction) is the primary driving force;
    hit quality has diminishing return scaling, so you get your best work at 1; past a certain point
    you're playing tee ball.
    """
    net_power = batter_power - reduction  # can - and often will - be negative!
    exit_velocity_base = MIN_EXIT_VELOCITY_AVERAGE + net_power * EXIT_VELOCITY_RANGE / 2
    quality_modifier = (quality + EXIT_VELOCITY_PITY_FACTOR) ** EXIT_VELOCITY_QUALITY_EXPONENT
    exit_velocity = normal(loc=exit_velocity_base * quality_modifier, scale=EXIT_VELOCITY_STDEV)
    return max(exit_velocity, 0)


class HitBall(Update):
    """A hit ball is an update which turns a swing into a live ball, which it carries with it."""
    def __init__(self, game: GameState, quality: float, reduction: float, batter: Player, messenger: Messenger):
        super().__init__()

        launch_angle = roll_launch_angle(quality, batter[s.power])
        field_angle = roll_field_angle(quality, batter[s.pull])
        reduction = EXIT_VELOCITY_RANGE * reduction
        exit_velocity = roll_exit_velocity(quality, reduction, batter[s.power])
        self.live = LiveBall(launch_angle=launch_angle, field_angle=field_angle, speed=exit_velocity)

        ground_location = self.live.ground_location()
        self.foul = game.stadium.check_foul(ground_location)
        if self.foul:
            self.homerun = False
            # don't send foul yet - fielding will have a chance at it.
        else:
            self.homerun, hit_wall = game.stadium.check_home_run(ground_location)
            if self.homerun:
                self.text = "Home run!"
                messenger.queue(len(game.bases) + 1, [GameTags.home_run, GameTags.runs_scored])
                # TODO: pull into home run handler / basepath handler?
                messenger.send(BaseSummary(game.stadium.NUMBER_OF_BASES), GameTags.bases_update)

            elif hit_wall:
                self.text = "Off the outfield wall!"
                self.live = LiveBall(launch_angle=launch_angle, field_angle=field_angle, speed=exit_velocity-5)

        messenger.queue(self, [GameTags.hit_ball, GameTags.game_updates])

    def __str__(self):
        return f"HitBall with live {self.live}"

    def __repr__(self):
        return f"<HitBall with live {repr(self.live)}>"


class HitManager(Manager):
    def __init__(self, state: GameState, messenger: Messenger):
        super().__init__(state, messenger)
        self.last_reduction = 0

    def start(self):
        self.messenger.subscribe(self.set_reduction, GameTags.pitch)
        self.messenger.subscribe(self.do_hit, GameTags.swing)

    def set_reduction(self, pitch: Pitch):
        self.last_reduction = pitch.reduction

    def do_hit(self, swing: Swing):
        if swing.hit:
            HitBall(
                self.state,
                swing.hit_quality,
                self.last_reduction,
                self.state.batter(),
                self.messenger
            )

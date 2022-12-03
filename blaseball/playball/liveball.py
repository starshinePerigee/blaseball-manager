"""
Governs the flight of a ball after it is hit, errored out, etc.
"""

import math
from numpy.random import normal

from blaseball.playball.event import Update
from blaseball.playball.hitting import Swing
from blaseball.playball.gamestate import GameState
from blaseball.stats.players import Player
from blaseball.util.geometry import Coord
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
LA_HIT_QUALITY_FACTOR = 0.5  # magic factor for launch angle hit quality,
# higher LA_HIT_QUALITY_FACTOR means hit quality matters less for scaling launch angles with good hits,
# LAHQF of 1 means a remainder of 1 cuts launch angle stdev in half.


def roll_launch_angle(quality, batter_power) -> float:
    median_launch_angle = BASE_LAUNCH_ANGLE + batter_power * LAUNCH_ANGLE_POWER_FACTOR
    angle_modifier = LA_HIT_QUALITY_FACTOR / (LA_HIT_QUALITY_FACTOR + quality)
    launch_angle_stdev = LAUNCH_ANGLE_BASE_STDEV * angle_modifier
    launch_angle = normal(loc=median_launch_angle, scale=launch_angle_stdev)
    return launch_angle


PULL_STDEV = 45


def roll_field_angle(batter_pull) -> float:
    for __ in range(0, 10):
        field_angle = normal(loc=batter_pull, scale=PULL_STDEV)
        if 0 <= field_angle <= 90:
            return field_angle
    return 45


MIN_EXIT_VELOCITY_AVERAGE = 80  # average EV for a player at 0 stars
MAX_EXIT_VELOCITY_AVERAGE = 120  # max for a juiced player at 10 stars
EXIT_VELOCITY_RANGE = MAX_EXIT_VELOCITY_AVERAGE - MIN_EXIT_VELOCITY_AVERAGE
EXIT_VELOCITY_STDEV = 10  # additional fuzz on top of hit quality, should be low
EXIT_VELOCITY_PITY_FACTOR = 0.2  # the higher this is, the less exit velo is reduced with low hit quality.
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
    def __init__(self, game: GameState, quality: float, reduction: float, batter: Player):
        super().__init__()

        launch_angle = roll_launch_angle(quality, batter['power'])
        field_angle = roll_field_angle(batter['pull'])
        reduction = EXIT_VELOCITY_RANGE * reduction
        exit_velocity = roll_exit_velocity(quality, reduction, batter['power'])
        self.live = LiveBall(launch_angle=launch_angle, field_angle=field_angle, speed=exit_velocity)
        self.homerun, hit_wall = game.stadium.check_home_run(self.live.ground_location())

        if self.homerun:
            self.text = "Home run!"
        elif hit_wall:
            self.text = "Off the outfield wall!"
            self.live = LiveBall(launch_angle=launch_angle, field_angle=field_angle, speed=exit_velocity-5)

        self.update_stats(batter)

    def update_stats(self, batter: Player):
        batter[s.total_hit_distance] += self.live.distance()
        batter[s.total_exit_velocity] += self.live.speed

        if self.homerun:
            batter[s.total_home_runs] += 1

    def __str__(self):
        return f"HitBall with live {self.live}"

    def __repr__(self):
        return f"<HitBall with live {repr(self.live)}>"


if __name__ == "__main__":
    from blaseball.stats import statclasses
    from blaseball.playball.pitching import Pitch

    from blaseball.util import quickteams
    g = quickteams.game_state

    test_pitcher = g.defense()['pitcher']
    test_catcher = g.defense()['catcher']
    test_batter = g.batter()

    print(f"Batter: {test_batter}")
    for s in statclasses.all_stats['rating']:
        if s.category == 'batting':
            print(f"{s}: {test_batter._to_stars(test_batter[s.name])}")

    PITCHES = 1000

    def derby():
        all_hits = []
        furthest_hit = None
        furthest_swing = None
        furthest_distance = 0
        for __ in range(0, 1000):
            p = Pitch(g, test_pitcher, test_catcher)
            p.location = 0
            s = Swing(g, p, test_batter)
            if s.hit:
                h = HitBall(g, s.hit_quality, p.reduction, test_batter)
                all_hits += [h]
                if h.live.distance() > furthest_distance:
                    furthest_distance = h.live.distance()
                    furthest_hit = h.live
                    furthest_swing = s

        print(f"Furthest hit is {furthest_distance:.0f} ft, "
              f"with a quality of {furthest_swing.hit_quality:.2f}, exit velocity {furthest_hit.speed:.0f} mph, "
              f"and launch angle {furthest_hit.launch_angle:.0f}")
        print("")

    derby()

    test_batter['power'] = 1.5
    test_batter['contact'] = 0.1

    derby()

    test_batter['power'] = 0.1
    test_batter['contact'] = 1.5

    derby()

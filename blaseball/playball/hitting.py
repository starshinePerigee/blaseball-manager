"""
Controls a player's pre-hit decisions as well as their actual swing attempt.
"""

from blaseball.playball.ballgame import BallGame
from blaseball.playball.pitching import Pitch
from blaseball.playball.fielding import LiveBall
from blaseball.stats.players import Player

from numpy.random import normal, rand


# Hit Intent:


BONUS_BALLS = 0.5  # extra ball used when determining desperation
DESPERATION_MIDPOINT = 0.85  # balls under for 100% desperation
DESPERATION_FLOOR = 0.2  # lowest amount of desperation possible


def decide_hit_effect(game: BallGame):
    pass


def calc_desperation(game: BallGame) -> float:
    total_balls = game.balls + BONUS_BALLS
    ball_ratio = total_balls / (BallGame.BALL_COUNT + BONUS_BALLS - 1)
    strike_ratio = game.strikes / (BallGame.STRIKE_COUNT - 1)
    balls_over = ball_ratio - strike_ratio
    if balls_over < 0:
        balls_over = 0
    desperation_base = (1 - balls_over) / DESPERATION_MIDPOINT
    desperation_scaled = desperation_base * (1 - DESPERATION_FLOOR) + DESPERATION_FLOOR
    return desperation_scaled


DISCIPLINE_REDUCTION_AT_ONE = 0.5  # how much obscurity is reduced when you have a 1 in discipline
DISCIPLINE_REDUCTION_FACTOR = -DISCIPLINE_REDUCTION_AT_ONE/(DISCIPLINE_REDUCTION_AT_ONE-1)
# DRF is equal to 1 when DRA1 is 0.5, but we need this math to get a nice curve with 1 at 0


# Swing parameters:


def calc_read_chance(obscurity, batter_discipline) -> float:
    # this is equal to 1 when DR is 0.5. it's algebra, trust me:
    discipline_modifier = DISCIPLINE_REDUCTION_FACTOR / (DISCIPLINE_REDUCTION_FACTOR + batter_discipline)
    effective_obscurity = obscurity * discipline_modifier
    return 1 / (1 + effective_obscurity)


def calc_swing_chance(read_chance, desperation, strike: bool) -> float:
    strike_chance = read_chance if strike else (1-read_chance)
    return strike_chance * desperation


def roll_for_swing_decision(swing_chance) -> bool:
    swing_roll = rand()
    return swing_roll < swing_chance


FOUL_BIAS = 0.6  # the higher this is, the more frequently fouls and hits occur vs strike swinging
NET_CONTACT_FACTOR = 0.4  # how much net contact affects the ability to hit.


def roll_hit_quality(net_contact) -> float:
    """Roll for hit quality. 1 is a good hit, 0-1 is a foul"""
    return normal(loc=(net_contact + FOUL_BIAS) * NET_CONTACT_FACTOR, scale=1)


# Hit parameters:


BASE_LAUNCH_ANGLE = 10  # median launch angle for a 0* batter
LAUNCH_ANGLE_POWER_FACTOR = 5  # bonus launch angle for a 5* batter
LAUNCH_ANGLE_BASE_STDEV = 40
LA_HIT_QUALITY_FACTOR = 0.5  # magic factor for launch angle hit quality,
# higher LA_HIT_QUALITY_FACTOR means hit quality matters less for scaling launch angles with good hits,
# LAHQF of 1 means a remainder of 1 cuts launch angle stdev in half.


def roll_launch_angle(quality_remainder, batter_power) -> float:
    median_launch_angle = BASE_LAUNCH_ANGLE + batter_power * BASE_LAUNCH_ANGLE
    angle_modifier = LA_HIT_QUALITY_FACTOR / (LA_HIT_QUALITY_FACTOR + quality_remainder)
    launch_angle_stdev = LAUNCH_ANGLE_BASE_STDEV * angle_modifier
    launch_angle = normal(loc=median_launch_angle, scale=launch_angle_stdev)
    return launch_angle


PULL_STDEV = 90


def roll_field_angle(batter_pull) -> float:
    while True:
        field_angle = normal(loc=batter_pull, scale=PULL_STDEV)
        if 0 < field_angle < 90:
            return field_angle


MIN_EXIT_VELOCITY_AVERAGE = 80  # average EV for a player at 0 stars
MAX_EXIT_VELOCITY_AVERAGE = 120  # max for a juiced player at 10 stars
EXIT_VELOCITY_RANGE = MAX_EXIT_VELOCITY_AVERAGE - MIN_EXIT_VELOCITY_AVERAGE
EXIT_VELOCITY_STDEV = 10  # additional fuzz on top of hit quality, should be low
EXIT_VELOCITY_PITY_FACTOR = 0.2  # the higher this is, the less exit velo is reduced with low hit quality.
# This is very sensitive - 0 means exit velo is 0 at 1.0 quality, 0.1 means exit velo is 40% and 0.2 means 60%
EXIT_VELOCITY_QUALITY_EXPONENT = 1 / 4


def roll_reduction(pitch_reduction: float) -> float:
    base_reduction = EXIT_VELOCITY_RANGE * pitch_reduction
    scaled_reduction = base_reduction * 2 * rand()
    return scaled_reduction


def roll_exit_velocity(quality_remainder, reduction, batter_power) -> float:
    exit_velocity_base = MIN_EXIT_VELOCITY_AVERAGE + batter_power * EXIT_VELOCITY_RANGE / 2
    quality_modifier = (quality_remainder + EXIT_VELOCITY_PITY_FACTOR) ** EXIT_VELOCITY_QUALITY_EXPONENT
    exit_velocity = normal(loc=exit_velocity_base * quality_modifier, scale=EXIT_VELOCITY_STDEV)
    exit_velocity -= reduction
    return exit_velocity


def roll_hit(hit_quality: float, pitch_reduction: float, batter: Player) -> LiveBall:
    quality_remainder = hit_quality - 1

    launch_angle = roll_launch_angle(quality_remainder, batter['power'])
    field_angle = roll_field_angle(batter['pull'])
    reduction = roll_reduction(pitch_reduction)
    exit_velocity = roll_exit_velocity(quality_remainder, reduction, batter['power'])

    return LiveBall(launch_angle=launch_angle, field_angle=field_angle, speed=exit_velocity)


class Swing:
    """A player's swing, from decision up to hit quality"""
    def __init__(self, game: BallGame, pitch: Pitch, batter: Player):
        self.desperation = calc_desperation(game)
        read_chance = calc_read_chance(pitch.obscurity, batter['discipline'])
        self.swing_chance = calc_swing_chance(read_chance, self.desperation, pitch.strike)
        self.did_swing = roll_for_swing_decision(self.swing_chance)

        self.strike = False
        self.ball = False
        self.foul = False
        self.live = None

        if self.did_swing:
            self.net_contact = batter['contact'] - pitch.difficulty
            self.hit_quality = roll_hit_quality(self.net_contact)
            if self.hit_quality < 0:
                self.strike = True
            elif 0 < self.hit_quality < 1:
                self.foul = True
            else:
                self.live = roll_hit(self.hit_quality, pitch.reduction, batter)
        else:
            self.net_contact = 0
            self.hit_quality = 0
            self.strike = pitch.strike
            self.ball = not pitch.strike

    def __bool__(self):
        return self.did_swing

    def __str__(self):
        if not self.did_swing:
            text = "Strike, looking" if self.strike else "Ball"
            return f"{text} with swing odds {self.swing_chance*100:.01f}% from desperation {self.desperation:.02f}"
        elif self.live:
            return f"Hit ball with quality {self.hit_quality:.3f}, result {self.live}"
        else:
            text = ""
            if self.strike:
                text += "strike"
            if self.foul:
                text += "foul"
            return f"Swung {text} with quality {self.hit_quality:.3f}"


if __name__ == "__main__":
    from blaseball.playball.pitching import Pitch
    from blaseball.stats import players, teams, stats
    from blaseball.stats.lineup import Lineup
    from data import teamdata
    pb = players.PlayerBase()
    team_names = teamdata.TEAMS_99
    league = teams.League(pb, team_names[5:7])
    print('setup complete..\r\n')

    l1 = Lineup("Home Lineup")
    l1.generate(league[0])
    l2 = Lineup("Away Lineup")
    l2.generate(league[1])

    g = BallGame(l1, l2, False)

    test_pitcher = g.defense()['pitcher']
    test_catcher = g.defense()['catcher']
    test_batter = g.batter()

    print(f"Batter: {test_batter}")
    for s in stats.all_stats['rating']:
        if s.category == 'batting':
            print(f"{s}: {test_batter._to_stars(test_batter[s.name])}")

    def do_swing():
        p = Pitch(g, test_pitcher, test_catcher)
        print(p)
        for __ in range(0, 5):
            print(Swing(g, p, test_batter))
        print("")

    print("")
    g.strikes = 2
    do_swing()

    g.strikes = 0
    do_swing()

    g.balls = 3
    do_swing()



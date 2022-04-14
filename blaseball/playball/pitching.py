"""
Controls a pitch through the entire pitch process - beginning with an intent, through the call,
to the pitch.
"""

from blaseball.playball.ballgame import BallGame
from blaseball.stats.players import Player

from scipy.stats import norm
from numpy.random import normal
from math import tanh


ONE_STDV_AT_ONE_ACCURACY = 0.7  # how wide one standard deviation is at one accuracy
ONE_STDV_AT_ZERO_ACCURACY = 1  # how wide one standard deviation is at zero accuracy

ACCURACY_STDV_SLOPE = ONE_STDV_AT_ONE_ACCURACY - ONE_STDV_AT_ZERO_ACCURACY
ACCURACY_STDV_INTERCEPT = ONE_STDV_AT_ZERO_ACCURACY


# Catcher calling functions:


def decide_pitch_effect(game: BallGame):
    pass


CALLING_WEIGHTS = {
    'count': 20,
    'discipline_bias': 5,
    'bases_loaded': 3,
    'outs_number': 3,
    'current_v_next_hitter': 1
}
FIRST_PITCH_BIAS = -0.2  # extra bias
RUNNER_IN_SCORING_POSITION_MODIFIER = 0.5  # how much to weight a runner in scoring position
RUNNERS_TO_WALK_FACTOR = 1.5  # the exponential factor for how much to worry about walking players
RUNNERS_TO_WALK_MODIFIER = 0.5  # the linear counterfactor of the above number


def calc_calling_modifier(game: BallGame) -> float:
    """
    Determine the ideal shift towards or away from the plate including catcher effects.
    This is a unitless number and can be positive (away from the strike zone)
    or negative (towards the strike zone)
    """
    calling_modifier = 0

    # evaluate current count:
    ball_ratio = game.balls / (BallGame.BALL_COUNT - 1)
    strike_ratio = game.strikes / (BallGame.STRIKE_COUNT - 1)
    if ball_ratio == 0 and strike_ratio == 0:
        count_effect = FIRST_PITCH_BIAS
    else:
        count_effect = strike_ratio - ball_ratio
    if game.balls == BallGame.BALL_COUNT - 1:
        count_effect += -0.2  # bonus hyper modifier
    count_effect *= CALLING_WEIGHTS['count']
    calling_modifier += count_effect

    # evaluate hitter discipline bias
    # the more disciplined a hitter is, the more strikes to throw and thus the more negative
    # the more powerful a hitter is, the more balls to throw and thus more positive
    discipline_bias_effect = game.batter()['power'] - game.batter()['discipline']
    discipline_bias_effect *= CALLING_WEIGHTS['discipline_bias']

    # calculate runners to walk vs. runners to bat in
    bases_occupied = [i is not None for i in game.bases]
    runner_in_scoring_position = bases_occupied[BallGame.NUMBER_OF_BASES - 1]
    runners_to_walk = 0
    for base in bases_occupied:
        if base:
            runners_to_walk += 1
        else:
            break
    if runners_to_walk != BallGame.NUMBER_OF_BASES and runner_in_scoring_position:
        # there is a player in socring position who won't score on a walk:
        risp_effect = RUNNER_IN_SCORING_POSITION_MODIFIER
    else:
        risp_effect = 0
    runners_to_walk_effect = runners_to_walk ** RUNNERS_TO_WALK_FACTOR
    runners_to_walk_effect /= RUNNERS_TO_WALK_MODIFIER
    bases_loaded_effect = runners_to_walk_effect + risp_effect
    bases_loaded_effect *= CALLING_WEIGHTS['bases_loaded']
    calling_modifier += bases_loaded_effect

    # calculate effect from current number of outs
    median_out = (BallGame.OUTS_COUNT - 1) / 2  # 1 for three outs, 1.5 for four
    outs_effect = game.outs - median_out
    outs_effect *= CALLING_WEIGHTS['outs_number']
    calling_modifier += outs_effect

    # calculate effect of current hitter vs next hitter difficulty
    cvn_hitter = game.batter()['total offense'] - game.batter(1)['total offense']
    cvn_hitter *= CALLING_WEIGHTS['current_v_next_hitter']
    calling_modifier += cvn_hitter
    return calling_modifier


STRIKE_PERCENT_BASE = 0.6  # what percentage of pitches would be strikes if calling was 0
STRIKE_PERCENT_VERTICAL_SCALE = 0.4  # how much calling can move the strike percentage
STRIKE_PERCENT_WIDTH = 20  # higher values make a steeper slope of the tanh function for strike percent


def calc_ideal_strike_percent(calling_modifier) -> float:
    """Determine the ideal strike percent based on calling modifiers"""
    tan_mod = tanh(calling_modifier/STRIKE_PERCENT_WIDTH)
    scaled_mod = tan_mod * STRIKE_PERCENT_VERTICAL_SCALE
    strike_percent = STRIKE_PERCENT_BASE - scaled_mod
    return strike_percent


def calc_target_location(pitcher_accuracy, strike_percent) -> float:
    """reverse the strike percent into a target location"""
    pitcher_stdev = ACCURACY_STDV_SLOPE * pitcher_accuracy + ACCURACY_STDV_INTERCEPT
    strike_z = norm.ppf(strike_percent)
    strike_position = strike_z * pitcher_stdev
    called_location = max(0, 1-strike_position)
    return called_location


def decide_call(game: BallGame, catcher: Player, pitcher: Player) -> float:
    """Determines a pitcher's intent, before they throw the ball, based on pitcher, catcher, and game state.

    Returns a 0 - 2ish value for ball position, where 0 is dead center of strike zone, 1 is edge of strike zone,
    and >1 is further into ball territory."""

    base_calling_modifier = calc_calling_modifier(game)
    catcher_calling_modifier = base_calling_modifier * min(1.0, catcher['calling'])
    ideal_strike_percent = calc_ideal_strike_percent(catcher_calling_modifier)
    pitcher_accuracy = pitcher['accuracy']
    target_location = calc_target_location(pitcher_accuracy, ideal_strike_percent)
    return target_location


# Pitching functions:


def roll_location(target_location, pitcher_accuracy) -> float:
    """Roll the actual pitch location"""
    pitcher_stdev = ACCURACY_STDV_SLOPE * pitcher_accuracy + ACCURACY_STDV_INTERCEPT
    return normal(loc=target_location, scale=pitcher_stdev)


FRAMING_FACTOR = 0.1  # how much exceptionally good catchers can bias the upires


def check_strike(pitch_location, catcher_calling):
    catcher_mod = max(0.0, catcher_calling - 1) * FRAMING_FACTOR
    return abs(pitch_location) <= 1 + catcher_mod


MAX_BASE_OBSCURITY = 10  # maximum amount of obscurity you can get via location (at 1.0)
OBSCURITY_DISTANCE_SCALE = 5  # magic factor to determine how distance scales,
# lower is higher obscurity for the same distance.
TRICKINESS_FACTOR = 0.5  # amount of obscurity added to every pitch for 1 trickiness


def calc_obscurity(pitch_location, pitcher_trickery) -> float:
    closeness_scale = 1 / OBSCURITY_DISTANCE_SCALE
    far_out = abs(pitch_location - 1)
    location_obscurity = closeness_scale / (far_out + (1 / MAX_BASE_OBSCURITY))
    trick_obscurity = pitcher_trickery * TRICKINESS_FACTOR
    return location_obscurity + trick_obscurity


DIFFICULTY_DISTANCE_FACTOR = 1.5  # EXPONENT for how being far out affects difficulty
STRIKE_ZONE_DIFFICULTY_CENTER = 0.5  # the point at which you start gaining difficulty for being far out
FORCE_FACTOR = 1  # how much a pitcher's force affects difficulty


def calc_difficulty(pitch_location, pitcher_force) -> float:
    force_difficulty = FORCE_FACTOR * pitcher_force
    location_base = max(0.0, pitch_location - STRIKE_ZONE_DIFFICULTY_CENTER)
    location_difficulty = location_base ** DIFFICULTY_DISTANCE_FACTOR
    return force_difficulty + location_difficulty


REDUCTION_FROM_TRICKERY = 0.2  # the percentage removed from exit velocity for a pitcher with 1 trickery


def calc_reduction(pitcher_trickery) -> float:
    return REDUCTION_FROM_TRICKERY * pitcher_trickery


class Pitch:
    """
    Represents an actual pitch. has four key stats:
    location: where the pitch is, from 0 +, where 0 is right over the plate
    obscurity: how hard the pitch is to read, from 0 to 2-ish
    difficulty: how hard the pitch is to hit, from 0 +
    reduction: how much successful hits are reduced
    """
    def __init__(self, game: BallGame, pitcher: Player, catcher: Player):
        self.target = decide_call(game, catcher, pitcher)
        self.location = roll_location(self.target, pitcher['accuracy'])
        self.strike = check_strike(self.location, catcher['calling'])
        self.obscurity = calc_obscurity(self.location, pitcher['trickery'])
        self.difficulty = calc_difficulty(self.location, pitcher['force'])
        self.reduction = calc_reduction(pitcher['trickery'])

    def __str__(self):
        strike_text = "Strike" if self.strike else "Ball"
        return (f"{strike_text}: loc {self.location:.2f} call {self.target:.2f} obs {self.obscurity:.2f} "
                f"dif {self.difficulty:.2f} red {self.reduction:.2f}")


if __name__ == "__main__":
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
    print(f"Pitcher: {test_pitcher}")
    for s in stats.all_stats['rating']:
        if s.category == 'pitching':
            print(f"{s}: {test_pitcher._to_stars(test_pitcher[s.name])}")
    test_catcher = g.defense()['catcher']
    print(f"Catcher: {test_catcher}")
    print(f"Calling: {test_catcher._to_stars(test_catcher['calling'])}")
    print("")

    def do_pitch():
        calling_modifier = calc_calling_modifier(g)
        strike_percent = calc_ideal_strike_percent(calling_modifier)
        print(f"Catcher logic: modifier {calling_modifier} -> "
              f"strike {strike_percent*100:.1f}%")
        p = Pitch(g, test_pitcher, test_catcher)
        print(p)

    do_pitch()
    g.balls = 1
    do_pitch()
    g.balls = 2
    do_pitch()
    g.strikes = 2
    do_pitch()

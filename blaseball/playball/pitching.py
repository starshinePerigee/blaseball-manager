"""
Controls a pitch through the entire pitch process - beginning with an intent, through the call,
to the pitch.
"""

from scipy.stats import norm
from numpy.random import normal, rand
from math import tanh
from typing import List

from blaseball.playball.gamestate import GameState, GameRules, GameTags
from blaseball.playball.event import Update
from blaseball.stats.players import Player
from blaseball.util.messenger import Messenger
from blaseball.playball.manager import Manager
from blaseball.stats import stats as s


ONE_STDV_AT_ONE_ACCURACY = 0.7  # how wide one standard deviation is at one accuracy
ONE_STDV_AT_ZERO_ACCURACY = 1  # how wide one standard deviation is at zero accuracy

ACCURACY_STDV_SLOPE = ONE_STDV_AT_ONE_ACCURACY - ONE_STDV_AT_ZERO_ACCURACY
ACCURACY_STDV_INTERCEPT = ONE_STDV_AT_ZERO_ACCURACY


# Catcher calling functions:


def decide_pitch_effect(game: GameState):
    pass


FIRST_PITCH_BIAS = -0.2  # extra bias


def calling_mod_from_count(balls, strikes, balls_count, strikes_count) -> float:
    # evaluate current count:
    ball_ratio = balls / (balls_count - 1)
    strike_ratio = strikes / (strikes_count - 1)
    if ball_ratio == 0 and strike_ratio == 0:
        count_effect = FIRST_PITCH_BIAS
    else:
        count_effect = strike_ratio - ball_ratio
    if balls == balls_count - 1:
        count_effect += -0.2  # bonus hyper modifier
    return count_effect


def calling_mod_from_discipline_bias(power, discipline) -> float:
    # evaluate hitter discipline bias
    # the more disciplined a hitter is, the more strikes to throw and thus the more negative
    # the more powerful a hitter is, the more balls to throw and thus more positive
    return power - discipline


RUNNERS_EXPONENT = 1.5  # the exponential factor for how much to worry about walking players
RUNNERS_TO_WALK_MODIFIER = -2  # the linear counterfactor of the above number
RUNNER_IN_SCORING_POSITION_MODIFIER = 3


def calling_mod_from_runners(runners: List[bool]) -> float:
    # calculate runners to walk vs. runners to bat in
    # ref https://www.beyondtheboxscore.com/2009/3/30/814883/bases-loaded-2-outs-full-c

    # if the bases are loaded, it's between you and god:
    # if all(runners):
    #     return 0

    runners_to_walk = 0
    for base in runners:
        if base:
            runners_to_walk += 1
        else:
            break

    runners_to_walk_effect = runners_to_walk ** RUNNERS_EXPONENT
    runners_to_walk_effect *= RUNNERS_TO_WALK_MODIFIER

    runners_in_scoring_position = 0
    for base in runners[::-1]:
        if base:
            runners_in_scoring_position += 1
        else:
            break

    risp_effect = runners_in_scoring_position ** RUNNERS_EXPONENT
    risp_effect *= RUNNER_IN_SCORING_POSITION_MODIFIER
    bases_loaded_effect = runners_to_walk_effect + risp_effect

    return bases_loaded_effect


def calling_mod_from_outs(outs: int, outs_count: int) -> float:
    # calculate effect from current number of outs
    median_out = (outs_count - 1) / 2  # 1 for three outs, 1.5 for four
    return outs - median_out


def calling_mod_from_next_hitter(current: Player, on_deck: Player) -> float:
    return current[s.total_offense] - on_deck[s.total_offense]


CALLING_WEIGHTS = {
    'count': 20,
    'discipline_bias': 5,
    'bases_loaded': 3,
    'outs_number': 3,
    'current_v_next_hitter': 1
}


def calc_calling_modifier(game: GameState) -> float:
    """
    Determine the ideal shift towards or away from the plate including catcher effects.
    This is a unitless number and can be positive (away from the strike zone)
    or negative (towards the strike zone)
    """
    calling_modifier = 0
    calling_modifier += (calling_mod_from_count(game.balls, game.strikes,
                                                game.rules.ball_count, game.rules.strike_count)
                         * CALLING_WEIGHTS['count'])
    calling_modifier += (calling_mod_from_discipline_bias(game.batter()[s.power], game.batter()[s.discipline])
                         * CALLING_WEIGHTS['discipline_bias'])
    calling_modifier += calling_mod_from_runners(game.boolean_base_list()) * CALLING_WEIGHTS['bases_loaded']
    calling_modifier += calling_mod_from_outs(game.outs, game.rules.outs_count) * CALLING_WEIGHTS['outs_number']
    calling_modifier += (calling_mod_from_next_hitter(game.batter(), game.batter(1))
                         * CALLING_WEIGHTS['current_v_next_hitter'])
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


def decide_call(game: GameState, catcher: Player, pitcher: Player) -> float:
    """Determines a pitcher's intent, before they throw the ball, based on pitcher, catcher, and game state.

    Returns a 0 - 2ish value for ball position, where 0 is dead center of strike zone, 1 is edge of strike zone,
    and >1 is further into ball territory."""

    base_calling_modifier = calc_calling_modifier(game)
    catcher_calling_modifier = base_calling_modifier * min(1.0, catcher[s.calling])
    ideal_strike_percent = calc_ideal_strike_percent(catcher_calling_modifier)
    pitcher_accuracy = pitcher[s.accuracy]
    target_location = calc_target_location(pitcher_accuracy, ideal_strike_percent)
    return target_location


# Pitching functions:


def roll_location(target_location, pitcher_accuracy) -> float:
    """Roll the actual pitch location"""
    pitcher_stdev = ACCURACY_STDV_SLOPE * pitcher_accuracy + ACCURACY_STDV_INTERCEPT
    return normal(loc=target_location, scale=pitcher_stdev)


FRAMING_FACTOR = 0.1  # how much exceptionally good catchers can bias the upires


def check_strike(pitch_location, catcher_calling) -> bool:
    """Returns True if pitch is a strike"""
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
    location_base = max(0.0, abs(pitch_location) - STRIKE_ZONE_DIFFICULTY_CENTER)
    location_difficulty = location_base ** DIFFICULTY_DISTANCE_FACTOR
    return force_difficulty + location_difficulty


REDUCTION_FROM_TRICKERY = 1  # reduction counteracts batter power directly.
REDUCTION_OFFSET = -1


def roll_reduction(pitcher_trickery) -> float:
    """Reduction is a number from -1 to 0 (for a 1 trick average pitch) to 3 (maximum 2 trick)
    It directly counters batter power."""
    reduction_with_offset = pitcher_trickery * 2 + REDUCTION_OFFSET  # can be negative
    base_reduction = reduction_with_offset * rand()
    scaled_reduction = base_reduction * REDUCTION_FROM_TRICKERY
    return scaled_reduction


class Pitch(Update):
    # TODO: fuzz more than just location values?
    """
    Represents an actual pitch. has four key stats:
    location: where the pitch is, from 0 +, where 0 is right over the plate
    obscurity: how hard the pitch is to read, from 0 to 2-ish
    difficulty: how hard the pitch is to hit, from 0 +
    reduction: how much successful hits are reduced
    """
    def __init__(
            self,
            pitcher: Player,
            target: float,
            location: float,
            strike: bool,
            obscurity: float,
            difficulty: float,
            reduction: float
    ):

        self.target = target
        self.location = location
        self.strike = strike
        self.obscurity = obscurity
        self.difficulty = difficulty
        self.reduction = reduction

        super().__init__(self.description_string(pitcher))

    def description_string(self, pitcher: Player):
        if self.location > 1.6:
            loc_text = "to the wide outside"
        elif self.location > 1.2:
            loc_text = "to the far outside"
        elif self.location > 0.8:
            loc_text = "right on the edge"
        elif self.location > 0.4:
            loc_text = "to the near outside"
        elif self.location > -0.4:
            loc_text = "straight down the middle"
        elif self.location > -1:
            loc_text = "to the near inside"
        else:
            loc_text = "to the far inside"

        text_obscurity = pitcher[s.trickery] * rand()
        if text_obscurity > 1.5:
            pitch_text = "screwball"
        elif text_obscurity > 1:
            pitch_text = "curveball"
        elif text_obscurity > 0.8:
            pitch_text = "changeup"
        elif text_obscurity > 0.6:
            pitch_text = "slider"
        elif text_obscurity > 0.5:
            pitch_text = "cutter"
        elif text_obscurity > 0.3:
            pitch_text = "four seam fastball"
        else:
            pitch_text = "two seam fastball"

        text_force = normal(pitcher[s.force] * 20 + 70, 10)

        return f"{text_force:.0f} mph {pitch_text} {loc_text}."

    def __str__(self):
        strike_text = "Strike" if self.strike else "Ball"
        return (f"{strike_text}: loc {self.location:.2f} call {self.target:.2f} obs {self.obscurity:.2f} "
                f"dif {self.difficulty:.2f} red {self.reduction:.2f}")

    def __eq__(self, other):
        return (
            self.difficulty == other.difficulty
            and self.obscurity == other.obscurity
            and self.location == other.location
            and self.reduction == other.reduction
            and self.strike == other.strike
        )


def build_pitch(state: GameState) -> Pitch:
    defense = state.defense()
    catcher = defense['catcher']
    pitcher = defense['pitcher']

    target = decide_call(state, catcher, pitcher)
    location = roll_location(target, pitcher[s.accuracy])
    strike = check_strike(location, catcher[s.calling])
    obscurity = calc_obscurity(location, pitcher[s.trickery])
    difficulty = calc_difficulty(location, pitcher[s.force])
    reduction = roll_reduction(pitcher[s.trickery])

    return Pitch(pitcher, target, location, strike, obscurity, difficulty, reduction)


class PitchManager(Manager):
    def start(self):
        self.messenger.subscribe(self.do_pitch, GameTags.state_ticks)

    def stop(self):
        self.messenger.unsubscribe(self.do_pitch, GameTags.state_ticks)

    def do_pitch(self):
        pitch = build_pitch(self.state)
        self.messenger.queue(pitch, [GameTags.pitch, GameTags.game_updates])

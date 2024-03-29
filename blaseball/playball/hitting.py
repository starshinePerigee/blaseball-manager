"""
Controls a player's pre-hit decisions as well as their actual swing attempt.
"""

from numpy.random import normal, rand

from blaseball.playball.gamestate import GameState, GameTags
from blaseball.playball.pitching import Pitch
from blaseball.stats.players import Player
from blaseball.playball.event import Update
from blaseball.stats import stats as s
from blaseball.util.messenger import Messenger
from blaseball.playball.manager import Manager


# Hit Intent:


BONUS_BALLS = 0.5  # extra ball used when determining desperation
DESPERATION_MIDPOINT = 0.85  # balls under for 100% desperation
DESPERATION_FLOOR = 0.2  # lowest amount of desperation possible


def decide_hit_effect(game: GameState):
    pass


def calc_desperation(balls, strikes, ball_count, strike_count) -> float:
    """Desperation is a measure of how much a player wants to swing vs take.
    It is a unitless number from 0 to 1.14, with 1 being "average"
    Note that there is no difference between one and two strikes."""
    total_balls = balls + BONUS_BALLS
    ball_ratio = total_balls / (ball_count + BONUS_BALLS - 1)
    strike_ratio = strikes / (strike_count - 1)
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
    base_quality = normal(loc=(net_contact + FOUL_BIAS) * NET_CONTACT_FACTOR, scale=1)
    return base_quality


class Swing(Update):
    """A player's swing, from decision up to hit quality"""
    def __init__(
            self,
            desperation: float,
            read_chance: float,
            swing_chance: float,
            did_swing: bool,
            thrown_strike: bool,
            net_contact: float,
            hit_quality: float,
    ):
        super().__init__()

        self.desperation = desperation
        self.read_chance = read_chance
        self.swing_chance = swing_chance
        self.did_swing = did_swing
        self.net_contact = net_contact
        self.hit_quality = hit_quality

        self.strike = False
        self.ball = False
        self.hit = False

        if did_swing:
            if hit_quality < 0:
                self.strike = True
                self.text = "Strike, swinging."
            else:
                self.hit = True
                self.text = "It's a hit!"
        else:
            if thrown_strike:
                self.strike = True
                self.text = "Strike, looking."
            else:
                self.ball = True
                self.text = "Ball."

    def __bool__(self):
        return self.did_swing

    def __str__(self):
        text = ""
        if not self.did_swing:
            text += "Strike, looking" if self.strike else "Ball"
            text += f" with swing odds {self.swing_chance*100:.01f}%"
        else:
            if self.hit:
                text += "Hit ball"
            else:
                text += "Swung strike"
            text += f" with quality {self.hit_quality:.3f}"
        text += f" from desperation {self.desperation:.02f}"
        return text


def build_swing(state: GameState, pitch: Pitch) -> Swing:
    batter = state.batter()

    desperation = calc_desperation(state.balls, state.strikes, state.rules.ball_count, state.rules.strike_count)
    read_chance = calc_read_chance(pitch.obscurity, batter[s.discipline])
    swing_chance = calc_swing_chance(read_chance, desperation, pitch.strike)
    did_swing = roll_for_swing_decision(swing_chance)

    if did_swing:
        net_contact = batter[s.contact] - pitch.difficulty
        hit_quality = roll_hit_quality(net_contact)
    else:
        net_contact = 0
        hit_quality = 0

    swing = Swing(
        desperation=desperation,
        read_chance=read_chance,
        swing_chance=swing_chance,
        did_swing=did_swing,
        thrown_strike=pitch.strike,
        net_contact=net_contact,
        hit_quality=hit_quality
    )

    return swing


class SwingManager(Manager):
    def start(self):
        self.messenger.subscribe(self.do_swing, GameTags.pitch)
        self.messenger.subscribe(self.update_score, GameTags.swing)

    def stop(self):
        self.messenger.unsubscribe(self.do_swing, GameTags.pitch)
        self.messenger.unsubscribe(self.update_score, GameTags.swing)

    def do_swing(self, pitch: Pitch):
        swing = build_swing(self.state, pitch)

        self.messenger.queue(self, [GameTags.swing])

    def update_score(self, swing: Swing):
        # this is separate to keep its position in the event queue
        if swing.strike:
            self.messenger.send(swing.did_swing, GameTags.strike)
        elif swing.ball:
            self.messenger.send(tags=GameTags.ball)
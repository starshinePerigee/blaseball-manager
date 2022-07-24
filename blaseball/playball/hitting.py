"""
Controls a player's pre-hit decisions as well as their actual swing attempt.
"""

from blaseball.playball.gamestate import GameState
from blaseball.playball.pitching import Pitch
from blaseball.stats.players import Player
from blaseball.playball.event import Update

from numpy.random import normal, rand


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
FOUL_HIT_QUALITY_THRESHOLD = 1


def roll_hit_quality(net_contact) -> float:
    """Roll for hit quality. 1 is a good hit, 0-1 is a foul"""
    base_quality = normal(loc=(net_contact + FOUL_BIAS) * NET_CONTACT_FACTOR, scale=1)
    return base_quality - FOUL_HIT_QUALITY_THRESHOLD


class Swing(Update):
    """A player's swing, from decision up to hit quality"""
    def __init__(self, game: GameState, pitch: Pitch, batter: Player):
        super().__init__()

        self.desperation = calc_desperation(game.balls, game.strikes, game.rules.ball_count, game.rules.strike_count)
        self.read_chance = calc_read_chance(pitch.obscurity, batter['discipline'])
        self.swing_chance = calc_swing_chance(self.read_chance, self.desperation, pitch.strike)
        self.did_swing = roll_for_swing_decision(self.swing_chance)

        self.strike = False
        self.ball = False
        self.foul = False
        self.hit = False

        # this could probably use cleaning up
        if self.did_swing:
            self.net_contact = batter['contact'] - pitch.difficulty
            self.hit_quality = roll_hit_quality(self.net_contact)
            if self.hit_quality < -FOUL_HIT_QUALITY_THRESHOLD:
                self.strike = True
                self.text = "Strike, swinging."
            elif self.hit_quality < 0:
                self.foul = True
                self.text = "Foul ball."
            else:
                self.hit = True
                self.text = "It's a hit!"
        else:
            self.net_contact = 0
            self.hit_quality = 0
            self.strike = pitch.strike
            if self.strike:
                self.ball = False
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
            elif self.foul:
                text += "Foul ball"
            else:
                text += "Swung strike"
            text += f" with quality {self.hit_quality:.3f}"
        text += f" from desperation {self.desperation:.02f}"
        return text


if __name__ == "__main__":
    from blaseball.stats import stats

    from blaseball.util import quickteams
    g = quickteams.game_state

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
            w = Swing(g, p, test_batter)
            print(w)
            print(w.text)
        print("")

    print("")
    g.strikes = 2
    do_swing()

    g.strikes = 0
    do_swing()

    g.balls = 3
    do_swing()



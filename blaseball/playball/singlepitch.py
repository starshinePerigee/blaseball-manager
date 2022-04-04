"""
This is a single pitch in a game, from the "commit to pitch" (no actions) to the result

The result can be a live ball, or an updated game state.
"""

from blaseball.playball.ballgame import BallGame, Ball
from blaseball.stats.players import Player
from data import gameconstants

from scipy.stats import norm
from numpy.random import normal, rand
from math import tanh

ONE_STDV_AT_ONE_ACCURACY = 0.7  # how wide one standard deviation is at one accuracy
ONE_STDV_AT_ZERO_ACCURACY = 1  # how wide one standard deviation is at zero accuracy

accuracy_stdv_slope = ONE_STDV_AT_ONE_ACCURACY - ONE_STDV_AT_ZERO_ACCURACY
accuracy_stdv_intercept = ONE_STDV_AT_ZERO_ACCURACY


class HitIntent:
    """
    A class that represents the desire of the batter before the pitch is thrown.

    Currently has a placeholder for effects, and desperation.
    """

    def __init__(self, game: 'BallGame'):
        self.game = game
        self.decide_effect()
        self.desperation = self.get_desperation()

    def decide_effect(self):
        pass

    BONUS_BALLS = 0.5  # extra ball used when determining desperation
    DESPERATION_MIDPOINT = 0.85  # balls under for 100% desperation
    DESPERATION_FLOOR = 0.2  # lowest amount of desperation possible

    def get_desperation(self) -> float:
        total_balls = self.game.balls + HitIntent.BONUS_BALLS
        ball_ratio = total_balls / (gameconstants.BALL_COUNT + HitIntent.BONUS_BALLS - 1)
        strike_ratio = self.game.strikes / (gameconstants.STRIKE_COUNT - 1)
        balls_over = ball_ratio - strike_ratio
        if balls_over < 0:
            balls_over = 0
        desperation_base = (1 - balls_over) / HitIntent.DESPERATION_MIDPOINT
        desperation_scaled = desperation_base * (1-HitIntent.DESPERATION_FLOOR) + HitIntent.DESPERATION_FLOOR
        return desperation_scaled

    def __str__(self):
        return f"hit intent: desperation {self.desperation:.2f}"


class PitchIntent:
    """
    Determines the pitcher's intent, before they throw the ball, based on pitcher, catcher, and game state.
    """
    def __init__(self, game: 'BallGame'):
        self.game = game

        self.pitcher = self.game.defense()['pitcher']
        self.catcher = self.game.defense()['catcher']
        self.batter = self.game.batter()
        self.next_at_bat = self.game.batter(1)

        self.decide_effect()
        self.base_calling_modifier = 0
        self.ideal_strike_percent = 0
        self.target_location = self.decide_target_location()

    def decide_effect(self):
        pass

    STRIKE_PERCENT_BASE = 0.6  # what percentage of pitches would be strikes if calling was 0
    STRIKE_PERCENT_VERTICAL_SCALE = 0.4  # how much calling can move the strike percentage
    STRIKE_PERCENT_WIDTH = 20  # higher values make a steeper slope of the tanh function for strike percent

    def decide_target_location(self) -> float:
        calling_modifier = self.calling_modifier()
        self.base_calling_modifier = calling_modifier

        calling = self.catcher['calling']
        calling_modifier *= min(1, calling)

        tan_mod = tanh(calling_modifier/PitchIntent.STRIKE_PERCENT_WIDTH)
        scaled_mod = tan_mod * PitchIntent.STRIKE_PERCENT_VERTICAL_SCALE
        strike_percent = PitchIntent.STRIKE_PERCENT_BASE - scaled_mod
        self.ideal_strike_percent = strike_percent

        pitcher_stdev = accuracy_stdv_slope * self.pitcher['accuracy'] + accuracy_stdv_intercept
        strike_z = norm.ppf(strike_percent)
        strike_position = strike_z * pitcher_stdev
        called_location = max(0, 1-strike_position)
        return called_location

    WEIGHTS = {
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

    def calling_modifier(self) -> float:
        """
        The ideal shift towards or away from the plate including catcher effects.
        This is a unitless number and can be positive (away from the strike zone)
        or negative (towards the strike zone)
        """
        calling_modifier = 0

        # evaluate current count:
        ball_ratio = self.game.balls / (gameconstants.BALL_COUNT - 1)
        strike_ratio = self.game.strikes / (gameconstants.STRIKE_COUNT - 1)
        if ball_ratio == 0 and strike_ratio == 0:
            count_effect = PitchIntent.FIRST_PITCH_BIAS
        else:
            count_effect = strike_ratio - ball_ratio
        if self.game.balls == gameconstants.BALL_COUNT - 1:
            count_effect += -0.2  # bonus hyper modifier
        count_effect *= PitchIntent.WEIGHTS['count']
        calling_modifier += count_effect

        # evaluate hitter discipline bias
        # the more disciplined a hitter is, the more strikes to throw and thus the more negative
        # the more powerful a hitter is, the more balls to throw and thus more positive
        discipline_bias_effect = self.batter['power'] - self.batter['discipline']
        discipline_bias_effect *= PitchIntent.WEIGHTS['discipline_bias']

        # calculate runners to walk vs. runners to bat in
        bases_occupied = [i is not None for i in self.game.bases]
        runner_in_scoring_position = bases_occupied[gameconstants.NUMBER_OF_BASES-1]
        runners_to_walk = 0
        for base in bases_occupied:
            if base:
                runners_to_walk += 1
            else:
                break
        if runners_to_walk != gameconstants.NUMBER_OF_BASES and runner_in_scoring_position:
            # there is a player in socring position who won't score on a walk:
            risp_effect = PitchIntent.RUNNER_IN_SCORING_POSITION_MODIFIER
        else:
            risp_effect = 0
        runners_to_walk_effect = runners_to_walk ** PitchIntent.RUNNERS_TO_WALK_FACTOR
        runners_to_walk_effect /= PitchIntent.RUNNERS_TO_WALK_MODIFIER
        bases_loaded_effect = runners_to_walk_effect + risp_effect
        bases_loaded_effect *= PitchIntent.WEIGHTS['bases_loaded']
        calling_modifier += bases_loaded_effect

        # calculate effect from current number of outs
        median_out = (gameconstants.OUTS_COUNT - 1) / 2  # 1 for three outs, 1.5 for four
        outs_effect = self.game.outs - median_out
        outs_effect *= PitchIntent.WEIGHTS['outs_number']
        calling_modifier += outs_effect

        # calculate effect of current hitter vs next hitter difficulty
        cvn_hitter = self.batter['total offense'] - self.next_at_bat['total offense']
        cvn_hitter *= PitchIntent.WEIGHTS['current_v_next_hitter']
        calling_modifier += cvn_hitter

        return calling_modifier

    def __str__(self):
        return f"pitch intent: target {self.target_location:.2f} modifier {self.base_calling_modifier:.1f} " \
               f"strike {self.ideal_strike_percent*100:.0f}%"


class Pitch:
    """
    Represents an actual pitch. has four key stats:
    location: where the pitch is, from 0 +, where 0 is right over the plate
    obscurity: how hard the pitch is to read, from 0 to 2-ish
    difficulty: how hard the pitch is to hit, from 0 +
    reduction: how much successful hits are reduced
    """
    def __init__(self, pitch_intent: PitchIntent, pitcher: Player, catcher: Player):
        self.intent = pitch_intent
        self.pitcher = pitcher
        self.catcher = catcher

        self.location = 0
        self.obscurity = 0
        self.difficulty = 0
        self.reduction = 0
        self.strike = False

    def pitch(self):
        self.location = self.roll_location()
        self.strike = self.check_strike()
        self.obscurity = self.get_obscurity()
        self.difficulty = self.get_difficulty()
        self.reduction = self.get_reduction()

    def roll_location(self) -> float:
        pitcher_stdev = accuracy_stdv_slope * self.pitcher['accuracy'] + accuracy_stdv_intercept
        target_location = self.intent.target_location

        return normal(loc=target_location, scale=pitcher_stdev)

    FRAMING_FACTOR = 0.1  # how much exceptionally good catchers can bias the upires

    def check_strike(self):
        catcher_mod = max(0.0, self.catcher['calling'] - 1) * Pitch.FRAMING_FACTOR
        return abs(self.location) <= 1 + catcher_mod

    MAX_BASE_OBSCURITY = 10  # maximum amount of obscurity you can get via location (at 1.0)
    OBSCURITY_DISTANCE_SCALE = 5  # magic factor to determine how distance scales,
    # lower is higher obscurity for the same distance.
    TRICKINESS_FACTOR = 0.5  # amount of obscurity added to every pitch for 1 trickiness

    def get_obscurity(self) -> float:
        closeness_scale = 1 / Pitch.OBSCURITY_DISTANCE_SCALE
        far_out = abs(self.location - 1)
        location_obscurity = closeness_scale / (far_out + (1 / Pitch.MAX_BASE_OBSCURITY))
        trick_obscurity = self.pitcher['trickery'] * Pitch.TRICKINESS_FACTOR
        return location_obscurity + trick_obscurity

    DIFFICULTY_DISTANCE_FACTOR = 1.5  # EXPONENT for how being far out affects difficulty
    STRIKE_ZONE_DIFFICULTY_CENTER = 0.5  # the point at which you start gaining difficulty for being far out
    FORCE_FACTOR = 1  # how much a pitcher's force affects difficulty

    def get_difficulty(self) -> float:
        force_difficulty = Pitch.FORCE_FACTOR * self.pitcher['force']
        location_base = max(0.0, self.location - Pitch.STRIKE_ZONE_DIFFICULTY_CENTER)
        location_difficulty = location_base ** Pitch.DIFFICULTY_DISTANCE_FACTOR
        return force_difficulty + location_difficulty

    REDUCTION_FACTOR = 0.1  # how much low force affects reduction

    def get_reduction(self) -> float:
        reduction_base = Pitch.REDUCTION_FACTOR * (1 - self.pitcher['force'])
        return max(0.0, reduction_base)

    def __str__(self):
        strike_text = "Strike" if self.strike else "Ball"
        return f"{strike_text}: loc {self.location:.2f} obs {self.obscurity:.2f} " \
               f"dif {self.difficulty:.2f} red {self.reduction:.2f}"


class SwingDecision:
    """
    Determines if a batter wants to swing for a pitch.
    """
    def __init__(self, pitch: Pitch, hit_intent: HitIntent, batter: Player):
        self.pitch = pitch
        self.intent = hit_intent
        self.batter = batter
        self.read_chance = self.calculate_read_chance()
        self.swing_chance = self.calculate_swing_chance()
        self.swing_roll = -1
        self.swinging = self.decide_swing()

    DISCIPLINE_REDUCTION_AT_ONE = 0.5  # how much obscurity is reduced when you have a 1 in discipline
    discipline_reduction_factor = -DISCIPLINE_REDUCTION_AT_ONE/(DISCIPLINE_REDUCTION_AT_ONE-1)
    # DRF is equal to 1 when DRA1 is 0.5, but we need this math to get a nice curve with 1 at 0

    def calculate_read_chance(self) -> float:
        # this is equal to 1 when DR is 0.5. it's algebra, trust me:
        drf = SwingDecision.discipline_reduction_factor
        discipline_modifier = drf / (drf + self.batter['discipline'])
        effective_obscurity = self.pitch.obscurity * discipline_modifier
        return 1 / (1 + effective_obscurity)

    def calculate_swing_chance(self) -> float:
        strike_chance = self.read_chance if self.pitch.strike else (1 - self.read_chance)
        return strike_chance * self.intent.desperation

    def decide_swing(self) -> bool:
        self.swing_roll = rand()
        return self.swing_roll < self.swing_chance

    def __str__(self):
        swing_text = "Swing" if self.swinging else "Look"
        return f"{swing_text}: read {self.read_chance*100:.0f}% swing {self.swing_chance*100:.0f}% " \
               f"roll {self.swing_roll:.2f}"


class Swing:
    """
    A players swing, from decision, through hit quality.
    """
    def __init__(self):
        pass

    def swing(self) -> Ball:
        return Ball()


class PitchHit:
    """
    A single pitch, from after the action timing window, to the result of the pitch.
    This is carried back to the game as a Ball.


    """
    def __init__(self, game: BallGame):
        self.game = game

        self.hit_intent = HitIntent(self.game)
        self.pitch_intent = PitchIntent(self.game)
        self.pitch = Pitch(
            self.pitch_intent,
            self.game.defense()['pitcher'],
            self.game.defense()['catcher']
        )
        self.pitch.pitch()
        self.swing_decision = SwingDecision(self.pitch, self.hit_intent, self.game.batter())
        if self.swing_decision.swinging:
            self.swing = Swing()
            self.result = self.swing.swing()
        else:
            self.result = Ball()


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
    g.balls = 1

    test_pitcher = g.defense()['pitcher']
    print(f"Pitcher: {test_pitcher}")
    for s in stats.all_stats['rating']:
        if s.category == 'pitching':
            print(f"{s}: {test_pitcher._to_stars(test_pitcher[s.name])}")
    test_catcher = g.defense()['catcher']
    print(f"Catcher: {test_catcher}")
    print(f"Calling: {test_catcher._to_stars(test_catcher['calling'])}")
    print("")
    test_batter = g.batter()
    print(f"Batter: {test_batter}")
    for s in stats.all_stats['rating']:
        if s.category == 'batting':
            print(f"{s}: {test_batter._to_stars(test_batter[s.name])}")

    def print_result(strike, swing):
        if strike and swing:
            print("Good swing!")
        elif strike:
            print("Strike!")
        elif swing:
            print("Reached on a ball!")
        else:
            print("Ball!")

    print("\r\n* * * * * \r\n\r\n")
    p = PitchHit(g)
    print(p.hit_intent)
    print(p.pitch_intent)
    print(p.pitch)
    print(p.swing_decision)
    print_result(p.pitch.strike, p.swing_decision.swinging)
    print("")

    for _ in range(0, 9):
        p = PitchHit(g)
        print(p.pitch)
        print(p.swing_decision)
        print_result(p.pitch.strike, p.swing_decision.swinging)
        print("")

    # def run_test(pitches):
    #     p = Pitch(g)
    #     print(p.pitch_intent)
    #
    #     strikes = 0
    #     location = 0
    #     obscurity = 0
    #     difficulty = 0
    #     for _ in range(0, pitches):
    #         p = Pitch(g)
    #         strikes += int(p.pitch.strike)
    #         location += p.pitch.location
    #         obscurity += p.pitch.obscurity
    #         difficulty += p.pitch.difficulty
    #     strike_rate = strikes / pitches * 100
    #     location /= pitches
    #     obscurity /= pitches
    #     difficulty /= pitches
    #     print(f"Strike rate: {strike_rate:.0f}%, ave location: {location:.2f}, "
    #           f"ave obscurity: {obscurity:.2f}, ave difficulty {difficulty:.2f}.")
    #
    # PITCHES = 1000
    #
    # g.balls = 3
    #
    # test_pitcher['accuracy'] = 0.1
    # test_catcher['calling'] = 0.1
    # print("min accuracy, min calling")
    # run_test(PITCHES)
    #
    # print("max accuracy, max calling")
    # test_pitcher['accuracy'] = 1
    # test_catcher['calling'] = 1
    # run_test(PITCHES)
    #
    # print('min accuracy, max calling')
    # test_pitcher['accuracy'] = 0.1
    # run_test(PITCHES)
    #
    # test_pitcher['accuracy'] = 1
    #
    # pi = PitchIntent(g)
    # pi.target_location = 0
    # t = pitch(pi, test_pitcher, test_catcher)
    #
    # strikes = 0
    # location = 0
    # obscurity = 0
    # difficulty = 0
    # for _ in range(0, 1000):
    #     t.pitch()
    #     strikes += int(t.strike)
    #     location += t.location
    #     obscurity += t.obscurity
    #     difficulty += t.difficulty
    # strike_rate = strikes / 1000 * 100
    # location /= 1000
    # obscurity /= 1000
    # difficulty /= 1000
    # print(f"Strike rate: {strike_rate:.0f}%, ave location: {location:.2f}, "
    #       f"ave obscurity: {obscurity:.2f}, ave difficulty {difficulty:.2f}.")

    print("x")

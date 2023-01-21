import pytest
import statistics

from blaseball.playball.gamestate import GameTags
from blaseball.playball import hitting, pitching
from blaseball.stats import stats as s


class TestHitting:

    DESPERATION_UPPER_BOUND = 1.4
    DESPERATION_LOWER_BOUND = 0

    @pytest.mark.parametrize(
        "count, limit, absolute",
        #  using absolute as a parameter is kind of a jank idea, this should have been two tests. see below.
        [
            ((0, 0), (1, 1.1), True),
            ((1, 0), (0, 1), True),
            ((0, 0), (1, 0), False),
            ((1, 0), (2, 0), False),
            ((2, 0), (3, 0), False),
            ((3, 1), (3, 0), False),
            ((3, 2), (1, 2), True),
            ((0, 1), (1, 2), True),
        ]
    )
    def test_calc_desperation(self, count, limit, absolute):
        # first pitch should be a strike: mlb first pitch strike rate is 58%
        desperation = hitting.calc_desperation(count[0], count[1], 4, 3)
        if absolute:
            assert limit[0] < desperation < limit[1]
        else:
            limit = hitting.calc_desperation(limit[0], limit[1], 4, 3)
            assert desperation > limit
            assert TestHitting.DESPERATION_LOWER_BOUND < limit < TestHitting.DESPERATION_UPPER_BOUND
        assert TestHitting.DESPERATION_LOWER_BOUND < desperation < TestHitting.DESPERATION_UPPER_BOUND

    def test_calc_desperation_strikes(self):
        assert hitting.calc_desperation(0, 2, 4, 3) == pytest.approx(hitting.calc_desperation(0, 1, 4, 3))

    def test_print_calc_desperation(self):
        print(" ~Desperation~")
        print(f"0-0: {hitting.calc_desperation(0, 0, 4, 3)}")
        print(f"Count max positive: {hitting.calc_desperation(0, 2, 4, 3)}")
        print(f"Count max negative: {hitting.calc_desperation(3, 0, 4, 3)}")
        print(f"3-2: {hitting.calc_desperation(3, 2, 4, 3)}")

    @pytest.mark.parametrize(
        "greater, lesser",
        [
            ((0, 0), (1, 0)),
            ((1, 1), (1, 0))
        ]
    )
    def test_calc_read_chance_comparison(self, greater, lesser):
        assert hitting.calc_read_chance(greater[0], greater[1]) > hitting.calc_read_chance(lesser[0], lesser[1])

    @pytest.mark.parametrize(
        "obscurity, discipline, low, high",
        [
            (0, 1, 0.95, 1),
            (3, 0, 0, 0.5),  # if you're bad enough and if the pitcher is good enough you do worse than just guessing.
            (1, 1, 0.6, 0.8)  # MLB odds are about 70% for reading the average pitch
        ]
    )
    def test_calc_read_chance_absolute(self, obscurity, discipline, low, high):
        # obscurity ranges from 0 to 3, but average is between 0.5 and 1
        assert low <= hitting.calc_read_chance(obscurity, discipline) <= high

    def test_print_calc_read_chance(self):
        print(" ~Read Chance~")
        obscurities = [0, 0.5, 1, 3]
        disciplines = [0, 0.5, 1, 2]
        print(f"Read chance vs obscurity ({disciplines} discipline)")
        for obscurity in obscurities:
            print_str = f"* {obscurity:0.1f} *  "
            for discipline in disciplines:
                print_str += f"{hitting.calc_read_chance(obscurity, discipline)*100: >3.0f}%  "
            print(print_str)

    @pytest.mark.parametrize('trickery', [0, 0.5, 1, 2])
    def test_print_trickery_vs_discipline(self, trickery):
        print(f" ~Discipline VS {trickery:0.1f} Trickery Across the Plate~")

        disciplines = [0, 0.5, 1, 2]

        print(f"Read chance at {trickery:0.1f} trickery, ({disciplines} discipline)")
        for i in range(0, 11):
            loc = 0.2 * i
            print_str = f"* {loc:0.1f} *  "
            for discipline in disciplines:
                obscurity = pitching.calc_obscurity(loc, trickery)
                read_chance = hitting.calc_read_chance(obscurity, discipline)
                print_str += f"{read_chance*100: >3.0f}%  "
            print(print_str)

    @pytest.mark.parametrize('swing_percent', [0, 0.1, 0.5, 0.9, 1])
    def test_roll_for_swing_decision(self, swing_percent, patcher):
        patcher.patch_rand('blaseball.playball.hitting.rand')
        swings = [hitting.roll_for_swing_decision(swing_percent) for __ in patcher]
        actual_percent = sum(swings) / 100
        assert actual_percent == pytest.approx(swing_percent, abs=0.04)  # rand_across_range includes outliers.

    # hit quality uses net contact: contact - pitch difficulty.
    # 0 force difficulty is about 0.3, 1 force difficulty is about 1.35.
    # net contact is thus 2 to about -3 for a far, far outside the plate 2 force.
    # 2 - (-2) is a wide range and 1 - (-1) is average.

    net_contacts = [-10, -4, -3, -1, -0.5, 0, 0.5, 0.8, 1, 2]
    net_contacts.sort()

    @pytest.mark.parametrize('net_contact, previous_contact', zip(net_contacts[1:], net_contacts[:-1]))
    def test_roll_hit_quality(self, net_contact, previous_contact, patcher):
        patcher.patch_normal('blaseball.playball.hitting.normal')
        qualities = [hitting.roll_hit_quality(net_contact) for i in patcher]
        print(f" ~Hit Quality~")
        print(f"Net contact: {net_contact:0.1f}")
        average_hit_quality = statistics.mean(qualities)

        average_previous_quality = statistics.mean([hitting.roll_hit_quality(previous_contact) for i in patcher])
        assert average_hit_quality > average_previous_quality

        print(f"Average hit quality: {average_hit_quality:.2f}")

        min_hit_quality = min(qualities)
        max_hit_quality = max(qualities)

        assert min_hit_quality < 0
        assert max_hit_quality > 0
        print(f"Min: {min_hit_quality:.2f}, Max: {max_hit_quality:.2f}")

    def test_print_roll_hit_quality(self, patcher):
        patcher.patch_normal('blaseball.playball.hitting.normal')
        for net_contact in TestHitting.net_contacts[1:]:
            qualities = [hitting.roll_hit_quality(net_contact) for __ in patcher]

            strikes = sum([x <= 0 for x in qualities])
            fouls = sum([0 < x < 1 for x in qualities])
            fairs = sum([x >= 1 for x in qualities])
            print(f"* {net_contact:+0.1f} *  {strikes: >3} strikes, {fouls: >3} fouls, {fairs: >3} fair hits.")

    @pytest.mark.xfail
    def test_foul_rate(self, patcher):
        patcher.patch_normal('blaseball.playball.hitting.normal')
        qualities = [hitting.roll_hit_quality(-0.3) for __ in patcher]
        strikes = sum([x <= 0 for x in qualities])
        fouls = sum([0 < x < 1 for x in qualities])
        fairs = sum([x >= 1 for x in qualities])

        # MLB strike swinging percent: https://www.fantasypros.com/2020/02/sabermetrics-glossary-swinging-strike-rate/
        assert 10 < strikes < 20
        # foul percent: https://blogs.fangraphs.com/unpacking-the-impact-of-foul-balls-on-strikeouts/
        assert 25 < fouls < 50


class TestHitIntegrated:
    hit_parameters = {
        # "location, swing, quality, strike, ball, hit"
        'wide strike swinging': (1.2, True, -3, True, False, False),
        'narrow strike swinging': (0.8, True, -3, True, False, False),
        'narrow strike looking': (0.5, False, -1, True, False, False),
        'take ball': (1.2, False, 0, False, True, False),
        'clean hit': (-0.1, True, 2, False, False, True),
        'reach hit': (1.5, True, 0.1, False, False, True)
    }

    @pytest.mark.parametrize(
        "location, swing, quality, strike, ball, hit",
        hit_parameters.values(),
        ids=list(hit_parameters.keys())
    )
    def test_swing_results(
            self, patcher, gamestate_1, messenger_1, pitch_1,
            location, swing, quality, strike, ball, hit
    ):
        pitch_1.location = location
        pitch_1.strike = pitching.check_strike(location, 1)
        patcher.patch('blaseball.playball.hitting.roll_for_swing_decision', lambda swing_chance: swing)
        patcher.patch('blaseball.playball.hitting.roll_hit_quality', lambda net_contact: quality)

        swing = hitting.build_swing(gamestate_1, pitch_1)

        assert swing.strike == strike
        assert swing.ball == ball
        assert swing.hit == hit


class TestHitStats:
    # this goes in its own class because playerbase fixtures are class-scoped
    def test_swing_stats_tracking(self, gamestate_1, stats_monitor_1, patcher, messenger_1):
        # be aware that we're mocking for legibility - the rates seen in this test have no resemblance
        # to expected or desired rates.

        # hit_stats = ['strike rate', 'ball rate', 'foul rate', 'hit rate', 'pitch read chance']

        pitcher = gamestate_1.defense()['pitcher']
        batter = gamestate_1.batter()

        swingmanager = hitting.SwingManager(gamestate_1, messenger_1)

        locations = [0.5, 1.5]
        read_chances = [0, 1]
        swing_outcomes = [True, False, False]
        hit_qualities = [-3.5, -2.5, -1.5, -0.5, 0.5, 1.5]

        total_swings = 0
        for location in locations:
            for read_chance in read_chances:
                for did_swing in swing_outcomes:
                    for hit_quality in hit_qualities:
                        patcher.patch(
                            'blaseball.playball.hitting.calc_read_chance',
                            lambda obscurity, batter_discipline: read_chance
                        )
                        patcher.patch(
                            'blaseball.playball.hitting.roll_for_swing_decision',
                            lambda swing_chance: did_swing
                        )
                        patcher.patch(
                            'blaseball.playball.hitting.roll_hit_quality',
                            lambda net_contact: hit_quality
                        )

                        pitch = pitching.Pitch(
                            pitcher=pitcher,
                            target=location,
                            location=location,
                            strike=(location > 1),
                            obscurity=1,
                            difficulty=1,
                            reduction=1
                        )

                        messenger_1.queue(pitch, GameTags.pitch)
                        total_swings += 1

        print(f"Total pitches simulated: {total_swings}")

        thrown_strike_rate = sum([location < 1 for location in locations]) / len(locations)
        swing_rate = sum(swing_outcomes) / len(swing_outcomes)
        strike_looking_rate = thrown_strike_rate * (1-swing_rate)
        hit_if_swing_rate = sum([hit_quality > 0 for hit_quality in hit_qualities]) / len(hit_qualities)
        strike_swinging_rate = hit_if_swing_rate * swing_rate
        assert batter[s.strike_rate] == pytest.approx(strike_looking_rate + strike_swinging_rate)

        ball_rate = (1 - thrown_strike_rate) * (1 - swing_rate)
        assert batter[s.ball_rate] == pytest.approx(ball_rate)

        assert batter[s.hit_rate] == pytest.approx(hit_if_swing_rate)

        swing_at_strike_rate = thrown_strike_rate * swing_rate
        read_correct_rate = swing_at_strike_rate + ball_rate
        assert batter[s.pitch_read_chance] == pytest.approx(read_correct_rate)

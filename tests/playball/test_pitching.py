import pytest
import statistics

from blaseball.stats import stats
from blaseball.playball import pitching


# note: this was written mostly avoiding parameterize, relying on comparisons instead. compare test_hitting
# for the parameterized variant.
# somewhat curious which one will hold up better.


class TestCallingModifiers:
    # reminder: calling mod is a unitless number and can be positive (away from the strike zone)
    # or negative (towards the strike zone)

    def test_calling_modifier_count(self):
        # first pitch should be a strike: mlb first pitch strike rate is 58%
        base_calling_modifier = pitching.calling_mod_from_count(0, 0)
        assert -5 < base_calling_modifier < 0

        assert pitching.calling_mod_from_count(0, 1) > 0
        assert pitching.calling_mod_from_count(0, 1) > base_calling_modifier
        assert pitching.calling_mod_from_count(0, 2) > pitching.calling_mod_from_count(0, 1)

        assert pitching.calling_mod_from_count(1, 0) < base_calling_modifier
        assert pitching.calling_mod_from_count(2, 0) < pitching.calling_mod_from_count(1, 0)
        assert pitching.calling_mod_from_count(3, 0) < pitching.calling_mod_from_count(2, 0)

        assert pitching.calling_mod_from_count(3, 0) < pitching.calling_mod_from_count(3, 1)

        assert -5 < pitching.calling_mod_from_count(3, 2) < 5

        print(" ~CM count~")
        print(f"First pitch: {base_calling_modifier}")
        print(f"Count max positive: {pitching.calling_mod_from_count(0, 2)}")
        print(f"Count max negative: {pitching.calling_mod_from_count(3, 0)}")
        print(f"Final pitch modfiier: {pitching.calling_mod_from_count(3, 2)}")

    def test_calling_modifier_discipline_bias(self):
        assert pitching.calling_mod_from_discipline_bias(1, 1) == 0
        assert pitching.calling_mod_from_discipline_bias(0, 1) < 0
        assert pitching.calling_mod_from_discipline_bias(1, 0) > 0

        print(" ~CM discipline bias~")
        print(f"Disipline bias max positive: {pitching.calling_mod_from_discipline_bias(1, 0)}")
        print(f"Discipline bias max negative: {pitching.calling_mod_from_discipline_bias(0, 1)}")

    def test_calling_modifier_runners(self):
        assert pitching.calling_mod_from_runners([False, False, False]) == 0
        # more on base means less walks:
        assert pitching.calling_mod_from_runners([True, False, False]) < 0
        assert (pitching.calling_mod_from_runners([True, True, False]) <
                pitching.calling_mod_from_runners([True, False, False]))

        # runner in scoring position means more walks:
        assert pitching.calling_mod_from_runners([False, False, True]) > 0

        assert (pitching.calling_mod_from_runners([False, False, True]) <
                pitching.calling_mod_from_runners([False, True, True]))

        print(" CM runners:")
        print(f"One on effect: {pitching.calling_mod_from_runners([True, False, False])}")
        print(f"RISP effect: {pitching.calling_mod_from_runners([False, False, True])}")
        print(f"bases loaded effect: {pitching.calling_mod_from_runners([True, True, True])}")

    def test_calling_modifier_outs(self):
        assert pitching.calling_mod_from_outs(1) == 0
        assert pitching.calling_mod_from_outs(2) > 0
        assert pitching.calling_mod_from_outs(0) < 0

        print(" ~CM outs~")
        print(f"No outs effect: {pitching.calling_mod_from_outs(0)}")
        print(f"Two outs effect: {pitching.calling_mod_from_outs(2)}")

    def test_caling_modifier_next_hitter(self, lineup_1):
        current = lineup_1['batter 1']
        on_deck = lineup_1['batter 2']
        current.set_all_stats(0)
        on_deck.set_all_stats(0)
        assert pitching.calling_mod_from_next_hitter(current, on_deck) == 0

        on_deck.set_all_stats(1)
        zero_v_one = pitching.calling_mod_from_next_hitter(current, on_deck)
        assert zero_v_one < 0
        one_v_zero = pitching.calling_mod_from_next_hitter(on_deck, current)
        assert one_v_zero > 0

        print(" ~CM next hitter~")
        print(f"Next hitter min effect: {zero_v_one}")
        print(f"Next hitter max effect: {one_v_zero}")

    def test_calc_calling_modifier(self, ballgame_1):
        # set baseline values:
        print(" ~total calling modifier~")
        ballgame_1.outs = 1
        current = ballgame_1.batter()
        on_deck = ballgame_1.batter(1)
        current.set_all_stats(1)
        on_deck.set_all_stats(1)

        first_pitch_mod = pitching.calc_calling_modifier(ballgame_1)
        base_first_pitch_mod = pitching.calling_mod_from_count(0, 0) * pitching.CALLING_WEIGHTS['count']
        assert first_pitch_mod == pytest.approx(base_first_pitch_mod, abs=1)
        print(f"First pitch modifier: {first_pitch_mod}")

        # max walks case
        ballgame_1.outs = 2
        on_deck.set_all_stats(0)
        ballgame_1.bases[3] = ballgame_1.batter(3)
        ballgame_1.bases[2] = ballgame_1.batter(4)
        ballgame_1.strikes = 2
        ballgame_1.balls = 0
        max_walks = pitching.calc_calling_modifier(ballgame_1)
        assert max_walks > 20
        print(f"Maximum walk bias: {max_walks}")

        # max strikes case
        ballgame_1.outs = 0
        on_deck.set_all_stats(1)
        current.set_all_stats(0)
        del ballgame_1.bases[3]
        ballgame_1.bases[1] = ballgame_1.batter(5)
        ballgame_1.strikes = 0
        ballgame_1.balls = 3
        max_strikes = pitching.calc_calling_modifier(ballgame_1)
        assert max_strikes < -20
        print(f"Maximum strike bias: {max_strikes}")


class TestCalling:
    def test_strike_percent(self):
        base_percent = pitching.calc_ideal_strike_percent(0)
        assert base_percent == pitching.STRIKE_PERCENT_BASE

        # make sure limits work
        assert pitching.calc_ideal_strike_percent(-1000) == pytest.approx(1)

        min_percent = abs(pitching.STRIKE_PERCENT_BASE - 0.5) * 2
        assert pitching.calc_ideal_strike_percent(1000) == pytest.approx(min_percent)

        assert pitching.calc_ideal_strike_percent(1) < base_percent
        assert pitching.calc_ideal_strike_percent(-1) > base_percent

        print(" ~overall calling~")
        print(f"Base strike percent: {base_percent}")

        for i in [-1000, -100, -10, -5, -3, -1, 0, 1, 3, 5, 10, 100, 1000]:
            print(f"Strike percent at {i:5d}: {pitching.calc_ideal_strike_percent(i)*100:0.3f}%")

    def test_target_location(self):
        assert pitching.calc_target_location(1, 1.0) == pytest.approx(0)
        assert pitching.calc_target_location(1, 0) > 2
        assert pitching.calc_target_location(1, 0.5) == pytest.approx(1)

        assert pitching.calc_target_location(0.5, 0.8) < pitching.calc_target_location(1, 0.8)
        assert pitching.calc_target_location(0.5, 0.2) > pitching.calc_target_location(1, 0.2)

    def test_decide_call(self, ballgame_1):
        catcher = ballgame_1.defense()['catcher']
        pitcher = ballgame_1.defense()['pitcher']

        catcher.set_all_stats(1)
        pitcher.set_all_stats(1)

        ballgame_1.outs = 1

        # should be an approximate strike
        assert pitching.decide_call(ballgame_1, catcher, pitcher) < 1

        ballgame_1.balls = 3
        pitcher['accuracy'] = 0.5
        # 3 balls on the count, aim dead center
        assert pitching.decide_call(ballgame_1, catcher, pitcher) == pytest.approx(0)

        ballgame_1.balls = 0
        ballgame_1.strikes = 2
        pitcher['accuracy'] = 1
        both_good = pitching.decide_call(ballgame_1, catcher, pitcher)
        pitcher['accuracy'] = 0.5
        bad_pitcher = pitching.decide_call(ballgame_1, catcher, pitcher)
        catcher['calling'] = 0.5
        both_bad = pitching.decide_call(ballgame_1, catcher, pitcher)
        pitcher['accuracy'] = 1
        bad_catcher = pitching.decide_call(ballgame_1, catcher, pitcher)

        assert both_good > 1
        # a bad catcher reduces overall effect, a good catcher also reduces overall effect
        assert both_good > bad_catcher  # -catcher
        assert both_good < bad_pitcher  # -pitcher
        assert bad_catcher < both_bad  # -pitcher
        assert bad_pitcher > both_bad  # -catcher


class TestPitching:
    def test_roll_location_local(self, monkeypatch):
        monkeypatch.setattr('blaseball.playball.pitching.normal', lambda loc=0, scale=1: 0.1 * scale + loc)
        assert pitching.roll_location(1, 1) == 1.07

    def test_roll_location(self, patcher):
        patcher.patch_normal('blaseball.playball.pitching.normal')
        locations = [pitching.roll_location(1, 1) for __ in patcher]
        assert statistics.mean(locations) == pytest.approx(1)

        deviations = [abs(x - 1) for x in locations]

        print(" ~pitch accuracy~")
        print(f"1 / 1mill pitch deviation: {max(deviations)}")
        print(f"Average pitch devation: {statistics.mean(deviations)}")

    def test_check_strike(self):
        assert not pitching.check_strike(1.01, 1)
        assert pitching.check_strike(1.05, 2)
        assert pitching.check_strike(0.99, 1)

    def test_calc_obscurity(self):
        assert pitching.calc_obscurity(0, 0) < 1
        assert pitching.calc_obscurity(0, 1) > pitching.calc_obscurity(0, 0.9)
        obsc_at_one = pitching.calc_obscurity(1, 1)
        assert obsc_at_one > pitching.calc_obscurity(1.1, 1)
        assert obsc_at_one > pitching.calc_obscurity(0.9, 1)
        assert pitching.calc_obscurity(10, 1) < 1
        assert pitching.calc_obscurity(-1, 1) < pitching.calc_obscurity(-.5, 1)
        assert pitching.calc_obscurity(-1, 1) < pitching.calc_obscurity(0, 1)

        print(" ~pitch obscurity~")
        print("Obscurity across the plate (0, 0.5, 1, 2 trickery)")
        for i in range(0, 11):
            loc = 0.2 * i
            print_str = f"* {loc:0.1f} *  "
            for trick in [0, 0.5, 1, 2]:
                print_str += f"{pitching.calc_obscurity(loc, trick):0.2f}  "
            print(print_str)

    def test_calc_difficulty(self):
        assert pitching.calc_difficulty(0.5, 1) < pitching.calc_difficulty(0.6, 1)
        assert pitching.calc_difficulty(2, 1) < pitching.calc_difficulty(2.1, 1)
        assert pitching.calc_difficulty(1, 1) > pitching.calc_difficulty(1, 0.9)
        assert pitching.calc_difficulty(1, 1) < 2
        assert pitching.calc_difficulty(0.7, 1) == pytest.approx(pitching.calc_difficulty(-0.7, 1))
        assert pitching.calc_difficulty(-1, 1) > pitching.calc_difficulty(-0.5, 1)

        print("Difficulty across the plate (0, 0.5, 1, 2 force)")
        for i in range(0, 11):
            loc = 0.2 * i
            print_str = f"* {loc:0.1f} *  "
            for force in [0, 0.5, 1, 2]:
                print_str += f"{pitching.calc_difficulty(loc, force):0.2f}  "
            print(print_str)

    @pytest.mark.parametrize('trickery', [0, 0.5, 1, 2])
    def test_roll_reduction(self, trickery, patcher):
        patcher.patch_normal('blaseball.playball.pitching.normal')

        reductions = [pitching.roll_reduction(trickery) for __ in patcher]
        reductions_minus_one = [pitching.roll_reduction(trickery - 0.1) for __ in patcher]

        assert statistics.mean(reductions) > statistics.mean(reductions_minus_one)
        print(" ~pitch reduction~")
        print(f"Reduction at {trickery:0.0f} trickery: {reductions[0]} to {reductions[-1]}, "
              f"mean {statistics.mean(reductions)}")


class TestPitchIntegrated:
    def test_pitch(self, ballgame_1, monkeypatch, patcher):
        ballgame_1.outs = 1
        catcher = ballgame_1.defense()['catcher']
        pitcher = ballgame_1.defense()['pitcher']
        print(" ~overall pitching~")

        called_locations = []
        difficulties = []
        obscurities = []
        reductions = []

        patcher.patch_normal('blaseball.playball.pitching.normal')

        # This *should be* an ideal candidate for pytest parameterization, but we need to compare each iteration
        # to each other to make sure trends go up. We could split this into two tests, but at that point you're
        # not really saving anything, are you?
        # In general, this failure mode is really common for almost all these tests. The parameters are arbitrary magic
        # numbers and we really only care that they trend in the right direction with the right proportionality.
        # once the ball is hit, we convert to real values (seconds, feet, etc) and then we can check for 'sanity'.
        # we do take a shot at parameterizing this in test_hitting.
        for stat in [0, 0.5, 1, 2]:
            catcher.reset_tracking()
            catcher.set_all_stats(stat)
            pitcher.reset_tracking()
            pitcher.set_all_stats(stat)

            monkeypatch.setattr(
                'blaseball.playball.pitching.roll_reduction',
                lambda pitcher_trickery: pitcher_trickery * pitching.REDUCTION_FROM_TRICKERY
            )

            pitches = [pitching.Pitch(ballgame_1, pitcher, catcher) for __ in patcher]

            assert catcher['total pitches called'] == 100
            assert pitcher['total pitches thrown'] == 100

            called_location_ave = statistics.mean([x.target for x in pitches])
            difficulty_ave = statistics.mean([x.difficulty for x in pitches])
            obscurity_ave = statistics.mean([x.obscurity for x in pitches])
            reduction_ave = statistics.mean([x.reduction for x in pitches])

            for result, group, tracked in zip(
                [called_location_ave, difficulty_ave, obscurity_ave, reduction_ave],
                [called_locations, difficulties, obscurities, reductions],
                ['average called location', 'average pitch difficulty', 'average pitch obscurity', 'average reduction']
            ):

                if tracked == 'average called location':
                    assert catcher[tracked] == pytest.approx(result)
                else:
                    assert pitcher[tracked] == pytest.approx(result)
                group += [result]

            print(f"\r\nAll stats at {stat:0.1f}")
            for tracked in stats.pitch_stats:
                print(f"{tracked.title()}: {pitcher[tracked]:0.2f}")

        for group in [difficulties, obscurities, reductions]:
            assert sorted(group) == group

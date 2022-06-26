import pytest

from blaseball.playball import fielding, liveball

from statistics import mean


class TestCatch:
    @pytest.mark.parametrize(
        "distance, reach, min_odds, max_odds",
        [
            (0, 1, 1, 1),
            (fielding.REACH_MINIMUM_DISTANCE, 0, 1, 1),
            (fielding.REACH_MAXIMUM_DISTANCE - 1, 1, 0, 0.1),
            (fielding.REACH_MAXIMUM_DISTANCE, 1, 0, 0),
            (fielding.REACH_MAXIMUM_DISTANCE, 1.01, 0.001, 0.1),
            (fielding.REACH_MAXIMUM_DISTANCE, 2, 0.4, 0.6)
        ]
    )
    def test_calc_reach_odds(self, distance, reach, min_odds, max_odds):
        assert min_odds <= fielding.calc_reach_odds(distance, reach) <= max_odds

    @pytest.mark.parametrize(
        "grab, odds",
        [
            (0, fielding.MIN_GRABBINESS_ODDS),
            (1, fielding.MIN_GRABBINESS_ODDS+fielding.GRABBINESS_MIDPOINT),
            (2, fielding.MAX_GRABBINESS_ODDS)
        ]
    )
    def test_calc_grab_odds(self, grab, odds):
        assert fielding.calc_grabbiness_odds(grab) == pytest.approx(odds)

    @pytest.mark.parametrize(
        "odds, ave_time_min, ave_time_max",
        [
            (0.01, 6, 9),
            (0.5, 5, 7),
            (0.9, 2, 3),
            (0.99, 1, 2)
        ]
    )
    def test_roll_error_time(self, patcher, odds, ave_time_min, ave_time_max):
        print(" ~Error Times~")
        patcher.patch_normal("blaseball.playball.fielding.normal")
        error_times = [fielding.roll_error_time(odds) for __ in patcher]
        error_times_minus_rejects = [x for x in error_times if x != 0]

        print(f"{odds*100:0.2f}% success: "
              f"min {min(error_times_minus_rejects):.2f}s "
              f"ten {error_times_minus_rejects[10]:.2f}s "
              f"mean {mean(error_times_minus_rejects):.2f}s "
              f"nten {error_times_minus_rejects[-10]:.2f}s "
              f"max {max(error_times_minus_rejects):.2f}s")

        assert min(error_times_minus_rejects) >= 0
        assert ave_time_min <= mean(error_times_minus_rejects) <= ave_time_max

    def test_catch_integrated(self, patcher, gamestate_1):
        patcher.patch('blaseball.playball.fielding.rand', lambda iteration: iteration/10+0.01, iterations=10)
        patcher.patch('blaseball.playball.fielding.calc_reach_odds',
                      lambda distance, reach, iteration: iteration / 2,
                      iterations=3)
        patcher.patch('blaseball.playball.fielding.calc_grabbiness_odds',
                      lambda grabbiness, iteration: iteration / 2,
                      iterations=3)
        patcher.patch('blaseball.playball.fielding.roll_error_time', lambda odds: 5)
        patcher.patch('blaseball.playball.liveball.LiveBall.flight_time', lambda self: 3)

        live_ball = liveball.LiveBall(10, 45, 80)
        fielder = gamestate_1.defense()['fielder 1']

        # 3 * 3 * 10 = 90 iterations
        # 50 at 0 odds = 0 catches, 8 second total
        # 10 at 0.25 odds = 3 catches
        # 20 at 0.50 odds = 10 catches
        # 10 at 1 odds = 10 catches

        catches = [fielding.Catch(live_ball, fielder, 10) for __ in patcher]
        made_catches = [x for x in catches if x.caught]
        missed_catches = [x for x in catches if not x.caught]

        assert len(made_catches) == 23
        assert len(missed_catches) == 90 - 23

        for catch in made_catches:
            assert catch.duration == 3

        for catch in missed_catches:
            assert catch.duration == 8

    def test_catch_str_conversion(self, gamestate_1, seed_randoms):
        # just make sure these don't throw errors
        live_ball = liveball.LiveBall(10, 45, 80)
        catch = fielding.Catch(live_ball, gamestate_1.defense()['fielder 1'], 20)
        assert isinstance(str(catch), str)
        assert isinstance(repr(catch), str)


class TestThrow:
    @pytest.mark.parametrize(
        "throwing, distance, min_below_98, max_below_98",
        # remember that patch_normal includes 1/1E6 outliers
        [
            (0, 100, 20, 50),
            (1, 100, 2, 5),
            (2, 100, 1, 5),
            (0.5, 40, 3, 10),
            (1, 400, 0, 100)
        ]
    )
    def test_roll_throw_odds(self, patcher, throwing, distance, min_below_98, max_below_98):
        print(" ~Throw Difficulty~")
        patcher.patch_normal('blaseball.playball.fielding.normal')

        throws = [fielding.roll_throw_odds_modifier(throwing, distance) for __ in patcher]
        total_below_98 = len([x for x in throws if x < 0.98])

        print(f"{distance:.0f} feet at {throwing:.2f} throwing: "
              f"min {min(throws)*100:.2f}% "
              f"ten {throws[10]*100:.2f}% "
              f"mean {mean(throws)*100:.2f}% "
              f"nten {throws[-10]*100:.2f}% "
              f"max {max(throws)*100:.2f}% "
              f"{total_below_98} below 98")

        assert min_below_98 <= total_below_98 <= max_below_98

    @pytest.mark.parametrize(
        "throwing, distance, time",
        [
            (1, 0, 0),
            (0, 100, 1),
            (1, 100, 1-(100*fielding.THROW_SPEED_FACTOR))
        ]
    )
    def test_throw_duration(self, throwing, distance, time):
        assert fielding.calc_throw_duration_base(throwing, distance) == pytest.approx(time)

    @pytest.mark.parametrize(
        "grabbiness, time",
        [
            (0, 2),
            (1, 1),
            (2, 0)
        ]
    )
    def test_calc_decision_time(self, grabbiness, time):
        assert fielding.calc_decision_time(grabbiness) == pytest.approx(time)

    def test_throw_integrated(self, patcher, gamestate_1):
        start_player = gamestate_1.defense()['basepeep 1']
        end_player = gamestate_1.defense()['basepeep 2']

        patcher.patch('blaseball.playball.fielding.rand',
                      lambda iteration: iteration/10+0.01,
                      iterations=10)
        patcher.patch('blaseball.playball.fielding.roll_throw_odds_modifier',
                      lambda throwing, distance, iteration: iteration / 2,
                      iterations=3)
        patcher.patch('blaseball.playball.fielding.calc_grabbiness_odds',
                      lambda grabbiness, iteration: iteration / 2,
                      iterations=3)
        patcher.patch('blaseball.playball.fielding.calc_throw_duration_base',
                      lambda throwing, distance: 3)
        patcher.patch('blaseball.playball.fielding.calc_decision_time',
                      lambda grabbiness: 1)
        patcher.patch('blaseball.playball.fielding.roll_error_time',
                      lambda odds: 7)

        throws = [fielding.Throw(start_player, end_player, 100) for __ in patcher]
        made_throws = [x for x in throws if not x.error]
        missed_throws = [x for x in throws if x.error]

        assert len(made_throws) == 23
        assert len(missed_throws) == 90 - 23

        for catch in made_throws:
            assert catch.duration == 4

        for catch in missed_throws:
            assert catch.duration == 11

    def test_throw_strings(self, gamestate_1):
        start_player = gamestate_1.defense()['basepeep 1']
        end_player = gamestate_1.defense()['basepeep 2']

        throw = fielding.Throw(start_player, end_player, 100)

        assert isinstance(throw.text, str)
        assert isinstance(str(throw), str)
        assert isinstance(repr(throw), str)
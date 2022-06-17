import pytest

from blaseball.playball import basepaths

from statistics import mean


class TestRunnerFunctions:
    @pytest.mark.parametrize(
        "speed, secperft",
        [
            (0, 0.05),
            (1, 0.04),
            (2, 0.03)
        ]
    )
    def test_calc_speed(self, speed, secperft):
        assert basepaths.calc_speed(speed) == pytest.approx(1 / secperft)

    # the leadoff testing is so wildly overbuilt here becuase I was figuring out how I wanted to handle leadoff
    # as I was writing the tests. TDD lo!!

    leadoff_parameters = {
        # "bravery, throwing, max_awareness, bravery_delta, throwing_delta, max_awareness_delta
        'delta bravery': (1, 1, 1, 0.1, 0, 0),
        'delta throwing': (1, 1, 1, 0, -0.1, 0),
        'delta awareness': (1, 1, 1, 0, 0, -0.1),
    }

    @pytest.mark.parametrize(
        "bravery, throwing, max_awareness, bravery_delta, throwing_delta, max_awareness_delta",
        leadoff_parameters.values(),
        ids=list(leadoff_parameters.keys())
    )
    def test_calc_leadoff_relative(self, bravery, throwing, max_awareness,
                                   bravery_delta, throwing_delta, max_awareness_delta):
        base_leadoff = basepaths.calc_leadoff(bravery, throwing, max_awareness)
        delta_leadoff = basepaths.calc_leadoff(
            bravery + bravery_delta,
            throwing + throwing_delta,
            max_awareness + max_awareness_delta
        )

        assert 0 <= base_leadoff <= 30
        assert base_leadoff < delta_leadoff

    leadoff_parameters = {
        # "bravery, throwing, max_awareness, bravery_delta, throwing_delta, max_awareness_delta
        'absolute_min': (0, 2, 2, 0, 1),
        'absolute_max': (2, 0, 0, 40, 60),
        'average': (1, 1, 1, 5, 20),
        'bad everything': (0.5, 0.5, 0.5, 5, 20)
    }

    @pytest.mark.parametrize(
        "bravery, throwing, max_awareness, min_distance, max_distance",
        leadoff_parameters.values(),
        ids=list(leadoff_parameters.keys())
    )
    def test_calc_leadoff_absoute(self, bravery, throwing, max_awareness, min_distance, max_distance):
        print(" ~Leadoff Distances~")
        leadoff = basepaths.calc_leadoff(bravery, throwing, max_awareness)

        print(f"{bravery:0.1f} bravery, {throwing:0.1f} pitcher throwing, {max_awareness:0.1f} max awarenss: "
              f"{leadoff} ft total leadoff.")
        assert min_distance <= leadoff <= max_distance

    @pytest.mark.parametrize(
        "duration, time_to_base, timing, bravery, min_percent, max_percent",
        [
            (3, 3, 1, 1, 10, 30),
            (10, 10, 1, 1, 10, 30),
            (30, 30, 1, 1, 20, 40),
            (15, 10, 1, 1, 60, 80),
            (20, 10, 1, 1, 70, 95),
            (10, 10, 0, 2, 45, 55),
            (20, 10, 0, 2, 70, 90),
            (20, 10, 1.5, 0, 70, 90),
            (12, 10, 1.5, 0, 0, 30),
            (12, 10, 2, 2, 80, 100)
        ]
    )
    def test_roll_net_advance_time(self, patcher, duration, time_to_base, timing, bravery, min_percent, max_percent):
        print(" ~Continue Net Timing~")
        patcher.patch_normal('blaseball.playball.basepaths.normal')

        net_times = [basepaths.roll_net_advance_time(duration, time_to_base, timing, bravery) for __ in patcher]
        advancing = len([x for x in net_times if x > 0])

        print(f"{timing:0.0f} timing, {bravery:0.0f} bravery. {time_to_base}s to cover in {duration}s: "
              f"min {min(net_times):0.2f} ten {net_times[10]:0.2f} mean {mean(net_times):0.2f} "
              f"nten {net_times[-10]:0.2f} max {max(net_times):0.2f}, {advancing}% advance")

        assert min_percent <= advancing <= max_percent


class TestRunner:
    def test_init_runner(self, ballgame_1):
        runner = basepaths.Runner(ballgame_1.batter(), 90)
        assert isinstance(runner, basepaths.Runner)
        assert runner.base == 0

    def test_time_to_base(self, runner_on_second):
        runner_on_second.basepath_length = 100
        runner_on_second.safe = False
        runner_on_second.forward = True
        runner_on_second.speed = 10
        assert runner_on_second.time_to_base() == pytest.approx(10)

        runner_on_second.remainder = 30
        assert runner_on_second.time_to_base() == pytest.approx(7)

        runner_on_second.forward = False
        assert runner_on_second.time_to_base() == pytest.approx(3)

        runner_on_second.safe = True
        assert runner_on_second.time_to_base() == 0.0

    def test_next_base(self, runner_on_second):
        assert runner_on_second.next_base() == 3

    error_parameters = {
        # "start_base, min_base, max_base, tagging_up"
        'pickle error': (2, 3, 2, False),
        'far ahead error': (3, 1, 1, False),
        'far behind error': (1, 3, 4, False),
        'tag base 0': (0, 1, 4, True),
        'tag negative': (1, 2, 4, True),
        'tag positive': (3, 1, 2, True),
    }

    @pytest.mark.parametrize(
        "start_base, min_base, max_base, tagging_up",
        error_parameters.values(),
        ids=list(error_parameters.keys())
    )
    def test_decide_errors(self, runner_on_second, start_base, min_base, max_base, tagging_up):
        runner_on_second.base = start_base
        runner_on_second.tagging_up = tagging_up
        with pytest.raises(RuntimeError):
            runner_on_second.decide(10, min_base, max_base, 0)

    def test_decide_force(self, runner_on_second):
        # test force forward
        runner_on_second.decide(10, 3, 4, 0)
        assert runner_on_second.forward
        assert runner_on_second.force

        # test force hold
        runner_on_second.decide(10, 1, 2, 0)
        assert not runner_on_second.forward
        assert runner_on_second.force

        runner_on_second.remainder = 70
        runner_on_second.decide(10, 2, 3, 0)
        assert runner_on_second.forward
        assert not runner_on_second.force

    def test_decide_rolls(self, runner_on_second, patcher):
        patcher.patch('blaseball.playball.basepaths.roll_net_advance_time',
                      lambda duration, time_to_base, timing, bravery, iteration: iteration - 0.5,
                      iterations=2)

        decisions = []
        for __ in patcher:
            runner_on_second.decide(10, 1, 2, 0)
            decisions += [runner_on_second.forward]
        assert not any(decisions)

        decisions = []
        for __ in patcher:
            runner_on_second.decide(10, 1, 3, 0)
            decisions += [runner_on_second.forward]
        assert not decisions[0]
        assert decisions[1]

    advance_parameters = {
        # min_base, max_base, adv_duration, ending_base, ending_remainder, forward
        'two to three': (2, 3, 100, 3, True),
        'two stop': (2, 3, 1, 2, True),
        'two to four': (2, 4, 100, 4, True),
        'two to three timing': (2, 4, 11, 3, True)
    }

    @pytest.mark.parametrize(
        "min_base, max_base, adv_duration, ending_base, forward",
        advance_parameters.values(),
        ids=list(advance_parameters.keys())
    )
    def test_advance_base(self, patcher, runner_on_second, min_base, max_base, adv_duration,
                          ending_base, forward):
        # force perfect decisions
        patcher.patch('blaseball.playball.basepaths.roll_net_advance_time',
                      lambda duration, time_to_base, timing, bravery: duration-time_to_base)
        runner_on_second.speed = 10

        runner_on_second.advance(adv_duration, min_base, max_base, 0)

        assert runner_on_second.base == ending_base
        assert runner_on_second.forward == forward
        # you should never have a reminder with 0 hit_duration_bonus and perfect decisions:
        assert runner_on_second.remainder == 0
        assert runner_on_second.safe


    @pytest.mark.parametrize(
        "adv_duration, end_base, end_remainder",
        [
            (1, 2, 10),
            (2, 2, 20),
            (10, 3, 10),
            (12, 3, 30)
        ]
    )
    def test_advance_remainder(self, patcher, runner_on_second, adv_duration, end_base, end_remainder):
        # force advance
        patcher.patch('blaseball.playball.basepaths.roll_net_advance_time',
                      lambda duration, time_to_base, timing, bravery: 1)
        runner_on_second.speed = 10

        runner_on_second.advance(adv_duration, 1, 4, 0)

        assert runner_on_second.base == end_base
        assert runner_on_second.remainder == pytest.approx(end_remainder)
        assert not runner_on_second.safe

    @pytest.mark.parametrize(
        "adv_duration, bonus_duration, end_base, end_remainder, end_safe",
        [
            (1, 1, 2, 0, True),
            (1, 10, 2, 10, False),
            (10, 2, 3, 0, True),
            (10, 20, 3, 10, False)
        ]
    )
    def test_advance_bonus(self, patcher, runner_on_second, adv_duration, bonus_duration,
                           end_base, end_remainder, end_safe):
        # set ideal stats:
        runner_on_second.player['timing'] = 2
        runner_on_second.player['bravery'] = 2
        patcher.patch('blaseball.playball.basepaths.normal', lambda loc, scale: loc)
        runner_on_second.speed = 10

        runner_on_second.advance(adv_duration, 1, 4, bonus_duration)

        assert runner_on_second.base == end_base
        assert runner_on_second.remainder == pytest.approx(end_remainder)
        assert runner_on_second.safe == end_safe

    def test_tagging_up_1(self, patcher, runner_on_second):
        # force advance
        patcher.patch('blaseball.playball.basepaths.roll_net_advance_time',
                      lambda duration, time_to_base, timing, bravery: 1)

        runner_on_second.tagging_up = True
        runner_on_second.remainder = 50
        runner_on_second.speed = 10
        runner_on_second.advance(8, 1, 4, 0)

        assert runner_on_second.base == 2
        assert runner_on_second.remainder == 30

    def test_tagging_up_2(self, patcher, runner_on_second):
        # prolly should parameterize this.
        # force advance
        patcher.patch('blaseball.playball.basepaths.roll_net_advance_time',
                      lambda duration, time_to_base, timing, bravery: 1)

        runner_on_second.tagging_up = True
        runner_on_second.remainder = 50
        runner_on_second.speed = 10
        runner_on_second.advance(5 + 9 + 2, 1, 4, 0)

        assert runner_on_second.base == 3
        assert runner_on_second.remainder == 20


class TestBasepathsManipulation:
    # Test creating and manipulating basepaths as a data structure
    def test_init_basepaths(self, ballgame_1):
        assert isinstance(ballgame_1.bases, basepaths.Basepaths)

    def test_get_set(self, ballgame_1):
        bases = ballgame_1.bases
        
        assert bases[1] is None

        batter_1 = ballgame_1.batter()
        bases[1] = batter_1
        assert isinstance(bases[1], basepaths.Runner)
        assert bases[1].player is batter_1
        assert bases[0] is None
        assert bases[2] is None
        assert bases[3] is None

        batter_2 = ballgame_1.batter(1)
        bases[3] = batter_2
        assert bases[1].player is batter_1
        assert bases[3].player is batter_2
        assert bases[0] is None
        assert bases[2] is None

    def test_del(self, ballgame_1):
        bases = ballgame_1.bases
        batter_1 = ballgame_1.batter()
        bases[1] = batter_1
        batter_2 = ballgame_1.batter(1)
        bases[3] = batter_2

        assert bases[1].player is batter_1
        del bases[1]
        assert bases[1] is None
        assert bases[3].player is batter_2

        del bases[3]
        assert bases[3] is None

        with pytest.raises(KeyError):
            del bases[3]

    def test_as_list(self, ballgame_1):
        bases = ballgame_1.bases

        assert list(bases) == []
        assert bases.to_base_list() == [None] * 4

        batter_1 = ballgame_1.batter()
        bases[1] = batter_1
        batter_2 = ballgame_1.batter(1)
        bases[3] = batter_2

        as_list = list(bases)
        assert len(as_list) == 2
        assert as_list[0].player is batter_1
        assert as_list[1].player is batter_2

        base_list = bases.to_base_list()
        assert len(base_list) == 4
        assert base_list[0] is None and base_list[2] is None
        assert base_list[1].player is batter_1
        assert base_list[3].player is batter_2

    def test_iteration(self, ballgame_1):
        bases = ballgame_1.bases

        batter_1 = ballgame_1.batter()
        bases[1] = batter_1
        batter_2 = ballgame_1.batter(1)
        bases[3] = batter_2

        for runner in bases:
            assert isinstance(runner, basepaths.Runner)

        players = [x.player for x in bases]
        assert len(players) == 2
        assert players[0] is batter_1
        assert players[1] is batter_2


    def test_add_runners_and_len(self, ballgame_1):
        assert len(ballgame_1.bases) == 0
        ballgame_1.bases += ballgame_1.batter()
        assert len(ballgame_1.bases) == 1
        ballgame_1.bases[2] = ballgame_1.batter(1)
        assert len(ballgame_1.bases) == 2

    def test_bool(self, empty_basepaths, player_1):
        assert not empty_basepaths
        empty_basepaths += player_1
        assert empty_basepaths

    def test_strs(self, empty_basepaths, player_1):
        assert isinstance(str(empty_basepaths), str)
        assert isinstance(empty_basepaths.nice_string(), str)
        empty_basepaths += player_1
        assert isinstance(str(empty_basepaths), str)
        assert isinstance(empty_basepaths.nice_string(), str)

class TestBasepathsRunners:
    # test basepaths ability to manage runners
    pass
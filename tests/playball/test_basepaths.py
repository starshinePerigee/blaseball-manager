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

    def test_decide_force(self, runner_on_second):
        # test pickle error
        with pytest.raises(RuntimeError):
            assert runner_on_second.decide(10, 2, 2, 0)

        # test force forward
        assert runner_on_second.decide(10, 3, 4, 0)
        assert runner_on_second.force

        # test force hold
        assert not runner_on_second.decide(10, 1, 2, 0)
        assert runner_on_second.force

        runner_on_second.remainder = 70
        assert runner_on_second.decide(10, 2, 3, 0)
        assert not runner_on_second.force

    def test_decide_rolls(self, runner_on_second, patcher):
        patcher.patch('blaseball.playball.basepaths.roll_net_advance_time',
                      lambda duration, time_to_base, timing, bravery, iteration: iteration - 0.5,
                      iterations=2)

        assert not any([runner_on_second.decide(10, 1, 2, 0) for __ in patcher])

        decisions = [runner_on_second.decide(10, 1, 3, 0) for __ in patcher]
        assert not decisions[0]
        assert decisions[1]

    advance_parameters = {
        # min_base, max_base, adv_duration, ending_base, ending_remainder, forward
        'two to three': (2, 3, 100, 3, True),
        'two stop': (2, 3, 1, 2, True)
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

        runner_on_second.advance(adv_duration, min_base, max_base, 0)

        assert runner_on_second.base == ending_base
        assert runner_on_second.forward == forward
        # you should never have a reminder with 0 hit_duration_bonus and perfect decisions:
        assert runner_on_second.remainder == 0
        assert runner_on_second.safe

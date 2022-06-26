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

    def test_runner_eq(self, batters_4):
        batter_1 = batters_4[0]
        batter_2 = batters_4[1]
        assert batter_1 == batter_1
        runner_1 = basepaths.Runner(batter_1, 90)
        assert runner_1 == batter_1
        assert runner_1 != batter_2

        runner_2 = basepaths.Runner(batter_2, 90)
        assert runner_2 != runner_1

        with pytest.raises(TypeError):
            assert batter_1 == runner_1

        with pytest.raises(TypeError):
            assert runner_2 == "Test1 Bobson"

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
        # don't forget basepaths.runners is FIFO
        bases = ballgame_1.bases

        assert list(bases) == []
        assert bases.to_base_list() == [None] * 4

        batter_1 = ballgame_1.batter()
        bases[1] = batter_1
        batter_2 = ballgame_1.batter(1)
        bases[3] = batter_2

        as_list = list(bases)
        assert len(as_list) == 2
        assert as_list[0].player is batter_2
        assert as_list[1].player is batter_1

        base_list = bases.to_base_list()
        assert len(base_list) == 4
        assert base_list[0] is None and base_list[2] is None
        assert base_list[1].player is batter_1
        assert base_list[3].player is batter_2

    def test_iteration(self, empty_basepaths, batters_4):
        bases = empty_basepaths

        bases[1] = batters_4[1]
        bases[3] = batters_4[0]
        bases += batters_4[2]

        count = 0
        for runner in bases:
            assert isinstance(runner, basepaths.Runner)
            count += 1
        assert count == 3

        count = 0
        for i, runner in enumerate(bases):
            count = i
            assert runner == batters_4[i]
        assert count == 2

        players = [x.player for x in bases]
        assert len(players) == 3
        assert players[1] is batters_4[1]
        assert players[0] is batters_4[0]

    def test_add_runners_and_len(self, ballgame_1):
        assert len(ballgame_1.bases) == 0
        ballgame_1.bases += ballgame_1.batter()
        assert len(ballgame_1.bases) == 1
        ballgame_1.bases[2] = ballgame_1.batter(1)
        assert len(ballgame_1.bases) == 2

    def test_add_runners_order(self, empty_basepaths, batters_4):
        """basepaths.runners is a fifo queue, so make sure order is preserved if you're manually adding runners."""
        empty_basepaths[1] = batters_4[1]
        assert empty_basepaths[1].player is batters_4[1]
        assert empty_basepaths.runners[0].player is batters_4[1]

        # add a player after
        empty_basepaths[3] = batters_4[3]
        assert empty_basepaths[3].player is batters_4[3]
        assert empty_basepaths.runners[0].player is batters_4[3]
        assert empty_basepaths.runners[1].player is batters_4[1]

        # add player in the middle
        empty_basepaths[2] = batters_4[2]
        assert empty_basepaths[2].player is batters_4[2]
        assert empty_basepaths.runners == batters_4[3:0:-1]

        # add player to beginning
        empty_basepaths += batters_4[0]
        assert empty_basepaths[0].player is batters_4[0]
        assert empty_basepaths.runners == batters_4[::-1]

    def test_bool(self, empty_basepaths, player_1):
        assert not empty_basepaths
        empty_basepaths += player_1
        assert empty_basepaths

    def test_strings(self, empty_basepaths, player_1):
        assert isinstance(str(empty_basepaths), str)
        assert isinstance(empty_basepaths.nice_string(), str)
        empty_basepaths += player_1
        assert isinstance(str(empty_basepaths), str)
        assert isinstance(empty_basepaths.nice_string(), str)

class TestBasepathsRunners:
    # test basepaths ability to manage runners
    def test_advance_all_single_runner(self, empty_basepaths, batters_4):
        # single runner case - rounding the bases and scoring
        empty_basepaths[2] = batters_4[0]
        runner = empty_basepaths[2]
        runner.always_run = True
        runner.speed = 10

        empty_basepaths.advance_all(5, 0)
        assert runner.remainder == pytest.approx(50)
        assert runner.base == 2

        empty_basepaths.advance_all(5, 0)
        assert runner.remainder == pytest.approx(10)
        assert runner.base == 3

        runs, runners = empty_basepaths.advance_all(100, 0)
        assert len(empty_basepaths) == 0
        assert runs == 1
        assert runners[0] is runner.player

    def test_advance_all_hitter_player_first(self, empty_basepaths, batters_4, patcher):
        # test interaction with a hitter and player on first who does not want to advance

        # perfect decisions:
        patcher.patch('blaseball.playball.basepaths.roll_net_advance_time',
                      lambda duration, time_to_base, timing, bravery: duration-time_to_base)

        empty_basepaths[1] = batters_4[0]
        empty_basepaths += batters_4[1]
        for runner in empty_basepaths:
            runner.speed = 10

        empty_basepaths.advance_all(1, 0)  # very low time
        assert empty_basepaths[1].player is batters_4[0]
        assert empty_basepaths[1].forward
        assert empty_basepaths[0].remainder == 10

        # advance them to the next bases
        empty_basepaths.advance_all(9, 100)
        assert empty_basepaths[2].player is batters_4[0]
        assert empty_basepaths[2].remainder == pytest.approx(10)

        # pretend the batter is super fast
        empty_basepaths[1].remainder = 80

        empty_basepaths.advance_all(2, 0)
        # leading runner should bail
        assert empty_basepaths[2].player is batters_4[0]
        assert empty_basepaths[2].remainder == 0
        assert empty_basepaths[2].safe

        assert empty_basepaths[1].remainder == pytest.approx(80 - 20)
        assert not empty_basepaths[1].safe
        assert not empty_basepaths[1].forward

    # this next test is actually a very complicated situation.
    # the runner on third is very far down the basepaths, but has to tag up, which will take a long time
    # the runner on second can tag up super fast, but then they're kind of in limbo
    # if they think the runner on third is going to get thrown out, they should stay at second -
    # otherwise the ball will be at third and they're hosed.
    # if they think the runner on third is safe (ie: will be able to tag up without issue and advance to home)
    # they should advance to third so they can take the base as soon as the runner on third tags up and turns

    # none of this is implemented, and this is a very rare case.
    # what we want is the safe option:
    # runners on second and first tag up, wait on base for the runner on third to tag up,
    # then decide freely simultaneously if they want to advance

    # but - this also doesn't work, because the way time is calculated per-runner.
    # if you give 100 seconds, the runner on third will tag up, advance, and score.
    # the runner on second will be clear to proceed
    # which in a way, is like the intended behavior - if the runner on first has enough time,
    # they go for it. the only problem is this fails to count hit_duration_bonus.
    # which isn't a huge problem, but you should be aware of it.

    tag_up_parameters = {
        # "advance_time, runner_bases, runner_positions, runs_to_score
        # 'one second easy': (1, [3, 2, 1], [70, 10, 10], 0),
        # '100 seconds clear': (100, [], [], 3),
        # '5 seconds hold at second': (5, [3, 2, 1], [30, 0, 0], 0),
        #'10 seconds advance all': (10, [3, 2, 1], [20, 80, 80], 0),
        '13 seconds double up on third weird edge case DANGER': (13, [3, 3, 2], [50, 0, 0], 0)
    }

    @pytest.mark.parametrize(
        "advance_time, runner_bases, runner_positions, runs_to_score",
        tag_up_parameters.values(),
        ids=list(tag_up_parameters.keys())
    )
    def test_tag_up_all_conflict(self, empty_basepaths, batters_4,
                                 advance_time, runner_bases, runner_positions, runs_to_score):
        empty_basepaths[3] = batters_4[2]
        empty_basepaths[2] = batters_4[1]
        empty_basepaths[1] = batters_4[0]

        for runner in empty_basepaths:
            runner.speed = 10
            runner.always_run = True
            runner.remainder = 20
        empty_basepaths[3].remainder = 80
        empty_basepaths.tag_up_all()

        runs_scored, scoring_runners = empty_basepaths.advance_all(advance_time)
        assert runs_scored == runs_to_score
        for runner, base, remainder in zip(empty_basepaths, runner_bases, runner_positions):
            assert runner.base == base
            assert runner.remainder == pytest.approx(remainder)

    def test_remove_home_runners(self, empty_basepaths, batters_4):
        empty_basepaths[3] = batters_4[2]
        empty_basepaths[2] = batters_4[1]
        empty_basepaths[1] = batters_4[0]

        for runner in empty_basepaths:
            runner.speed = 10
            runner.always_run = True
            runner.remainder = 20

        empty_basepaths.advance_all(20)
        assert empty_basepaths.runners == [batters_4[0]]

    def test_check_out_condition_forward(self, empty_basepaths, player_1):
        """Test check out logic"""
        assert empty_basepaths.check_out(1)[0] is None

        empty_basepaths[2] = player_1
        runner = empty_basepaths[2]
        runner.remainder = 20.0
        runner.force = False
        runner.forward = True

        assert empty_basepaths.check_out(2)[0] is None
        assert empty_basepaths.check_out(3)[0] is None

        runner.force = True
        assert empty_basepaths.check_out(2)[0] is None
        runner_out, tagable = empty_basepaths.check_out(3)
        assert runner_out is runner
        assert not tagable
        assert empty_basepaths.runners == []

    def test_check_out_condition_backwards(self, empty_basepaths, player_1):
        """Test check out logic"""
        empty_basepaths[2] = player_1
        runner = empty_basepaths[2]
        runner.remainder = 20.0
        runner.force = False
        runner.forward = False

        assert empty_basepaths.check_out(2)[0] is None
        assert empty_basepaths.check_out(3)[0] is None

        runner.remainder = 5.0
        assert empty_basepaths.check_out(3)[0] is None
        runner_out, tagable = empty_basepaths.check_out(2)
        assert runner_out is runner
        assert tagable
        assert empty_basepaths.runners == []

    def test_check_out_live(self, empty_basepaths, batters_4):
        """Test checking out with live basepath situations,
        by simulating a runners on first and third, 6-4-3-2 triple play"""

        # players on 1st and 3rd, with a hit:
        empty_basepaths[3] = batters_4[0]  # third base
        empty_basepaths[1] = batters_4[1]  # first base
        empty_basepaths += batters_4[2]  # batter

        for runner in empty_basepaths:
            runner.speed = 10
            runner.always_run = True

        # advance 2 seconds (20 feet)
        empty_basepaths.advance_all(2)

        # force out at second
        assert empty_basepaths.check_out(2)[0] == batters_4[1]

        empty_basepaths.advance_all(2)

        #force out at first
        assert empty_basepaths.check_out(1)[0] == batters_4[2]

        empty_basepaths.advance_all(2)
        # runner on third is now 60 feet down, so not taggable yet. if this were live, we'd have a rundown.
        # but instead we've forced advance, so now we can see them run into the tag
        assert empty_basepaths.check_out(4)[0] is None
        empty_basepaths.advance_all(2.5)
        assert empty_basepaths.check_out(4)[0] == batters_4[0]
        # what a disaster for the offense haha

    def test_reset_all(self, empty_basepaths, batters_4):
        empty_basepaths[3] = batters_4[0]  # third base
        empty_basepaths[1] = batters_4[1]  # first base

        empty_basepaths.tag_up_all()

        empty_basepaths.reset_all(batters_4[2], batters_4[3])  # just need random players in here
        assert empty_basepaths[3].remainder > 5
        assert empty_basepaths[3].forward
        assert not empty_basepaths[3].tagging_up
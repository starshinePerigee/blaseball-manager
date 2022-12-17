import pytest

from blaseball.playball import inplay
from blaseball.playball.liveball import LiveBall
from blaseball.playball.fielding import Catch, Throw, calc_throw_duration_base
from blaseball.playball.event import Update
from blaseball.playball.inplay import LiveDefense, FieldBall
from blaseball.stats import stats as s

from statistics import mean


class TestLiveDefense:
    def test_init(self, gamestate_1):
        live_d = inplay.LiveDefense(gamestate_1.defense().defense, gamestate_1.stadium.base_coords)
        assert isinstance(live_d, inplay.LiveDefense)

    def test_catch_liveball_caught(self, live_defense_rf, player_1, patcher):
        patcher.patch('blaseball.playball.fielding.roll_to_catch', lambda odds: True)
        far_left = LiveBall(20, 80, 100)

        catch_update, duration, caught = live_defense_rf.catch_liveball(far_left, player_1)

        assert isinstance(catch_update, inplay.CatchOut)
        assert duration > 1
        assert caught
        assert live_defense_rf.fielder == live_defense_rf.defense['fielder 3'].player

    def test_catch_liveball_missed(self, live_defense_rf, player_1, patcher):
        patcher.patch('blaseball.playball.fielding.roll_to_catch', lambda odds: False)
        far_left = LiveBall(20, 80, 100)

        catch_update, duration, caught = live_defense_rf.catch_liveball(far_left, player_1)

        assert isinstance(catch_update, Catch)
        assert duration > 1
        assert not caught
        assert live_defense_rf.fielder == live_defense_rf.defense['fielder 3'].player

    def test_throw_to_first(self, live_defense_rf, patcher):
        patcher.patch('blaseball.playball.fielding.roll_to_catch', lambda odds: True)
        basepeep = live_defense_rf.defense['basepeep 1'].player

        throw, duration = live_defense_rf.throw_to_base(1)

        assert isinstance(throw, Throw)
        assert duration > 1
        assert live_defense_rf.fielder == basepeep

    def test_tag_at_first(self, live_defense_rf, patcher):
        patcher.patch('blaseball.playball.fielding.roll_to_catch', lambda odds: True)
        basepeep = live_defense_rf.defense['basepeep 1'].player
        live_defense_rf.fielder = basepeep

        tag, duration = live_defense_rf.throw_to_base(1)

        assert isinstance(tag, Update)
        assert duration < 5
        assert live_defense_rf.fielder == basepeep

    @staticmethod
    def print_runner_priorities(priority_list, base, title, accuracy):
        total_zeros = sum([1 for x in priority_list if x <= 0])
        total_ones = sum([1 for x in priority_list if x >= base])

        print(f"{title:>40}:  "
              f"min {min(priority_list):.2f} "
              f"ten {priority_list[10]:.2f} "
              f"mean {mean(priority_list):.2f} "
              f"nten {priority_list[-10]:.2f} "
              f"max {max(priority_list):.2f}; "
              f"{total_zeros} zeros, {total_ones} total ones, {100 - total_ones - total_zeros} fuzz area, "
              f"{accuracy}% accuracy")

    def test_calc_throw_time_ratio_1(self, runner_on_second, live_defense_rf, patcher):
        runner_on_second.speed = 10
        patcher.patch('blaseball.playball.inplay.calc_throw_duration_base', lambda throwing, distance: 5)

        runner_on_second.remainder = 80  # 1 / 5
        assert live_defense_rf.calc_throw_time_ratio(runner_on_second) == pytest.approx(1/5)

        runner_on_second.remainder = 70
        assert live_defense_rf.calc_throw_time_ratio(runner_on_second) == pytest.approx(2/5)

        runner_on_second.remainder = 40
        assert live_defense_rf.calc_throw_time_ratio(runner_on_second) == pytest.approx(1)

        runner_on_second.remainder = 10
        assert live_defense_rf.calc_throw_time_ratio(runner_on_second) == pytest.approx(8/5)

    def test_calc_throw_time_ratio_2(self, runner_on_second, live_defense_rf):
        runner_on_second.remainder = 80
        assert 0 < live_defense_rf.calc_throw_time_ratio(runner_on_second) < 0.3

        runner_on_second.remainder = 30
        assert 1 < live_defense_rf.calc_throw_time_ratio(runner_on_second)

    @pytest.mark.parametrize(
        "awareness, min_accuracy, max_accuracy",
        [
            (0, 40, 60),
            (0.5, 55, 65),
            (1, 60, 70),
            (2, 95, 100)
        ]
    )
    def test_prioritize_runner_fielder_awareness(self, patcher, live_defense_rf, runner_on_second,
                                                 awareness, min_accuracy, max_accuracy):
        # you have the following variables: throw distance, runner distance to base, fielder awareness.
        print(" ~Fielder Runner Prioritization~")
        patcher.patch_normal('blaseball.playball.inplay.normal')
        live_defense_rf.fielder['awareness'] = awareness
        runner_on_second.remainder = 70  # runner beats the throw by 0.37 seconds

        all_weights = [live_defense_rf.prioritize_runner(runner_on_second) for __ in patcher]

        # runner_on_second beats the throw by 0.027 seconds
        throw_threshold = (inplay.LiveDefense.NOT_BASE_WEIGHT + 3) * 0.5
        accuracy = sum([1 for x in all_weights if x < throw_threshold])
        TestLiveDefense.print_runner_priorities(all_weights, 2,
                                                f"{awareness:0.0f} awe vs runner on 2nd + 50", accuracy)
        assert min_accuracy <= accuracy <= max_accuracy

    def test_print_prioritize_runner_remainder(self, live_defense_rf, runner_on_second, patcher):
        print(" ~Runner State Prioritization~")
        patcher.patch_normal('blaseball.playball.inplay.normal')
        # reminder: awareness is 1

        for distance in range(10, 100, 10):
            runner_on_second.remainder = 90 - distance
            all_weights = [live_defense_rf.prioritize_runner(runner_on_second) for __ in patcher]
            throw_threshold = (inplay.LiveDefense.NOT_BASE_WEIGHT + 3) * 0.5
            if live_defense_rf.calc_throw_time_ratio(runner_on_second) > 1:
                # fielder is favored, runner is close to start
                accuracy = sum([1 for x in all_weights if x >= throw_threshold])
                TestLiveDefense.print_runner_priorities(all_weights, 2, f"remainder {distance}", accuracy)
            else:
                # runner has crossed the midpoint
                accuracy = sum([1 for x in all_weights if x < throw_threshold])
                TestLiveDefense.print_runner_priorities(all_weights, 2, f"remainder {distance}", accuracy)

    def test_fielders_choice(self, empty_basepaths, batters_4, live_defense_rf, patcher):
        live_defense_rf.location = live_defense_rf.defense['basepeep 1'].location

        for base in range(0, 4):
            empty_basepaths[base] = batters_4[base]
            empty_basepaths[base].remainder = 10
            empty_basepaths[base].speed = 10
        active_runners = [runner for runner in empty_basepaths.runners if runner]

        # we have plenty of time, so we should throw home
        patcher.patch('blaseball.playball.inplay.normal', lambda loc, scale: 0)

        assert live_defense_rf.fielders_choice(active_runners) == 4

        for runner in empty_basepaths:
            runner.remainder = 80
        empty_basepaths[0].remainder = 40
        live_defense_rf.location = live_defense_rf.defense['fielder 1'].location

        # with no time, favor closest
        assert live_defense_rf.fielders_choice(active_runners) == 1

    def test_roll_rundown_out(self, patcher):
        patcher.patch('blaseball.playball.inplay.rand', lambda: 0)
        assert LiveDefense.roll_rundown_out(0, 0, 0) == pytest.approx(-1/2)
        assert - LiveDefense.roll_rundown_out(1.8, 1, 1) < - LiveDefense.roll_rundown_out(2, 1, 1)
        assert - LiveDefense.roll_rundown_out(1, 1, 1) > - LiveDefense.roll_rundown_out(1, 1, 1.1)
        assert - LiveDefense.roll_rundown_out(1, 1, 1) > - LiveDefense.roll_rundown_out(1, 1.1, 1)
        assert 0.2 < - LiveDefense.roll_rundown_out(1, 1, 1) < 0.5

    @pytest.mark.parametrize(
        'min_limit, max_limit, runner_bravery, defender_bravery',
        [
            (45, 55, 1, 1),
            (10, 20, 2, 0),
            (80, 90, 0, 2)
        ]
    )
    def test_roll_rundown_advance(self, patcher, min_limit, max_limit, runner_bravery, defender_bravery):
        patcher.patch_rand('blaseball.playball.inplay.rand', 100)
        rolls = [LiveDefense.roll_rundown_advance(runner_bravery, defender_bravery) for __ in patcher]
        assert min_limit < sum(rolls) < max_limit


    @pytest.mark.parametrize(
        'low_runner, high_runner, roll, low_time, high_time',
        [
            (1, 1.1, 0.1, 1, 10),
            (0, 2, 1, 1, 10),
            (1, 1.1, 0.5, 1, 5)
        ]
    )
    def test_calc_wasted_time(self, low_runner, high_runner, roll, low_time, high_time):
        low_wasted = LiveDefense.calc_wasted_time(low_runner, roll)
        high_wasted = LiveDefense.calc_wasted_time(high_runner, roll)
        assert low_wasted < high_wasted
        assert low_time < low_wasted
        assert high_time > high_wasted


    @pytest.mark.parametrize(
        'tagging_up, rundown_out, rundown_advance, expected_outs, final_base',
        [
            (False, False, True, 0, 4),
            (False, True, True, 1, 0),
            (False, False, False, 0, 3),
            (True, False, False, 0, 3),
            (True, True, False, 1, 0),
            (True, False, True, 0, 4)
        ]
    )
    def test_run_rundown(self, live_defense_catcher, empty_basepaths, batters_4, patcher,
                         tagging_up, rundown_out, rundown_advance, expected_outs, final_base):
        empty_basepaths[3] = batters_4[1]
        runner = empty_basepaths[3]
        runner.speed = 25
        runner.remainder = 60

        roll = 0.2 if rundown_out else -0.2
        patcher.patch("blaseball.playball.inplay.LiveDefense.roll_rundown_out",
                      lambda runner_bravery, primary_basepeep_bravery, support_basepeep_bravery: roll)
        patcher.patch("blaseball.playball.inplay.LiveDefense.roll_rundown_advance",
                      lambda runner_bravery, forward_basepeep_bravery: rundown_advance)
        patcher.patch('blaseball.playball.inplay.LiveDefense.calc_wasted_time',
                      lambda timing, rundown_roll: 1.25)

        if tagging_up:
            runner.tagging_up = tagging_up
            destination_base = 3
            third_basepeep = live_defense_catcher.defense['basepeep 3'].player
            live_defense_catcher.fielder = third_basepeep
            live_defense_catcher.location = live_defense_catcher.defense['basepeep 3'].location
        else:
            destination_base = 4

        updates, outs, wasted_time = live_defense_catcher.run_rundown(empty_basepaths, destination_base)

        assert wasted_time == 1.25
        assert outs == expected_outs
        if expected_outs < 1:
            assert runner.base == final_base
        else:
            assert runner not in empty_basepaths.runners

    def test_rundown_stall(self, live_defense_catcher, empty_basepaths, batters_4, gamestate_1):
        # this situation should trigger a rundown via throwing to self
        empty_basepaths[3] = batters_4[1]
        runner = empty_basepaths[3]
        runner.speed = 1
        runner.remainder = 60

        active_runners = [runner for runner in empty_basepaths.runners if runner]
        assert len(active_runners) == 1

        assert live_defense_catcher.fielders_choice(active_runners) == 4
        assert live_defense_catcher.throw_to_base(4)[1] == 0.0

    def test_strings(self, live_defense_rf):
        assert isinstance(str(live_defense_rf), str)
        assert isinstance(repr(live_defense_rf), str)


class TestFieldBall:
    def test_infield_fly_caught_empty_bases(self, gamestate_1, empty_basepaths, patcher):
        fly_ball_to_third = LiveBall(30, 70, 90)

        patcher.patch('blaseball.playball.fielding.roll_to_catch', lambda odds: True)

        field_ball = inplay.FieldBall(
            gamestate_1.batter(),
            gamestate_1.defense().defense,
            fly_ball_to_third,
            empty_basepaths
        )

        print(" ~Catch Out~")
        for update in field_ball.updates:
            print(update)

        assert isinstance(field_ball.updates[0], inplay.CatchOut)
        assert field_ball.outs == 1

    def test_infield_fly_caught_triple_play(self, gamestate_1, empty_basepaths, batters_4, patcher):
        empty_basepaths[1] = batters_4[1]
        empty_basepaths[2] = batters_4[2]
        for runner in empty_basepaths:
            runner.speed = 1  # slow lol
            runner.remainder = 50
        patcher.patch('blaseball.playball.fielding.roll_to_catch', lambda odds: True)

        fly_ball_to_first = LiveBall(30, 0.01, 60)

        field_ball = inplay.FieldBall(
            gamestate_1.batter(),
            gamestate_1.defense().defense,
            fly_ball_to_first,
            empty_basepaths
        )

        print(" ~Triple Play~")
        for update in field_ball.updates:
            print(update)

        assert field_ball.outs == 3
        assert sum([isinstance(u, inplay.FieldingOut) for u in field_ball.updates]) >= 2
        assert sum([isinstance(u, inplay.CatchOut) for u in field_ball.updates]) >= 1

    @pytest.mark.skip
    def test_infield_bases_loaded_home_run(self, gamestate_1, empty_basepaths, batters_4, patcher):
        # TODO: this test is inconsistent.
        for i in range(1, 4):
            empty_basepaths[i] = batters_4[i]
            empty_basepaths[i].always_run = True

        patcher.patch('blaseball.playball.fielding.roll_to_catch', lambda odds: False)
        patcher.patch('blaseball.playball.fielding.roll_error_time', lambda odds: 100)  # absolutely pants defense

        fly_ball_to_third = LiveBall(30, 70, 90)

        field_ball = inplay.FieldBall(
            gamestate_1.batter(),
            gamestate_1.defense().defense,
            fly_ball_to_third,
            empty_basepaths
        )

        print(" ~Infield Grand Slam~")
        for update in field_ball.updates:
            print(update)

        assert field_ball.outs == 0
        assert field_ball.runs == 4

    def test_do_rundown_score(self, defense_1, empty_basepaths, batters_4, patcher):
        """
        In this scenario, there is a runner on 3rd.
        The runner taps it impossibly slow (a bunt basically), and the catcher gets the ball
        Because there's no one on second, the runner on third doesn't have force
        but because they took a huge leadoff, they're caught in a rundown.
        They're super baller, so not only do they win the rundown (scoring a run),
        they buy enough time for the hitter to advance to first.
        """
        empty_basepaths[3] = batters_4[1]
        runner = empty_basepaths[3]
        runner.speed = 25
        runner.remainder = 55

        defense_1['catcher'].player[s.awareness] = 2

        patcher.patch("blaseball.playball.inplay.LiveDefense.roll_rundown_out",
                      lambda runner_bravery, primary_basepeep_bravery, support_basepeep_bravery: -0.2)
        patcher.patch("blaseball.playball.inplay.LiveDefense.roll_rundown_advance",
                      lambda runner_bravery, forward_basepeep_bravery: True)
        patcher.patch("blaseball.playball.inplay.LiveDefense.calc_wasted_time",
                      lambda timing, rundown_roll: 3)
        patcher.patch("blaseball.playball.fielding.roll_to_catch",
                      lambda odds: False)
        patcher.patch("blaseball.playball.fielding.roll_error_time",
                      lambda odds: 0.1)
        # patcher.patch("blaseball.playball.inplay.normal", lambda: 0)

        fail_ball = LiveBall(30, 45, 0)

        fb = FieldBall(batters_4[0], defense_1, fail_ball, empty_basepaths)

        print(" ~Rundown to Home~")
        for update in fb.updates:
            print(update)

        assert fb.outs == 0
        assert fb.runs == 1
        assert empty_basepaths[1].player is batters_4[0]
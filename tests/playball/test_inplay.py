import pytest

from blaseball.playball import inplay
from blaseball.playball.liveball import LiveBall
from blaseball.playball.fielding import Catch, Throw, calc_throw_duration_base
from blaseball.playball.event import Update

from statistics import mean


class TestLiveDefense:
    def test_init(self, ballgame_1):
        live_d = inplay.LiveDefense(ballgame_1.defense().defense, ballgame_1.bases.base_coords)
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

    def test_strings(self, live_defense_rf):
        assert isinstance(str(live_defense_rf), str)
        assert isinstance(repr(live_defense_rf), str)


class TestFieldBall:
    def test_infield_fly_caught_empty_bases(self, ballgame_1, patcher):
        fly_ball_to_third = LiveBall(30, 70, 90)

        patcher.patch('blaseball.playball.fielding.roll_to_catch', lambda odds: True)

        field_ball = inplay.FieldBall(
            ballgame_1.batter(),
            ballgame_1.defense().defense,
            fly_ball_to_third,
            ballgame_1.bases
        )

        print(" ~Catch Out~")
        for update in field_ball.updates:
            print(update)

        assert isinstance(field_ball.updates[0], inplay.CatchOut)
        assert field_ball.outs == 1

    def test_infield_fly_caught_triple_play(self, ballgame_1, batters_4, patcher):
        ballgame_1.bases[1] = batters_4[1]
        ballgame_1.bases[2] = batters_4[2]
        for runner in ballgame_1.bases:
            runner.speed = 1  # slow lol
            runner.remainder = 50
        patcher.patch('blaseball.playball.fielding.roll_to_catch', lambda odds: True)

        fly_ball_to_first = LiveBall(30, 0.01, 60)

        field_ball = inplay.FieldBall(
            ballgame_1.batter(),
            ballgame_1.defense().defense,
            fly_ball_to_first,
            ballgame_1.bases
        )

        print(" ~Triple Play~")
        for update in field_ball.updates:
            print(update)

        assert field_ball.outs == 3
        assert sum([isinstance(u, inplay.FieldingOut) for u in field_ball.updates]) >= 2
        assert sum([isinstance(u, inplay.CatchOut) for u in field_ball.updates]) >= 1

    def test_infield_bases_loaded_home_run(self, ballgame_1, batters_4, patcher):
        for i in range(1, 4):
            ballgame_1.bases[i] = batters_4[i]
            ballgame_1.bases[i].always_run = True

        patcher.patch('blaseball.playball.fielding.roll_to_catch', lambda odds: False)
        patcher.patch('blaseball.playball.fielding.roll_error_time', lambda odds: 100)  # absolutely pants defense

        fly_ball_to_third = LiveBall(30, 70, 90)

        field_ball = inplay.FieldBall(
            ballgame_1.batter(),
            ballgame_1.defense().defense,
            fly_ball_to_third,
            ballgame_1.bases
        )

        print(" ~Infield Grand Slam~")
        for update in field_ball.updates:
            print(update)

        assert field_ball.outs == 0
        assert field_ball.runs == 4

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

    def test_catch_liveball_caught(self, live_defense_1, player_1, patcher):
        patcher.patch('blaseball.playball.fielding.roll_to_catch', lambda odds: True)
        far_left = LiveBall(20, 80, 100)

        catch_update, duration, caught = live_defense_1.catch_liveball(far_left, player_1)

        assert isinstance(catch_update, inplay.CatchOut)
        assert duration > 1
        assert caught
        assert live_defense_1.fielder == live_defense_1.defense['fielder 3'].player

    def test_catch_liveball_missed(self, live_defense_1, player_1, patcher):
        patcher.patch('blaseball.playball.fielding.roll_to_catch', lambda odds: False)
        far_left = LiveBall(20, 80, 100)

        catch_update, duration, caught = live_defense_1.catch_liveball(far_left, player_1)

        assert isinstance(catch_update, Catch)
        assert duration > 1
        assert not caught
        assert live_defense_1.fielder == live_defense_1.defense['fielder 3'].player

    def test_throw_to_first(self, live_defense_1, patcher):
        patcher.patch('blaseball.playball.fielding.roll_to_catch', lambda odds: True)
        live_defense_1.fielder = live_defense_1.defense['fielder 3'].player
        basepeep = live_defense_1.defense['basepeep 1'].player

        throw, duration = live_defense_1.throw_to_base(1)

        assert isinstance(throw, Throw)
        assert duration > 1
        assert live_defense_1.fielder == basepeep

    def test_tag_at_first(self, live_defense_1, patcher):
        patcher.patch('blaseball.playball.fielding.roll_to_catch', lambda odds: True)
        basepeep = live_defense_1.defense['basepeep 1'].playe
        live_defense_1.fielder = basepeep

        tag, duration = live_defense_1.throw_to_base(1)

        assert isinstance(tag, Update)
        assert duration < 5
        assert live_defense_1.fielder == basepeep

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

    @pytest.mark.parametrize(
        "awareness, min_accuracy, max_accuracy",
        [
            (0, 40, 60),
            (0.5, 55, 65),
            (1, 60, 70),
            (2, 95, 100)
        ]
    )
    def test_prioritize_runner_fielder_awareness(self, patcher, live_defense_1, runner_on_second,
                                                 awareness, min_accuracy, max_accuracy):
        # you have the following variables: throw distance, runner distance to base, fielder awareness.
        print(" ~Fielder Runner Prioritization~")
        patcher.patch_normal('blaseball.playball.inplay.normal')
        fielder = live_defense_1.defense['fielder 3'].player
        live_defense_1.fielder = fielder
        fielder['awareness'] = awareness
        live_defense_1.location = live_defense_1.defense['fielder 3'].location
        runner_on_second.remainder = 70  # runner beats the throw by 0.37 seconds

        all_weights = [live_defense_1.prioritize_runner(runner_on_second) for __ in patcher]

        # runner_on_second beats the throw by 0.027 seconds
        accuracy = sum([1 for x in all_weights if x < 1.5])
        TestLiveDefense.print_runner_priorities(all_weights, 2,
                                                f"{awareness:0.0f} awe vs runner on 2nd + 50", accuracy)
        assert min_accuracy <= accuracy <= max_accuracy

    def test_print_prioritize_runner_remainder(self, live_defense_1, runner_on_second, patcher):
        print(" ~Runner State Prioritization~")
        patcher.patch_normal('blaseball.playball.inplay.normal')
        fielder = live_defense_1.defense['fielder 3'].player
        live_defense_1.fielder = fielder
        live_defense_1.location = live_defense_1.defense['fielder 3'].location

        for distance in range(10, 100, 10):
            runner_on_second.remainder = 90 - distance
            all_weights = [live_defense_1.prioritize_runner(runner_on_second) for __ in patcher]
            if live_defense_1.calc_throw_time_differential(runner_on_second) > 0:
                # runner is far from the base, so we're just starting
                accuracy = sum([1 for x in all_weights if x >= 1.5])
                TestLiveDefense.print_runner_priorities(all_weights, 2, f"remainder {distance}", accuracy)
            else:
                # runner has crossed the midpoint?
                accuracy = sum([1 for x in all_weights if x < 1.5])
                TestLiveDefense.print_runner_priorities(all_weights, 2, f"remainder {distance}", accuracy)

    def test_fielders_choice(self):
        pass
"""This class is meant to test fixtures and the mock functions."""

import pytest
# import blaseball
from blaseball.stats.statclasses import Stat

from support import fixturetarget

from scipy.stats import norm
import numpy
import random
from loguru import logger

#
# class TestFixtures:
#     """This exists to shakedown test fixtures, primarily to make sure they don't throw runtime errors.
#     Actual testing of most of the functionality gets captured in the test_foo classes later."""
#
#     def test_loggercapture_1(self, logger_store):
#         # this is a bad, overloaded test lol
#         assert logger_store.level_inventory['INFO'] == 0
#         logger.info("test 1")
#         logger.info("test 2")
#         logger.trace("trace 1")
#         assert logger_store.level_inventory['INFO'] == 2
#         assert "test 1" in logger_store[0]
#         assert "trace 1" in logger_store[-1]
#         assert len(logger_store) == 3
#         assert "test 2" in logger_store
#
#     def test_loggercapture_persistence(self, logger_store):
#         # just a little worried because logger has its whole global thing going on
#         assert logger_store.log == []
#         assert len(logger_store) == 0
#
#     def test_league_2(self, league_2):
#         assert isinstance(league_2, blaseball.stats.teams.League)
#
#     def test_team_1(self, team_1):
#         assert isinstance(team_1, blaseball.stats.teams.Team)
#
#     def test_player_1(self, player_1):
#         assert isinstance(player_1, blaseball.stats.players.Player)
#
#     def test_stadium_a(self, stadium_a):
#         assert isinstance(stadium_a, blaseball.stats.stadium.Stadium)
#
#     def test_compare_stadiums(self, stadium_a, stadium_cut_lf):
#         assert stadium_cut_lf.polygon.area > stadium_a.polygon.area
#         print(f"Stadium a: {stadium_a.polygon.area:.0f} sqft, stadium cut lf: {stadium_cut_lf.polygon.area:.0f} sqft")
#         print(f"Delta: {stadium_cut_lf.polygon.area - stadium_a.polygon.area:.0f} sqft")
#
#     def test_lineup_1(self, lineup_1):
#         assert isinstance(lineup_1, blaseball.stats.lineup.Lineup)
#
#     def test_defense_1(self, defense_1):
#         assert isinstance(defense_1, blaseball.stats.lineup.Defense)
#
#     def test_gamestate_1(self, gamestate_1):
#         assert isinstance(gamestate_1, blaseball.playball.gamestate.GameState)
#
#     def test_empty_basepaths(self, empty_basepaths):
#         assert isinstance(empty_basepaths, blaseball.playball.basepaths.Basepaths)
#         assert len(empty_basepaths) == 0
#
#     def test_stats_monitor_1(self, stats_monitor_1, ballgame_1):
#         assert isinstance(stats_monitor_1, blaseball.playball.statsmonitor.StatsMonitor)
#         assert stats_monitor_1.current_state is ballgame_1.state
#         assert stats_monitor_1.new_game_state in [
#             priority_tuple[1]
#             for priority_tuple
#             in ballgame_1.messenger.listeners[blaseball.playball.gamestate.GameTags.pre_tick]
#         ]
#
#     previous_pitch = None
#
#     @pytest.mark.parametrize('execution_number', range(5))
#     def test_pitch_1(self, pitch_1, execution_number):
#         assert isinstance(pitch_1, blaseball.playball.pitching.Pitch)
#         if TestFixtures.previous_pitch is not None:
#             assert TestFixtures.previous_pitch == pitch_1
#         TestFixtures.previous_pitch = pitch_1
#
#     def test_runner_on_second(self, runner_on_second, gamestate_1):
#         assert isinstance(runner_on_second, blaseball.playball.basepaths.Runner)
#         assert gamestate_1.bases[2] == runner_on_second.player
#
#     def test_batters_4(self, batters_4, gamestate_1):
#         assert isinstance(batters_4, list)
#         assert isinstance(batters_4[0], blaseball.stats.players.Player)
#         assert gamestate_1.batter() is batters_4[0]
#
#     def test_live_defense_1(self, live_defense_rf):
#         assert isinstance(live_defense_rf, blaseball.playball.inplay.LiveDefense)
#         assert live_defense_rf.location.y > 100
#
#     def test_messenger_1(self, messenger_1):
#         assert isinstance(messenger_1, blaseball.util.messenger.Messenger)
#
#     def test_count_store_all(self, count_store_all, messenger_1):
#         assert isinstance(count_store_all, blaseball.util.messenger.CountStore)
#
#         tags = blaseball.playball.gamestate.GameTags
#         messenger_1.send(1, tags.outs)
#         messenger_1.send(2, tags.foul)
#         messenger_1.send(3, tags.game_updates)
#
#         assert count_store_all.count == 3
#         assert [item.argument for item in count_store_all.items] == [3, 2, 1]
#
#     def test_pitch_manager(self, pitch_manager_1, gamestate_1, messenger_1):
#         assert isinstance(pitch_manager_1, blaseball.playball.pitchmanager.PitchManager)
#
#         count_store_pitch = blaseball.util.messenger.CountStore(
#             messenger_1,
#             blaseball.playball.gamestate.GameTags.pitch
#         )
#
#         messenger_1.send(gamestate_1, blaseball.playball.gamestate.GameTags.state_ticks)
#         assert isinstance(count_store_pitch[0], blaseball.playball.pitching.Pitch)
#
#     def test_ballgame_1(self, messenger_1, ballgame_1, count_store_all, gamestate_1):
#         assert isinstance(ballgame_1, blaseball.playball.ballgame.BallGame)
#         assert ballgame_1.state == gamestate_1
#         ballgame_1.send_tick()
#         assert len(count_store_all) > 1
#         assert isinstance(count_store_all[0], blaseball.playball.gamestate.GameState)


def noop_fn(x, iteration):
    return x


def return_iter(x, iteration):
    return iteration


class TestFunctionPatch:
    def test_function_patcher_length(self, patcher):
        patcher.patch("support.fixturetarget.add_average_1", noop_fn, 15)
        patcher.patch("support.fixturetarget.add_average_2", noop_fn, 10)

        assert len(patcher) == 150

    def test_no_patcher(self, monkeypatch):
        monkeypatch.setattr('support.fixturetarget.add_average_1', lambda x: x)
        monkeypatch.setattr('support.fixturetarget.add_average_2', lambda x: x)
        monkeypatch.setattr('support.fixturetarget.add_average_3', lambda x: x)
        assert fixturetarget.add_all_average(1) == 3

    def test_function_patcher_noop(self, patcher):
        patcher.patch("support.fixturetarget.add_average_1", noop_fn, 3)
        patcher.patch("support.fixturetarget.add_average_2", noop_fn, 5)
        patcher.patch("support.fixturetarget.add_average_3", noop_fn, 2)
        for i, patcher_i in zip(range(0, 15), patcher):
            assert i == patcher_i
            assert fixturetarget.add_all_average(10) == 30

    def test_function_patcher_iteration(self, patcher):
        patcher.patch("support.fixturetarget.add_average_1", return_iter, 2)
        patcher.patch("support.fixturetarget.add_average_2", return_iter, 3)
        patcher.patch("support.fixturetarget.add_average_3", return_iter, 4)
        results = {i: [] for i in range(1, 4)}
        for __ in patcher:
            for i, function in enumerate(
                    [fixturetarget.add_average_1, fixturetarget.add_average_2, fixturetarget.add_average_3]
            ):
                results[i+1] += [function(i+1)]
        assert sorted(results[1]) == sorted([0, 1] * 12)
        assert sorted(results[2]) == sorted([0, 1, 2] * 8)
        assert sorted(results[3]) == sorted([0, 1, 2, 3] * 6)

    def test_patch_single(self, patcher):
        patcher.patch("support.fixturetarget.add_average_1", lambda x: 1)
        assert fixturetarget.add_average_1(3) == 1
        patcher.patch('support.fixturetarget.add_average_2', lambda x: 2)
        patcher.patch('support.fixturetarget.add_average_3', lambda x, iteration: x + iteration, iterations=20)

        results = [fixturetarget.add_all_average(3) for __ in patcher]

        assert len(results) == 20
        assert results[0] == 6
        assert results[-1] == 25

    def test_patch_double(self, patcher):
        patcher.patch("support.fixturetarget.add_average_2", noop_fn, 10)
        assert len([fixturetarget.add_average_2(1) for __ in patcher]) == 10
        assert len([fixturetarget.add_average_2(3) for __ in patcher]) == 10
        patcher.reset()
        patcher.patch("support.fixturetarget.add_average_2", noop_fn, iterations=100)
        assert len([fixturetarget.add_average_2(1) for __ in patcher]) == 100

    def test_patch_rand(self, patcher):
        patcher.patch_rand("support.fixturetarget.rand", iterations=1)
        for __ in patcher:
            assert fixturetarget.add_average_1(1) == pytest.approx(2)
        patcher.patch_rand("support.fixturetarget.rand", iterations=100)
        for i in patcher:
            assert fixturetarget.add_average_1(1) == pytest.approx(1 + (i / 99) * 2)

    def test_patch_rand_iterative(self, patcher):
        def mock_add_average(x, iteration):
            return x + iteration
        patcher.patch_rand("support.fixturetarget.rand")
        patcher.patch("support.fixturetarget.add_average_2", mock_add_average, 2)
        patcher.patch("support.fixturetarget.add_average_3", mock_add_average, 3)

        all_values = [fixturetarget.add_all_average(1) for __ in patcher]

        assert len(all_values) == 600
        assert min(all_values) == pytest.approx(3)
        assert all_values[0] == min(all_values)
        assert max(all_values) == pytest.approx(8)
        assert all_values[-1] == max(all_values)

    def test_patch_normal(self, patcher):
        patcher.patch_normal("support.fixturetarget.normal", 100, 6)
        all_values = [fixturetarget.normal_test(5) for __ in patcher]

        assert len(all_values) == 100
        assert min(all_values) == pytest.approx(norm.ppf(10**-6) * 5 + 100)
        assert all_values[0] == min(all_values)
        assert max(all_values) == pytest.approx(norm.ppf(1-10**-6) * 5 + 100)
        assert all_values[-1] == max(all_values)

        all_values_20 = [fixturetarget.normal_test(20) for __ in patcher]
        assert all_values_20[10] - 100 == pytest.approx((all_values[10] - 100) * 4)


class TestRandomSeed:
    last_seed_value = -1
    last_normal = -1
    last_numpy_random = -1
    last_python_random = -1

    def test_random_seed_1(self, seed_randoms):
        TestRandomSeed.last_seed_value = numpy.random.get_state()[1][0]
        TestRandomSeed.last_python_random = random.random()
        TestRandomSeed.last_normal = numpy.random.normal()
        TestRandomSeed.last_numpy_random = numpy.random.random()

    def test_random_seed_2(self, seed_randoms):
        assert numpy.random.get_state()[1][0] == TestRandomSeed.last_seed_value + 1
        assert TestRandomSeed.last_python_random != random.random()
        assert TestRandomSeed.last_normal != numpy.random.normal()
        assert TestRandomSeed.last_numpy_random != numpy.random.random()
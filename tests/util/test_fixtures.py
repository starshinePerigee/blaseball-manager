"""This class is meant to test fixtures and the mock functions."""

import pytest
import blaseball

from support import fixturetarget

from scipy.stats import norm
import numpy
import random


class TestFixtures:
    """This exists to shakedown test fixtures, primarily to make sure they don't throw runtime errors.
    Actual testing of most of the functionality gets captured in the test_foo classes later."""
    def test_league_2(self, league_2):
        assert isinstance(league_2, blaseball.stats.teams.League)

    def test_team_1(self, team_1):
        assert isinstance(team_1, blaseball.stats.teams.Team)

    def test_player_1(self, player_1):
        assert isinstance(player_1, blaseball.stats.players.Player)

    def test_stadium_a(self, stadium_a):
        assert isinstance(stadium_a, blaseball.stats.stadium.Stadium)

    def test_compare_stadiums(self, stadium_a, stadium_cut_lf):
        assert stadium_cut_lf.polygon.area > stadium_a.polygon.area
        print(f"Stadium a: {stadium_a.polygon.area:.0f} sqft, stadium cut lf: {stadium_cut_lf.polygon.area:.0f} sqft")
        print(f"Delta: {stadium_cut_lf.polygon.area - stadium_a.polygon.area:.0f} sqft")

    def test_lineup_1(self, lineup_1):
        assert isinstance(lineup_1, blaseball.stats.lineup.Lineup)

    def test_defesne_1(self, defense_1):
        assert isinstance(defense_1, blaseball.stats.lineup.Defense)

    def test_ballgame_1(self, ballgame_1):
        assert isinstance(ballgame_1, blaseball.playball.ballgame.BallGame)

    previous_pitch = None

    @pytest.mark.parametrize('execution_number', range(5))
    def test_pitch_1(self, pitch_1, execution_number):
        assert isinstance(pitch_1, blaseball.playball.pitching.Pitch)
        if TestFixtures.previous_pitch is not None:
            assert TestFixtures.previous_pitch == pitch_1
        TestFixtures.previous_pitch = pitch_1

    def test_runner_on_second(self, runner_on_second, ballgame_1):
        assert isinstance(runner_on_second, blaseball.playball.basepaths.Runner)
        assert ballgame_1.bases[2] is runner_on_second.player

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
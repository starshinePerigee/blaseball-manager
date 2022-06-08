"""This class is meant to test fixtures and the mock functions."""

import pytest
import blaseball
from support.mock_functions import FunctionPatcher

from support import fixturetarget


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


def noop_fn(x, iteration):
    return x


def return_iter(x, iteration):
    return iteration


class TestFunctionPatch:
    def test_function_patcher_length(self, patcher):
        patcher.patch("support.fixturetarget.add_average_1", noop_fn, 15)
        patcher.patch("support.fixturetarget.add_average_2", noop_fn)

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
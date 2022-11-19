import pytest

from blaseball.stats.teams import Team, League
from blaseball.stats import players
from blaseball.stats import stats as s


class TestTeam:
    def test_init(self, empty_all_base):
        team_comp = []
        for __ in range(10):
            new_player = players.Player(s.pb)
            new_player.initialize()
            team_comp += [new_player]
        team = Team("Test Crew", team_comp)
        assert len(team) == 10

    def test_team_strings(self, team_1):
        assert isinstance(repr(team_1), str)
        assert isinstance(str(team_1), str)


class TestLeague:
    def test_init(self, empty_all_base):
        league = League(s.pb, ["test team 1", "test team 2"])
        assert len(league) == 2
        s.pb.verify()

    def test_league_strings(self, league_2):
        assert isinstance(repr(league_2), str)
        assert isinstance(str(league_2), str)
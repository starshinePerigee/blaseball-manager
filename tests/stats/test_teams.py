import pytest

from blaseball.stats.teams import Team, League
from blaseball.stats import players


class TestTeam:
    def test_init(self):
        pb = players.PlayerBase()
        pb.new_players(10)
        team = Team("test team 1", list(pb.players.values()))
        assert len(team) == 10

    def test_team_strings(self, team_1):
        assert isinstance(repr(team_1), str)
        assert isinstance(str(team_1), str)


class TestLeague:
    def test_init(self):
        pb = players.PlayerBase()
        league = League(pb, ["test team 1", "test team 2"])
        assert len(league) == 2
        assert pb.verify_players()

    def test_league_strings(self, league_2):
        assert isinstance(repr(league_2), str)
        assert isinstance(str(league_2), str)
import pytest

from blaseball.stats.teams import League
from blaseball.stats import players, lineup
from data import teamdata


@pytest.fixture()
def league_20():
    pb = players.PlayerBase()
    l = League(pb, teamdata.TEAMS_99)
    return l


@pytest.fixture
def team_1(league_20):
    return league_20.teams[0]


class TestLineup:
    def test_generate(self, team_1):
        test_lineup = lineup.Lineup.generate(team_1)
        assert test_lineup.validate[0]

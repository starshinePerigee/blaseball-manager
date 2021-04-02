import pytest

from blaseball.stats.teams import League
from blaseball.stats import players
from blaseball.stats.lineup import Lineup
from data import teamdata


@pytest.fixture()
def league_2():
    pb = players.PlayerBase()
    l = League(pb, teamdata.TEAMS_99[0:2])
    return l


@pytest.fixture
def team_1(league_2):
    return league_2[0]


class TestLineup:
    def test_generate(self, team_1):
        test_lineup = Lineup()
        test_lineup.generate(team_1)
        assert test_lineup.validate[0]

import pytest

from blaseball.stats.teams import Team, League
from blaseball.stats import players
from data import teamdata


@pytest.fixture()
def league_20():
    pb = players.PlayerBase()
    l = League(pb, teamdata.TEAMS_99)
    return l


@pytest.fixture
def team_1(league_20):
    return league_20.teams[0]




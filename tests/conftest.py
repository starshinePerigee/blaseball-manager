"""
This test contains some very useful fixtures for instantiating leagues, teams, and players

if this gets huge, check https://gist.github.com/peterhurford/09f7dcda0ab04b95c026c60fa49c2a68
"""

import pytest

from blaseball.stats import players, teams, lineup
from data import teamdata


@pytest.fixture(scope='class')
def league_2():
    pb = players.PlayerBase()
    l = teams.League(pb, teamdata.TEAMS_99[0:2])
    return l


@pytest.fixture(scope='class')
def team_1(league_2):
    for i, player in enumerate(league_2[0]):
        player["name"] = f"Test{i} Bobson"

    return league_2[0]


@pytest.fixture(params=[6, 10], scope='module')
def d_sizes(request):
    return request.param


@pytest.fixture(scope='function')
def d_fixture(d_sizes, team_1):
    i = 0
    defense_fixture = lineup.Defense()
    while i < d_sizes:
        if i <= 0:
            defense_fixture.catcher = team_1[i]
        elif i <= 1:
            defense_fixture.shortstop = team_1[i]
        elif i <= 4:
            defense_fixture.basepeeps += [team_1[i]]
        elif i <= 7:
            defense_fixture.fielders += [team_1[i]]
        else:
            defense_fixture.extras += [team_1[i]]
        i += 1
    return defense_fixture


@pytest.fixture(scope='class')
def l_fixture(d_sizes, team_1):
    lineup_fixture = lineup.Lineup()
    lineup_fixture.generate(team_1, in_order=True)
    return lineup_fixture

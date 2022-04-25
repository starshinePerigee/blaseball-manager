"""
This test contains some very useful fixtures for instantiating leagues, teams, and players

if this gets huge, check https://gist.github.com/peterhurford/09f7dcda0ab04b95c026c60fa49c2a68
"""

import pytest

from blaseball.stats import players, teams
from data import teamdata


@pytest.fixture(scope='class')
def league_2():
    playerbase = players.PlayerBase()
    league = teams.League(playerbase, teamdata.TEAMS_99[0:2])
    return league


@pytest.fixture(scope='class')
def team_1(league_2):
    for i, player in enumerate(league_2[0]):
        player["name"] = f"Test{i} Bobson"

    return league_2[0]


@pytest.fixture(scope='function')
def player_1():
    playerbase = players.PlayerBase(1)
    player = list(playerbase.players.values())[0]
    return player



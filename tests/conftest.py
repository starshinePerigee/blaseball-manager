"""
This test contains some very useful fixtures for instantiating leagues, teams, and players

if this gets huge, check https://gist.github.com/peterhurford/09f7dcda0ab04b95c026c60fa49c2a68
"""

import pytest

from blaseball.stats import players, teams, stadium, lineup
from blaseball.playball import ballgame
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


@pytest.fixture(scope='class')
def stadium_a():
    angels_coords = stadium.ANGELS_STADIUM
    return stadium.Stadium(angels_coords)


@pytest.fixture(scope='class')
def lineup_1(team_1):
    test_lineup = lineup.Lineup("Test Lineup")
    test_lineup.generate(team_1, in_order=True)
    return test_lineup


@pytest.fixture(scope='class')
def defense_1(lineup_1):
    return lineup_1.defense


@pytest.fixture(scope='function')
def ballgame_1(league_2, stadium_a):
    home_lineup = lineup.Lineup("Home Lineup")
    home_lineup.generate(league_2[0])
    away_lineup = lineup.Lineup("Away Lineup")
    away_lineup.generate(league_2[1])

    test_ballgame = ballgame.BallGame(home_lineup, away_lineup, stadium_a)
    return test_ballgame
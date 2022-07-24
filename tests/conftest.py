"""
This test contains some very useful fixtures for instantiating leagues, teams, and players

if this gets huge, check https://gist.github.com/peterhurford/09f7dcda0ab04b95c026c60fa49c2a68
"""

import pytest

from blaseball.stats import players, teams, stadium, lineup
from blaseball.playball import gamestate, pitching, basepaths, inplay, pitchmanager, ballgame, statsmonitor
from blaseball.util import messenger
from support.mock_functions import FunctionPatcher
from support.loggercapture import LoggerCapture
from data import teamdata

import numpy
import random
from loguru import logger
import sys


# disable logging during tests
logger.remove()


@pytest.fixture(scope='function')
def logger_print():
    logger_id = logger.add(sys.stdout)
    yield
    logger.remove(logger_id)


@pytest.fixture(scope='function')
def logger_store():
    logger_capture = LoggerCapture()
    logger_id = logger.add(logger_capture.receive, level="TRACE")
    yield logger_capture
    logger.remove(logger_id)


@pytest.fixture(scope='function')
def patcher(monkeypatch):
    return FunctionPatcher(monkeypatch)


class RunningSeed:
    """Since we're writing to this variable, we can't leave it floating out in the module scope ether.
    So it becomes a static member of a singleton class.
    There has to be a better way?"""
    running_seed = 383  # feather lucky number :3


@pytest.fixture(scope='function')
def seed_randoms():
    numpy.random.seed(RunningSeed.running_seed)
    random.seed(RunningSeed.running_seed)
    RunningSeed.running_seed += 1


@pytest.fixture(scope='class')
def league_2():
    playerbase = players.PlayerBase()
    league = teams.League(playerbase, teamdata.TEAMS_99[0:2])
    for i, player in enumerate(league[0]):
        player["name"] = f"Test{i} Bobson"
        player.set_all_stats(1)
    for i, player in enumerate(league[1]):
        player["name"] = f"Test{i} Johnson"
        player.set_all_stats(1)
    return league


@pytest.fixture(scope='class')
def team_1(league_2):
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
def stadium_cut_lf():
    return stadium.Stadium([300, 400, 400, 400, 400])

@pytest.fixture(scope='class')
def lineup_1(team_1):
    test_lineup = lineup.Lineup("Test Lineup")
    test_lineup.generate(team_1, in_order=True)
    return test_lineup

@pytest.fixture(scope='class')
def defense_1(lineup_1):
    return lineup_1.defense

@pytest.fixture(scope='function')
def ballgame_1(league_2, stadium_cut_lf, messenger_1):
    null_messenger = messenger.Messenger()

    home_lineup = lineup.Lineup("Home Lineup")
    home_lineup.generate(league_2[0])
    away_lineup = lineup.Lineup("Away Lineup")
    away_lineup.generate(league_2[1])

    test_ballgame = ballgame.BallGame(
        null_messenger, home_lineup, away_lineup, stadium_cut_lf, gamestate.GameRules(), messenger_1
    )
    return test_ballgame

@pytest.fixture(scope='function')
def gamestate_1(ballgame_1):
    return ballgame_1.state

@pytest.fixture(scope='function')
def pitch_1(gamestate_1, monkeypatch):
    """A nice pitch right through the zone."""
    catcher = gamestate_1.defense()['catcher']
    catcher.set_all_stats(1)
    pitcher = gamestate_1.defense()['pitcher']
    pitcher.set_all_stats(1)

    gamestate_1.outs = 1

    monkeypatch.setattr('blaseball.playball.pitching.normal', lambda loc, scale=1: loc)
    monkeypatch.setattr('blaseball.playball.pitching.rand', lambda: 0.5)

    calling_mod_from_discipline_bias = pitching.calling_mod_from_discipline_bias
    monkeypatch.setattr(
        'blaseball.playball.pitching.calling_mod_from_discipline_bias',
        lambda power, discipline: 0
    )
    calling_mod_from_next_hitter = pitching.calling_mod_from_next_hitter
    monkeypatch.setattr(
        'blaseball.playball.pitching.calling_mod_from_next_hitter',
        lambda current, on_deck: 0
    )

    pitch = pitching.Pitch(gamestate_1, pitcher, catcher)

    monkeypatch.setattr('blaseball.playball.pitching.normal', numpy.random.normal)
    monkeypatch.setattr('blaseball.playball.pitching.rand', numpy.random.rand)
    monkeypatch.setattr(
        'blaseball.playball.pitching.calling_mod_from_discipline_bias',
        calling_mod_from_discipline_bias
    )
    monkeypatch.setattr(
        'blaseball.playball.pitching.calling_mod_from_next_hitter',
        calling_mod_from_next_hitter
    )

    return pitch


@pytest.fixture(scope='function')
def runner_on_second(gamestate_1):
    player = gamestate_1.batter()
    bases = basepaths.Basepaths(gamestate_1.stadium)
    bases[2] = player
    gamestate_1.bases[2] = player
    gamestate_1.at_bat_numbers[1] += 1
    runner = bases.runners[0]
    runner.reset(player, player, base=2)  # pass player since it doesn't matter, since we're clearing the leadoff
    runner.remainder = 0
    assert isinstance(runner, basepaths.Runner)  # needed for pycharm type hints
    return runner

@pytest.fixture(scope='function')
def empty_basepaths(gamestate_1):
    return basepaths.Basepaths(gamestate_1.stadium)

@pytest.fixture(scope='function')
def batters_4(gamestate_1):
    return [gamestate_1.batter(i) for i in range(4)]

@pytest.fixture(scope='function')
def live_defense_rf(gamestate_1):
    live_d = inplay.LiveDefense(gamestate_1.defense().defense, gamestate_1.stadium.base_coords)

    fielder = live_d.defense['fielder 3'].player
    live_d.fielder = fielder
    live_d.location = live_d.defense['fielder 3'].location
    return live_d

@pytest.fixture(scope='function')
def messenger_1():
    return messenger.Messenger()

@pytest.fixture(scope='function')
def pitch_manager_1(league_2, stadium_cut_lf, messenger_1):
    home_lineup = lineup.Lineup("Home Lineup")
    home_lineup.generate(league_2[0])
    away_lineup = lineup.Lineup("Away Lineup")
    away_lineup.generate(league_2[1])
    initial_state = gamestate.GameState(home_lineup, away_lineup, stadium_cut_lf, gamestate.GameRules())

    return pitchmanager.PitchManager(initial_state, messenger_1)

@pytest.fixture(scope='function')
def count_store_all(messenger_1):
    return messenger.CountStore(messenger_1, list(gamestate.GameTags))

@pytest.fixture(scope='function')
def stats_monitor_1(ballgame_1):
    stats_monitor = statsmonitor.StatsMonitor(ballgame_1.messenger, ballgame_1.state)
    return stats_monitor

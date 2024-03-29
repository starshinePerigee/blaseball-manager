"""
This test contains some very useful fixtures for instantiating leagues, teams, and players

if this gets huge, check https://gist.github.com/peterhurford/09f7dcda0ab04b95c026c60fa49c2a68
"""

import pytest

from blaseball.stats import statclasses, playerbase, stats, players, teams, stadium, lineup
from blaseball.playball import gamestate, pitching, basepaths, inplay, pitchmanager, ballgame, statsmonitor
from blaseball.util import messenger
from support.mock_functions import FunctionPatcher
from support.loggercapture import LoggerCapture
from data import teamdata
from blaseball.stats import stats as s

import pandas as pd
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


@pytest.fixture(scope='function')
def arbitrary_pb():
    test_dataframe = pd.DataFrame(
        data={
            'name': ["A A", "B B", "C C", "D D", "E E"],
            'team': ["RIV"] * 5,
            'col0': [0, 0, 0, 0, 0],
            'col1': [1, 2, 3, 4, 5],
            'col2': [6, 7, 8, 9, 10],
            'cola': ['a', 'b', 'c', 'd', 'e'],
            'col3': [0.1, 0.2, 0.3, 0.4, 0.5],
            'col4': [0.3, 0.3, 0.3, 0.3, 0.3],
            'col5': [0, 0.2, 0.8, 1.6, 2.0]
        },
        index=[10, 11, 12, 13, 14]
    )
    pb = playerbase.PlayerBase(statclasses.RECALCULATION_ORDER_TEST, statclasses.BASE_DEPENDENCIES_TEST)
    pb.players = {i: players.Player(pb, cid=i) for i in test_dataframe.index}
    pd.stats = {
        name: statclasses.Stat(name, statclasses.Kinds.test, -1, None, None, pb)
        for name
        in test_dataframe.columns
    }
    pb._pending_stats = []  # blow this away
    pb.df = test_dataframe
    for stat in pb.stats.values():
        stat._linked_dataframe = test_dataframe
    for player in pb.players.values():
        player.load_from_pb()
    return pb


@pytest.fixture(scope='function')
def stat_1(arbitrary_pb):
    return arbitrary_pb.stats['col1']


@pytest.fixture(scope='function')
def stat_2(arbitrary_pb):
    return arbitrary_pb.stats['col2']


@pytest.fixture(scope='function')
def stat_3(arbitrary_pb):
    return arbitrary_pb.stats['col3']


"""
Here's the old conftest game construct tree
playerbase_10
league_2
    team_1
        lineup_1
            defense_1
    ballgame_1 (with messenger_1, stadium_cut_lf)
        gamestate_1
            pitch_1
            runner_on_second
            empty_basepaths
            batters_4
            live_defense_rf
            live_defense_catcher
    pitch_manager_1 (with messenger_1, stadium_cut_lf)
player_1

the correct game construct tree should look like:

generate_league (class level)
    league_2 (function level, handles league cleanup)
        gamestate_1
            pitch_1
            etc...
        ballgame_1 (with pitch_manager, stats_manager, etc.)
        pitch_manager
        stats_manager
        etc..
        player_1
stadium_cut_lf (class level)
messenger_1 (class level, users have to clean up)

"""


@pytest.fixture(scope='function')
def playerbase_10():
    for __ in range(10):
        new_player = players.Player(stats.pb)
        stats.pb.new_player(new_player)
    yield stats.pb
    stats.pb.clear_players()


@pytest.fixture(scope='function')
def empty_all_base():
    s.pb.clear_players()


@pytest.fixture(scope='class')
def generate_league_2():
    league = teams.League(s.pb, teamdata.TEAMS_99[0:2])
    for i, player in enumerate(league[0]):
        player["name"] = f"Test{i} Bobson"
        player.set_all_stats(1)
    for i, player in enumerate(league[1]):
        player["name"] = f"Test{i} Johnson"
        player.set_all_stats(1)
    yield league
    s.pb.clear_players()


@pytest.fixture(scope='class')
def generate_team_components():
    """An internal fixture to allow class scope for the tricky generate parts"""
    test_team = league_2[0]
    test_lineup = lineup.Lineup("Test Lineup")
    test_lineup.generate(team_1, in_order=True)

    return


@pytest.fixture(scope='function')
def league_2(generate_league_2):
    yield generate_league_2
    for player in generate_league_2:
        player.reset_tracking()
        player.set_all_stats(1)


@pytest.fixture(scope='function')
def team_1(league_2):
    return league_2[0]


@pytest.fixture(scope='function')
def player_1():
    player = players.Player(s.pb)
    player.initialize()
    player.modifiers = []
    player.recalculate()
    yield player
    del stats.pb[player]


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
def gamestate_1(league_2):
    state = gamestate.GameState(

    )


@pytest.fixture(scope='function')
def pitch_1(gamestate_1):
    return pitching.Pitch(
        pitcher=gamestate_1.defense()['pitcher'],
        target=0,
        location=0,
        strike=True,
        obscurity=pitching.calc_obscurity(0, 0.5),
        difficulty=pitching.calc_difficulty(0, 0.5),
        reduction=0
    )


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
def live_defense_catcher(gamestate_1):
    live_d = inplay.LiveDefense(gamestate_1.defense().defense, gamestate_1.stadium.base_coords)

    catcher = live_d.defense['catcher'].player
    live_d.fielder = catcher
    live_d.location = live_d.defense['catcher'].location
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
    stats_monitor = ballgame_1.stats_monitor
    return stats_monitor

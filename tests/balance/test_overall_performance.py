from random import shuffle

import pytest

from blaseball.playball.ballgame import BallGame
from blaseball.playball.pitchmanager import PitchManager
from blaseball.playball.gamestate import GameRules, GameState
from blaseball.util.messenger import Messenger
from blaseball.stats.teams import Team, League
from blaseball.stats.lineup import Lineup
from blaseball.stats.statclasses import Stat
from blaseball.stats import stats as s
from data import teamdata
from blaseball.settings import Settings

from typing import Tuple


def run_game(home_lineup: Lineup, away_lineup: Lineup, stadium, rules=None) -> Tuple[GameState, int]:
    if rules is None:
        rules = GameRules()

    null_messenger = Messenger()

    ballgame = BallGame(null_messenger, home_lineup, away_lineup, stadium, rules)

    pitch_manager = PitchManager(ballgame.state, ballgame.messenger)

    ballgame.start_game()
    while ballgame.live_game:
        ballgame.send_tick()

    return ballgame.state, ballgame.tick_count


def build_lineup(team: Team, pitcher_index: int) -> Lineup:
    new_lineup = Lineup(f"Linup index {pitcher_index}")
    players = team.players[:10]
    players_rotated = players[pitcher_index:] + players[:pitcher_index]

    new_lineup.add_player(players_rotated[0], 'pitcher')
    new_lineup.add_player(players_rotated[1], 'catcher')
    new_lineup.add_player(players_rotated[2], 'shortstop')
    new_lineup.add_player(players_rotated[3], 'basepeep 1')
    new_lineup.add_player(players_rotated[4], 'basepeep 2')
    new_lineup.add_player(players_rotated[5], 'basepeep 3')
    new_lineup.add_player(players_rotated[6], 'fielder 1')
    new_lineup.add_player(players_rotated[7], 'fielder 2')
    new_lineup.add_player(players_rotated[8], 'fielder 3')
    new_lineup.add_player(players_rotated[9], 'extra 1')
    assert new_lineup.validate()[0]

    return new_lineup


def print_stats_distribution(name: str) -> None:
    # TODO: this breaks on random stats for TBD reasons
    sample = s.pb.df[name].iloc[0]
    try:
        if isinstance(sample, float):
            print(
                f"{name}: "
                f"min {s.pb.df[name].min():.3f} - {s.pb.players[s.pb.df[name].idxmin()]['name']}  "
                f"max {s.pb.df[name].max():.3f} - {s.pb.players[s.pb.df[name].idxmax()]['name']}  "
                f"mean {s.pb.df[name].mean():.3f}  "
                f"median {s.pb.df[name].median():.3f}  "
                f"mode {s.pb.df[name].mode()[0]:.3f}  "
                f"stdv {s.pb.df[name].std():.3f}"
            )
        elif isinstance(sample, int):
            print(
                f"{name}: "
                f"min {s.pb.df[name].min()} - {s.pb.players[s.pb.df[name].idxmin()]['name']}  "
                f"max {s.pb.df[name].max()} - {s.pb.players[s.pb.df[name].idxmax()]['name']}  "
                f"mean {s.pb.df[name].mean()}  "
                f"median {s.pb.df[name].median()}  "
                f"mode {s.pb.df[name].mode()[0]}  "
                f"stdv {s.pb.df[name].std()}"
            )
    except TypeError:
        print(f"Could not evaluate stats for {name}")


@pytest.mark.skip("Skip this because it takes forever - manually run this as-needed")
def test_all_stats(stadium_a, messenger_1):
    Settings.players_per_team = 10

    team_names = teamdata.TEAMS_99
    shuffle(team_names)
    league = League(s.pb, team_names[0:2])
    
    print("x")
    a_total_wins = 0
    a_total_runs = 0
    b_total_wins = 0
    b_total_runs = 0

    print(build_lineup(league[0], 0).string_summary())
    print("\n* VS *\n")
    print(build_lineup(league[1], 0).string_summary())

    for i in range(200):
        lineup_a = build_lineup(league[0], i % 10)
        lineup_b = build_lineup(league[1], (i // 10) % 10)
        a_is_home = i >= 100

        if a_is_home:
            home_lineup = lineup_a
            away_lineup = lineup_b
        else:
            home_lineup = lineup_b
            away_lineup = lineup_a

        final_state, ticks = run_game(home_lineup, away_lineup, stadium_a)
        print(f"[{i}] Final score: {final_state.scores} in {ticks} ticks")

        if final_state.scores[0] > final_state.scores[1]:
            a_total_wins += 1
        else:
            b_total_wins += 1

        a_total_runs += final_state.scores[0]
        b_total_runs += final_state.scores[1]

    print("\n\n** FINAL SCORES **")
    print(f"{league[0]}: {a_total_wins} wins, {a_total_runs} runs")
    print(f"{league[1]}: {b_total_wins} wins, {b_total_runs} runs")

    s.pb.save_all_players_to_pb()

    for stat in s.pb.stats:
        print_stats_distribution(stat)

    s.pb.df.to_csv(r"C:\temp\bstats.csv")


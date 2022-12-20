"""A lot of classes use an "if name == __main__" block to run quick tests. These often require teams, games, etc.

This module creates a few placeholders so we can copy less code."""

from blaseball.stats import players, teams, lineup, stadium
from blaseball.stats import stats as s
from blaseball.playball import gamestate
from blaseball.util import messenger
from data import teamdata

from random import shuffle


team_names = teamdata.TEAMS_99
shuffle(team_names)

league = teams.League(s.pb, team_names[0:2])

player = league[0]

home_lineup = lineup.Lineup("Home Lineup")
home_lineup.generate(league[0])
away_lineup = lineup.Lineup("Away Lineup")
away_lineup.generate(league[1])

stadium = stadium.Stadium(stadium.ANGELS_STADIUM)

game_state = gamestate.GameState(home_lineup, away_lineup, stadium, gamestate.GameRules())

messenger = messenger.Messenger()

print("Setup complete.")

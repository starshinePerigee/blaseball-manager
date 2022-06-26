from random import shuffle
from time import perf_counter

from blaseball.stats import players, teams, lineup
from blaseball.playball import gamestate
from data import teamdata

t_zero = perf_counter()
print("Generating League...")
pb = players.PlayerBase()
team_names = teamdata.TEAMS_99
league = teams.League(pb, team_names)
t_league = perf_counter()

print("Generating Lineups...")
lineups = {}
for team in league:
    team_lineup = []
    for i in range(0, 5):
        new_lineup = lineup.Lineup(f"{team.name} Lineup {i}")
        new_lineup.generate(team)
        team_lineup.append(new_lineup)
    lineups[team.name] = team_lineup
t_lineups = perf_counter()

total_games = {team: 0 for team in team_names}
total_wins = {team: 0 for team in team_names}

for day in range(1, 100):
    print(f"\r\n\r\n~~~~~~~~~~ DAY {day} ~~~~~~~~~~\r\n")
    shuffle(team_names)
    for game in range(0, int(len(team_names) / 2)):
        t_home = team_names[game]
        l_home = lineups[t_home][game % 5]
        t_away = team_names[game+int(len(team_names) / 2)]
        l_away = lineups[t_away][game % 5]

        g = gamestate.GameState(l_home, l_away)
        while not g.complete:
            g.next()

        # print(league[t_home])
        # print(l_home.string_summary())
        # print("\r\n\t\t* * * VS * * *\r\n")
        # print(league[t_away])
        # print(l_away.string_summary())

        print(g.summary[-1] + "\r\n")
        total_games[t_home] += 1
        total_games[t_away] += 1
        if g.scores[0] > g.scores[1]:
            total_wins[t_home] += 1
        else:
            total_wins[t_away] += 1

t_games = perf_counter()

print("FINAL RECORD")
for team in team_names:
    print(f"{team}: {total_games[team]} games played, {total_wins[team]}-{total_games[team]-total_wins[team]}")

print(f"League generation time: {t_league - t_zero}")
print(f"Lineup generation time: {t_lineups - t_league}")
number_games = 99 * int(len(team_names)/2)
print(f"Total game time: {t_games - t_lineups} ({(t_games - t_lineups)/number_games}) per game.")
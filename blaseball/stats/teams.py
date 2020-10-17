"""
Contains info for handling team actions and team statistics.
"""


from blaseball.settings import Settings


class Team:
    """
    Represents a single team, with team stats and team methods.
    """
    def __init__(self, name, players=None):
        self.name = name
        self.players = players
        for player in self.players:
            player["team"] = name

    def __len__(self):
        return len(self.players)

    def __str__(self):
        return f"{self.name} ({len(self)})"

    def __repr__(self):
        return (f"<{self.__module__}.{self.__class__.__name__} "
                f"'{self['name']}' "
                f"at {hex(id(self))}>")


class League:
    """
    This contains links to every team and contains functions for whole-league
    manipulations.
    """
    def __init__(self, playerbase, team_names=None):
        self.teams = {}
        for team_name in team_names:
            self.teams[team_name] = Team(team_name,
                                         playerbase.new_players(Settings.players_per_team))

    def __len__(self):
        return len(self.teams.keys())

    def __str__(self):
        return f"THE LEAGUE ({len(self)})"

    def __repr__(self):
        return (f"<{self.__module__}.{self.__class__.__name__} "
                f"'THE LEAGUE' ({len(self)})"
                f"at {hex(id(self))}>")


if __name__ == "__main__":
    from blaseball.stats import players
    from data import teamdata
    pb = players.PlayerBase()
    l = League(pb, teamdata.TEAMS_99)
    print(l)
    for p in pb:
        print(p)

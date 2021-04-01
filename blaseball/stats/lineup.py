"""
This function manages a single lineup - ie, a team configuration that is going to go play
a game of blaseball.
"""

from blaseball import settings


class Lineup:
    running_number = 0

    @staticmethod
    def new_num():
        Lineup.running_number += 1
        return Lineup.running_number

    def __init__(self, name=None):
        if name is None:
            self.name = "new lineup " + str(Lineup.new_num())
        else:
            self.name = name

        self.batting_order = []
        self.pitcher = None
        self.fielding = {
            "Basepeeps": [],
            "SS": None,
            "C": None,
            "RF": None,
            "CF": None,
            "LF": None,
            "Extras": [],
        }

    def get_all_players(self):
        all_players = []


    def generate(self, team, strength):
        pass

    def validate(self):
        """
        Make sure a lineup is still valid:
        - all players are on the same team
        - lineup has at least min_players players
        - lineup has a pitcher
        - all lineup players have positions
        - all positions are in lineup
        - there's a basepeep for every p
        - all players are in playing condition (TBD)
        """
        return (False, "Not yet implimented")

    def print_summary(self):
        pass

    def __str__(self):
        pass

    def __repr__(self):
        return f"Lineup {self.name} at {hex(id(self))}"


if __name__ == "__main__":
    from blaseball.stats import players, teams
    from data import teamdata
    pb = players.PlayerBase()
    l = teams.League(pb, teamdata.TEAMS_99)

    lu = Lineup("main lineup")
    lu.generate(l)
"""
Contains database info and stats for a blaseball player and the playerbase.
"""

import random

import pandas as pd

from data import playerdata

class Player:
    #default values
    CORE_STATS = {
        "name": "UNDEFINED PLAYER",
        "team": "N/A TEAM",
    }
    BASE_STATS = {
        "hitting": 0, # base hitting ability
        "running": 0, # base baserunning ability
        "catching": 0, # base defense ability
        "pitching": 0, # base pitching ability
        "power": 0,
        # for pitchers: pitch speed/power,
        # for hitters: clean hit power
        # for defense: throw speed
        "technique": 0,
        # for pitchers: pitch accuracy
        # for batters: hit "direction" - reduce chance of fly out
        # for defence: chance of misplay
        "strategy": 0,
        # for pitchers: pitch choice
        # for batters: pitch prediction
        # for defense: chance of incorrect fielder's choice,
        "speed": 0,
        # for batters: fastball defense,
        # for runners: base speed,
        # for pitchers: stealing defense
        # for defenders: ground out chances
        "durability": 0, # stat loss per game
    }
    BONUS_STATS = {
        "fingers": 9,
        "element": "Basic",
        "vibes": 0,
        "dread": 0,
    }
    ALL_STATS_KEYS = list(CORE_STATS.keys()) + list(BASE_STATS.keys())\
                     + list(BONUS_STATS.keys())
    COMBINED_STATS = [CORE_STATS, BASE_STATS, BONUS_STATS]

    @staticmethod
    def generate_name():
        first_name = random.choice(playerdata.PLAYER_FIRST_NAMES)
        last_name = random.choice(playerdata.PLAYER_LAST_NAMES)
        return f"{first_name} {last_name}".title()

    def __init__(self, df_row):
        self.s = df_row

    def initialize(self):
        for statset in Player.COMBINED_STATS:
            for stat in list(statset.keys()):
                self.s[stat] = statset[stat]

    def randomize(self):
        self.s["name"] = Player.generate_name()
        for stat in Player.BASE_STATS:
            self.s[stat] = random.random()
        self.s["fingers"] += 1
        self.s["element"] = random.choice(playerdata.PLAYER_ELEMENTS)

    #TODO: more indexing


class PlayerBase:
    """this class contains the whole set of players and contains operations
    to execute actions on batches of players"""
    def __init__(self):
        self.players = pd.DataFrame(columns=Player.ALL_STATS_KEYS)

    def new_players(self, num_players):
        """batch create new players"""
        # add new players as empty rows:
        old_len = len(self)
        self.players = self.players.reindex(self.players.index.tolist()
                                            + list(range(old_len, old_len+num_players)))
        new_players = self.players.iloc[old_len:old_len+num_players]
        for new_player in new_players.iterrows():
            player = Player(new_player[1])
            player.initialize()
            player.randomize()

    def __len__(self):
        return len(self.players.index)

    #TODO: indexing


if __name__ == "__main__":
    pb = PlayerBase()
    pb.new_players(10)
    print(pb.players)
"""
Contains database info and stats for a blaseball player and the playerbase.

Typical workflow:
maintain a single collection of players in the single PlayerBase. Player
info is pulled as Player instances. Player methods should update the
playerbase entries as-needed (and vice versa)
"""

import random
from collections.abc import Mapping, MutableMapping, Hashable
from typing import Union, List

import pandas as pd
from numpy import integer

from data import playerdata
from blaseball.stats import traits


class Player(Mapping):
    """
    A representation of a single player.

    This includes a link to a line in a PlayerBase, which uses a pandas
    dataframe to store the bulk of numeric ratings and stats. However, player is
    implemented as a separate class to support advanced functionality best not
    stored in a dataframe (like play logs, special ability functions, etc.)
    """

    # default values
    CORE_ATTRIBUTES = {
        "name": "UNDEFINED PLAYER",
        "team": "N/A TEAM",
        "number": -1
    }
    PERSONALITY_FIVE = [
        "determination",
        "enthusiasm",
        "stability",
        "insight",
        "mysticism"
    ]
    
    DETERMINATION_RATINGS = ["power", "force", "bravery", "endurance", "cool"]
    ENTHUSASM_RATINGS = ["contact", "speed", "trickery", "extroversion", "hang"]
    STABILITY_RATINGS = ["control", "accuracy", "positivity", "support"]
    INSIGHT_RATINGS = ["discipline", "awareness", "strategy", "introversion", "patience"]
    MYSTICISM_RATINGS = ["recovery", "sparkle", "teaching"]

    BATTING_RATINGS = ["power", "contact", "control", "discipline"]
    BASERUNNING_RATINGS = ["speed", "bravery", "timing"]
    DEFENSE_RATINGS = ["reach", "reaction", "timing"]
    PITCHING_RATINGS = ["force", "accuracy", "trickery"]
    EDGE_RATINGS = ["strategy", "sparkle", "clutch"]
    CONSTITUTION_RATINGS = ["endurance", "positivity", "extroversion", "introversion", "recovery"]
    SOCIAL_RATINGS = ["teaching", "patience", "cool", "hang", "support"]

    DEEP_RATINGS = [
        "power",
        "contact",
        "control",
        "discipline",
        "speed",
        "timing",
        "reaction",
        "force",
        "accuracy",
        "trickery",
        "awareness",
        "strategy",
        "sparkle",
        "endurance",
        "positivity",
        "extroversion",
        "introversion",
        "recovery",
        "teaching",
        "patience",
        "cool",
        "hang",
        "support",
    ]
    DERIVED_DEEP = [
        "reach",  # speed
        "reaction",  # discipline
        "timing",  # awareness
        "throwing",  # accuracy
        "clutch",  # bravery
    ]
    DERIVED_RATINGS = [
        "total_offense",
        "total_defense",
        "batting",
        "baserunning",
        "defense",
        "pitching",
        "edge",
        "constitution",
        "social"
    ]

    CONDITION_STATUS = {
        "stamina": 1.0,
        "vibes": 1.0,
        "corporeality": 1.0,
    }
    BONUS_STATS = {
        "fingers": 9,
        "is_pitcher": False,
        "element": "Basic",
    }

    COMBINED_STATS = [
        CORE_ATTRIBUTES,
        PERSONALITY_FIVE,
        DEEP_RATINGS,
        DERIVED_DEEP,
        DERIVED_RATINGS,
        CONDITION_STATUS,
        BONUS_STATS
    ]
    ALL_KEYS = []
    for statset in COMBINED_STATS:
        if isinstance(statset, list):
            ALL_KEYS += statset
        else:
            ALL_KEYS += list(statset.keys())

    player_class_id = 1000  # unique ID for each generation of a player,
    # used to verify uniqueness

    @staticmethod
    def generate_name() -> str:
        """Creates a random name from the playerdata lists.
        Guaranteed to be great."""
        first_name = random.choice(playerdata.PLAYER_FIRST_NAMES)
        last_name = random.choice(playerdata.PLAYER_LAST_NAMES)
        return f"{first_name} {last_name}".title()

    @staticmethod
    def new_cid() -> int:
        Player.player_class_id += 1
        return Player.player_class_id

    def __init__(self) -> None:
        self.cid = Player.new_cid()  # players "Character ID", a unique identifier
        self.pb = None  # pointer to the row of playerbase containing this player's stats
        self.traits = []
        # you MUST call initialize after this.

    def initialize(self, playerbase: 'PlayerBase') -> None:
        """Create / reset all stats to default values.
        Counts as a new player"""
        self.pb = playerbase
        for statset in Player.COMBINED_STATS:
            if isinstance(statset, list):
                for stat in statset:
                    self[stat] = 0.0
            else:
                for stat in list(statset.keys()):
                    self[stat] = statset[stat]

    def generate_player_number(self) -> int:
        """dumb fun function to create a player number based partially on CID"""
        unusual = random.random() < 0.10

        low_thresh = max(random.randrange(-20, 20, 2), (-20 if unusual else 0))
        high_thresh = random.randrange(45, random.randrange(50, (1000 if unusual else 100)))
        base = self.cid % 100

        if (base < high_thresh) and (base > low_thresh) and not unusual:
            return base
        else:
            ones = base % 10
            tens = int(((base % high_thresh) + low_thresh) / 10) * 10
            return ones + tens

    def randomize(self) -> None:
        """Generate random values for applicable stats.
        Call initialize() first.
        Counts as a new player."""
        self["name"] = Player.generate_name()
        self["number"] = self.generate_player_number()



        #
        # for stat in Player.BASE_STATS:
        #     self[stat] = random.random()
        # swing_weights = {}
        # for stat in Player.SWING_STATS:
        #     swing_weights[stat] = random.random()
        # total_weight = sum(swing_weights.values())
        # # we want these stats to average to 0.5, so build your factor:
        # swing_factor = (len(Player.SWING_STATS) * 0.5 / total_weight)
        # for stat in swing_weights:
        #     self[stat] = swing_weights[stat] * swing_factor
        #
        # self["fingers"] += 1
        # self["element"] = random.choice(playerdata.PLAYER_ELEMENTS)

    def derive(self) -> None:
        pass

    def add_trait(self, trait: traits.Trait) -> None:
        self.traits += trait
        for stat in trait:
            self[stat] += trait[stat]

    def remove_trait(self, trait: traits.Trait) -> None:
        if trait not in self.traits:
            raise KeyError(f"Trait {trait} not on player {self}")

    def assign(self, values: Union[dict, pd.Series, 'Player']) -> None:
        if isinstance(values, Player):
            self.assign(values.stat_row())
            return
        elif isinstance(values, pd.Series):
            keys = values.index
        else:
            keys = values.keys()

        for key in keys:
            self[key] = values[key]

    def stat_row(self) -> pd.Series:
        if self.pb is None:
            raise RuntimeError(f"{self} not linked to a valid PlayerBase! Call player.initialize"
                               f"before using this player!")
        else:
            return self.pb.df.loc[self.cid]

    def df_index(self) -> int:
        """get the CID / dataframe index of this player."""
        if self.stat_row().name == self.cid:
            return self.cid
        else:
            raise RuntimeError(f"Warning! Playerbase Dataframe index {self.stat_row().name} "
                               f"does not match player CID {self.cid}, likely playerbase corruption.")

    def __getitem__(self, item) -> object:
        if item == 'cid':
            return self.cid
        else:
            return self.stat_row()[item]

    def __setitem__(self, item: Hashable, value: object) -> None:
        self.pb.df.loc[self.cid][item] = value

    def __iter__(self) -> iter:
        return iter(self.stat_row())

    def __len__(self) -> int:
        return len(self.stat_row())

    def __eq__(self, other: Union['Player', pd.Series, dict]) -> bool:
        if isinstance(other, Player):
            return other.cid == self.cid
        else:
            if isinstance(other, pd.Series):
                keys = other.index
            else:
                keys = other.keys()
            for stat in keys:
                try:
                    if self[stat] != other[stat]:
                        return False
                except (KeyError, TypeError):
                    return False
            return True

    def total_stars(self) -> str:
        # """Return a string depiction of this player's stars"""
        # average = (self.stat_row()[Player.BASE_STATS].sum()
        #            / len(Player.BASE_STATS)) * 5  # 0-5 star rating
        # stars = int(average)
        # half = average % 1 >= 0.5
        # return "*"*stars + ('-' if half else '')
        return "***"

    def __str__(self) -> str:
        return(f"[{self.cid}] "
               f"'{self['name']}' ({self['team']}) "
               f"{self.total_stars()}"
               )

    def __repr__(self) -> str:
        return (f"<{self.__module__}.{self.__class__.__name__} "
                f"[{self.cid}] "
                f"'{self['name']}' "
                f"(c{self.cid}) at {hex(id(self))}>")


class PlayerBase(MutableMapping):
    """this class contains the whole set of players and contains operations
    to execute actions on batches of players

    It has two parts: a dataframe df, which contains the actual stats
        with players as rows and stats as columns,
    and players, a dict indext by CID which contains pointers to the Players objects.
    """
    def __init__(self, num_players: int = 0) -> None:
        self.df = pd.DataFrame(columns=Player.ALL_KEYS)
        self.players = {}

        if num_players > 0:
            self.new_players(num_players)

    def new_players(self, num_players: int) -> List[Player]:
        """batch create new players. Returns the new players as a list
        of Player"""

        finished_players = []
        for i in range(num_players):
            # create a set of new players:
            player = Player()
            self.df.loc[player.cid] = None
            player.initialize(self)
            player.randomize()

            self.players[player.df_index()] = player

            finished_players.append(player)
        return finished_players

    def verify_players(self) -> bool:
        """Because we have a dataframe with player stats, and a separate
        list of player objects that are linked, it's important to make sure
        these two data sources don't get out of sync with each other.

        This function performs a validation to make sure that each Player
        links to a valid dataframe row and each dataframe row has a valid
        Player.
        """
        try:
            for key in self.players.keys():
                if self.players[key].cid != key:
                    raise RuntimeError(
                        f"Player CID and key mismatch:"
                        f"key {key}, "
                        f"player {self.players[key]}"
                    )
                if self[key] != self.players[key]:
                    raise RuntimeError(
                        f"Player verification failure! "
                        f"Player {key} mismatch: "
                        f"{self[key]} vs {self.players[key]}"
                    )
            for key in self.df.index:
                if self.players[key] != self.df.loc[key]:
                    raise RuntimeError(
                        f"Player verification failure! "
                        f"Dataframe row key {key} mismatch: "
                        f"{self.df.loc[key]['name']} "
                        f"vs {self.players[key]}"
                    )
        except KeyError as e:
            raise RuntimeError(f"KeyError during verification: {e}")
        return True

    def __len__(self) -> int:
        if len(self.players) != len(self.df.index):
            raise RuntimeError(
                f"Player/df mismatch!"
                f"{len(self.players)} players vs "
                f"{len(self.df.index)} dataframe rows."
            )
        return len(self.df.index)

    def __getitem__(self, key: Hashable) -> Union[Player, List[Player]]:
        if isinstance(key, str):
            item_row = self.df.loc[self.df['name'] == key.title()]
            if len(item_row) > 1:
                # you have duplicate names!
                pass
            item_row = item_row.iloc[0]
            return self.players[item_row.name]
        elif isinstance(key, (int, integer)):
            return self.players[key]
        elif isinstance(key, (range, list)):
            return [self[i] for i in key]
        else:
            raise KeyError(f"Could not index by type {type(item)}, expected CID int or name string.")

    def iloc(self, key: Union[int, slice, range]) -> Union[Player, List[Player]]:
        """
        You should not be able to do this. This is a mapping, so order doesn't matter.
        But dang it, sometimes you just need a player or a handful, and you don't care who you get.
        Don't expect this to be anything but a random selection!
        """
        all_cids = list(self.players.keys())

        if isinstance(key, int):
            return self[all_cids[key]]
        if isinstance(key, range):
            key = slice(key.start, key.stop, key.step)

        return_players = []
        for cid in all_cids[key]:
            return_players.append(self[cid])
        return return_players

    def __setitem__(self, key: Hashable, value: Union[Player, pd.Series]) -> None:
        """
        If the value player is in the playerbase, that player will be duplicated!
        Take care with this function!
        """
        self[key].assign(value)

    def __delitem__(self, key: Hashable) -> None:
        del self.players[key]
        self.df.drop(key)

    def __str__(self) -> str:
        return_str = f"PlayerBase {len(self)} players x "
        return_str += (f"{len(list(self.df.columns))} cols"
                      f"\r\n{list(self.df.columns)}")

        if len(self) <= 10:
            for player in self.iloc(range(len(self))):
                return_str += "\r\n" + str(player)
        else:
            for player in self.iloc(range(0, 5)):
                return_str += "\r\n" + str(player)
            return_str += "\r\n..."
            for player in self.iloc(range(len(self)-5, len(self))):
                return_str += "\r\n" + str(player)
        return return_str

    def __repr__(self) -> str:
        return(f"<{self.__module__}.{self.__class__.__name__} "
               f"[{len(self)} rows x "
               f"{len(self.df.columns)} cols] "
               f"at {hex(id(self))}")

    def __iter__(self) -> iter:
        return iter(self.players.values())


if __name__ == "__main__":
    pb = PlayerBase(1000)
    print(pb)
    p = Player()
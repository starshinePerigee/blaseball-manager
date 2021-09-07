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
ENTHUSIASM_RATINGS = ["contact", "speed", "trickery", "extroversion", "hang"]
STABILITY_RATINGS = ["control", "accuracy", "positivity", "support"]
INSIGHT_RATINGS = ["discipline", "awareness", "strategy", "introversion", "patience"]
MYSTICISM_RATINGS = ["recovery", "sparkle", "teaching"]

BATTING_RATINGS = ["power", "contact", "control", "discipline"]
BASERUNNING_RATINGS = ["speed", "bravery", "timing"]
DEFENSE_RATINGS = ["reach", "reaction", "throwing"]
PITCHING_RATINGS = ["force", "accuracy", "trickery", "awareness"]
EDGE_RATINGS = ["strategy", "sparkle", "clutch"]
CONSTITUTION_RATINGS = ["endurance", "positivity", "extroversion", "introversion", "recovery"]
SOCIAL_RATINGS = ["teaching", "patience", "cool", "hang", "support"]

DEEP_RATINGS = [
    "power",
    "contact",
    "control",
    "discipline",
    "speed",
    "bravery",
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
RATING_PERSONALITY_LOOKUP = {}
for rating_list, personality in zip([
    DETERMINATION_RATINGS,
    ENTHUSIASM_RATINGS,
    STABILITY_RATINGS,
    INSIGHT_RATINGS,
    MYSTICISM_RATINGS,
],["determination", "enthusiasm", "stability", "insight", "mysticism"]):
    for rating in rating_list:
        RATING_PERSONALITY_LOOKUP[rating] = personality
DERIVED_DEEP = [
    "reach",  # speed
    "reaction",  # discipline
    "timing",  # awareness
    "throwing",  # accuracy
    "clutch",  # bravery
]
DERIVED_DEEP_LOOKUP = {
    rating[0]: rating[1] for rating in
    zip(DERIVED_DEEP, ["speed", "discipline", "awareness", "accuracy", "bravery"])
}
DERIVED_RATINGS = [
    "total_offense",
    "total_defense",
    "total_off_field",
    "batting",
    "baserunning",
    "defense",
    "pitching",
    "edge",
    "constitution",
    "social"
]
RATING_DESCRIPTORS = {
    "overall_descriptor": "Unevaluated Player",
    "offense_descriptor": "Hits for Beans",
    "defense_descriptor": "Can't Catch A Cold",
    "personality_descriptor": "Is Smol Bean",
}
POSITION_INFO = {
    "offense_position": "Bench",
    "defense_position": "Bullpen"
}
CONDITION_STATUS = {
    "stamina": 1.0,
    "vibes": 1.0,
    "corporeality": 1.0,
    "condition": 1.0
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
    BONUS_STATS,
    RATING_DESCRIPTORS,
    POSITION_INFO
]
ALL_KEYS = []
for statset in COMBINED_STATS:
    if isinstance(statset, list):
        ALL_KEYS += statset
    else:
        ALL_KEYS += list(statset.keys())

BATTING_WEIGHTS = (("power", 2), ("contact", 3), ("control", 2), ("discipline", 1))
BASERUNNING_WEIGHTS = (("speed", 3), ("bravery", 1), ("timing", 2))
DEFENSE_WEIGHTS = (("reach", 1), ("reaction", 1), ("throwing", 1))
PITCHING_WEIGHTS = (("force", 2), ("accuracy", 1), ("trickery", 1.5), ("awareness", 0.5))
EDGE_WEIGHTS = (("strategy", 1), ("sparkle", 1), ("clutch", 1))
DURABILITY_WEIGHTS = (("endurance", 1), ("positivity", 1), ("extroversion", 1),
                      ("introversion", 1), ("recovery", 2))
SOCIAL_WEIGHTS = (("teaching", 2), ("patience", 2), ("cool", 1), ("hang", 1), ("support", 1))
TOTAL_OFFENSE_WEIGHTS = (("batting", 2), ("baserunning", 1), ("edge", 0.5))
TOTAL_DEFENSE_WEIGHTS_PITCHING = (("pitching", 2), ("defense", 1), ("edge", 0.5))
TOTAL_DEFENSE_WEIGHTS_FIELDING = (("pitching", 0.5), ("defense", 2), ("edge", 0.5))
TOTAL_OFF_FIELD_WEIGHTS = (("constitution", 2), ("social", 2))


class Player(Mapping):
    """
    A representation of a single player.

    This includes a link to a line in a PlayerBase, which uses a pandas
    dataframe to store the bulk of numeric ratings and stats. However, player is
    implemented as a separate class to support advanced functionality best not
    stored in a dataframe (like play logs, special ability functions, etc.)
    """

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
        for statset in COMBINED_STATS:
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

        for stat in PERSONALITY_FIVE:
            self[stat] = random.random()

        for i in range(0, random.randrange(3, 6)):
            self.add_trait(traits.personality_traits.draw())

        for stat in DEEP_RATINGS:
            self[stat] = random.random() * max(self[RATING_PERSONALITY_LOOKUP[stat]], 0.5)
            if self[RATING_PERSONALITY_LOOKUP[stat]] > 1:
                # this is a dumb hack - contrary to the plan, this can result in deep stats higher than
                # the respective personalities. In my defense, it'll be rare and cool when it happens.
                self[stat] += self[RATING_PERSONALITY_LOOKUP[stat]] - 1

        for stat in DERIVED_DEEP_LOOKUP:
            self[stat] = self[DERIVED_DEEP_LOOKUP[stat]]

        self.derive()

        self["element"] = random.choice(playerdata.PLAYER_ELEMENTS)

    def _derive_weighted(self, stat, weights):
        weight = sum([x[1] for x in weights])
        total = sum([self[x[0]] * x[1] for x in weights])
        self[stat] = total / weight

    def write_descriptors(self) -> None:
        """Updates the descriptor fields for this player"""

        self["overall_descriptor"] = "The Observed"
        self["offense_descriptor"] = "Possible Hitter"
        if self["is_pitcher"]:
            self["defense_descriptor"] = "Might Pitch"
        else:
            self["defense_descriptor"] = "Lackluster Fielder"

    def derive(self) -> None:
        for stat, weights in zip(
                ["batting", "baserunning", "defense", "pitching", "edge",
                 "durability", "social", "total_offense", "total_off_field"],
                [BATTING_WEIGHTS, BASERUNNING_WEIGHTS, DEFENSE_WEIGHTS, PITCHING_WEIGHTS,
                 EDGE_WEIGHTS, DURABILITY_WEIGHTS, SOCIAL_WEIGHTS, TOTAL_OFFENSE_WEIGHTS,
                 TOTAL_OFF_FIELD_WEIGHTS]
        ):
            self._derive_weighted(stat, weights)

        self["is_pitcher"] = self["pitching"] > self["defense"] * 1.1

        if self["is_pitcher"]:
            self._derive_weighted("total_defense", TOTAL_DEFENSE_WEIGHTS_PITCHING)
        else:
            self._derive_weighted("total_defense", TOTAL_DEFENSE_WEIGHTS_FIELDING)

        self.write_descriptors()

        self["fingers"] += 1

    def add_trait(self, trait: traits.Trait) -> None:
        self.traits += [trait]
        for stat in trait:
            self[stat] += trait[stat]
        self.derive()

    def remove_trait(self, trait: traits.Trait) -> None:
        if trait not in self.traits:
            raise KeyError(f"Trait {trait} not on player {self}")
        else:
            for stat in trait:
                self[stat] -= trait[stat]
        self.traits.remove(trait)
        self.derive()

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

    def __getitem__(self, item) -> float:
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

    @staticmethod
    def _to_stars(stat: float) -> str:
        """converts a 0 - 2 float number into a star string"""
        stars = int(stat * 5)
        half = (stat * 5) % 1 >= 0.5
        star_string = "*" * stars + ('-' if half else '')
        if len(star_string) > 5:
            star_string = star_string[0:5] + " " + star_string[5:]
        elif len(star_string) == 0:
            return "0"
        return star_string

    def total_stars(self) -> str:
        # """Return a string depiction of this player's stars"""
        return self._to_stars((self["total_offense"] + self["total_defense"]) / 2)

    def text_breakdown(self) -> str:
        text = (
            f"{self['name']} {self.total_stars()}\r\n"
            f"\r\n~ ~ ~ ~ ~ \r\n\r\n"
            f"{self['number']}: {self['name']}\r\n"
            f"{self.total_stars()} {self['overall_descriptor']}\r\n"
            f"{self['offense_position']}\r\n{self['defense_position']}\r\n"
            f"RBI: ?? OPS: ???\r\nERA: --- WHIP: ---\r\n\r\n"
            f"Personality: {self['personality_descriptor']}\r\n"
            f"Offense: {self._to_stars(self['total_offense'])} {self['offense_descriptor']}\r\n"
            f"Defense: {self._to_stars(self['total_defense'])} {self['defense_descriptor']}\r\n"
            f"Off-Field: {self._to_stars(self['total_off_field'])}\r\n"
            f"\r\n"
            f"Condition: {self['condition']}\r\n"
            f"\r\n~ ~ ~ ~ ~\r\n\r\n"
        )
        text += "Key Ratings\r\n\r\n"
        text += "\r\n".join(
            [f"{r.title()}: {self[r] * 100:.0f}%" for r in ["stamina", "vibes", "corporeality"]])
        text += "\r\n\r\n"
        text += "\r\n".join(
            [f"{r.title()}: {self._to_stars(self[r])}" for r in [
                "batting", "baserunning", "defense", "pitching", "edge", "constitution", "social"
            ]]
        )
        text += "\r\n\r\n"
        text += "\r\n".join(
            [f"{r.title()}: {self._to_stars(self[r])}" for r in [
                "determination", "enthusiasm", "stability", "insight", "mysticism"
            ]]
        )
        text += "\r\n\r\n~ ~ ~ ~ ~\r\n\r\n"
        text += "Traits and Conditions\r\n\r\n"
        text += "\r\n".join([
            trait.nice_string() for trait in self.traits
        ])
        text += "\r\n\r\n~ ~ ~ ~ ~\r\n\r\n"
        text += "Deep Ratings\r\n"
        for top, group in zip(DERIVED_RATINGS[3:], [
            BATTING_RATINGS, BASERUNNING_RATINGS, DEFENSE_RATINGS, PITCHING_RATINGS,
            EDGE_RATINGS, CONSTITUTION_RATINGS, SOCIAL_RATINGS
        ]):
            text += f"\r\n{top.title()}:\r\n"
            for rating in group:
                text += f"{rating.title()} {self._to_stars(self[rating])}\r\n"

        return text

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
        self.df = pd.DataFrame(columns=ALL_KEYS)
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
            raise KeyError(f"Could not index by type {type(key)}, expected CID int or name string.")

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
    pb = PlayerBase(10)
    print(pb)
    print(pb[1001].text_breakdown())

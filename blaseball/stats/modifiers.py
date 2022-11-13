"""
Defines Modifiers - special things that affect a player, meant to be distinct and/or temporary
"""

from random import shuffle
from collections.abc import Mapping
from typing import Union, Dict, List, TYPE_CHECKING
if TYPE_CHECKING:
    from blaseball.stats.statclasses import Stat, PlayerBase

from data import playertraits
from blaseball.stats.stats import pb


class Modifier(Mapping):
    """
    Quote new_player_arch.txt:
    things that a player has that have effects.

    This is vague, which is difficult, but they're bundled together becuase we need to check *all of them* when it comes
    time to read a player's stat.

    These are the primary way for side systems (items, blessings, personality) to *temporarily* affect a player.

     A player can have dozens to hundreds of modifiers!
    """
    running_id = 0

    def __init__(self, name: str, stat_effects: Dict['Stat', float] = None, tags: List[str] = None):
        self.name = name
        if stat_effects is None:
            self.stat_effects = {}
        else:
            self.stat_effects = stat_effects
        if tags is None:
            self.tags = []
        else:
            self.tags = tags

    def __getitem__(self, item) -> Union[bool, float]:
        if item in self.stat_effects:
            return self.stat_effects[item]
        elif item in self.tags:
            return True

        for stat in self.stat_effects:
            if item == stat.name:
                return self.stat_effects[stat]

        return False

    def __iter__(self):
        return iter([stat.name for stat in self.stat_effects] + self.tags)

    def __len__(self):
        return len(self.stat_effects) + len(self.tags)

    def __contains__(self, item):
        if item in self.stat_effects or item in self.tags:
            return True
        else:
            return item in [stat.name for stat in self.stat_effects]

    def nice_string(self):
        rate_str = ""
        if len(self.stat_effects) > 0:
            rate_str += " ".join([f"{stat.name} {self.stat_effects[stat]:+.2f}" for stat in self.stat_effects])
        else:
            rate_str += "no stats"
        rate_str += " | "
        if len(self.tags) > 0:
            rate_str += " ".join(self.tags)
        else:
            rate_str += "no tags"
        return f"{self.name.title()} ({rate_str})"

    def __str__(self):
        return f"Trait '{self.name}': {len(self.stat_effects)} stat effects, {len(self.tags)} tags"

    def __repr__(self):
        return f"Trait '{self.name}' at {hex(id(self))}"


class PersonalityTraitDeck:
    """A helper class to pull personality modifiers from a deck. Used in player generation.
    """
    def __init__(self, traits: Dict[str, Dict[str, int]], pb: 'PlayerBase'):
        self.trait_names = list(traits.keys())
        self.traits = traits
        self.pb = pb

        self.shuffle_threshold = len(traits) / 2
        self.trait_deck = []
        self.shuffle()

    def parse_trait(self, name, trait: Dict[str, int]) -> Modifier:
        """Parse playertraits.py's PERSONALITY_TRAITS.
        This scales from (-20)-(+20) to (-2)-(+2)!"""
        modifier_dict = {}
        for stat_str in trait.keys():
            modifier_dict[self.pb.get_stats_by_name(stat_str)[0]] = trait[stat_str] / 10
        return Modifier(
            name,
            modifier_dict
        )

    def shuffle(self):
        """re-shuffle the traits deck"""
        self.trait_deck = self.trait_names.copy()
        shuffle(self.trait_deck)

    def draw(self):
        """
        Draw a new trait from the deck, shuffling if needed.
        """
        if len(self.trait_deck) < self.shuffle_threshold:
            self.shuffle()
        new_trait_name = self.trait_deck.pop(0)
        new_trait = self.parse_trait(new_trait_name, self.traits[new_trait_name])
        return new_trait

    def __len__(self):
        return len(self.trait_names)


default_personality_deck = PersonalityTraitDeck(playertraits.PERSONALITY_TRAITS, pb)


if __name__ == "__main__":
    pt = default_personality_deck

    for i in range(0, 3):
        nt = pt.draw()
        print(nt.nice_string())


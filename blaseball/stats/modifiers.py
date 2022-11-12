"""
Defines Modifiers - special things that affect a player, meant to be distinct and/or temporary
"""

# from random import shuffle, random
from collections.abc import Mapping
from typing import Union, Dict, List, TYPE_CHECKING
if TYPE_CHECKING:
    from blaseball.stats.statclasses import Stat
#
# from data import playertraits


class Modifier(Mapping):
    """
    Quote new_player_arch.txt:
    things that a player has that have effects.

    This is vague, which is difficult, but they're bundled together becuase we need to check *all of them* when it comes
    time to read a player's stat.

    These are the primary way for side systems (items, blessings, personality) to *temporarily* affect a player.

     A player can have have dozens to hundreds of modifiers!
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
        else:
            return item in self.tags

    def __iter__(self):
        return iter(list(self.stat_effects) + self.tags)

    def __len__(self):
        return len(self.stat_effects) + len(self.tags)

    def __contains__(self, item):
        return item in self.stat_effects or item in self.tags

    # def __add__(self, other: 'Modifier'):
    #     combined_dict =
#
#     def __add__(self, other: 'Trait') -> 'Trait':
#         new_ratings = self.ratings.copy()
#         for rating in other:
#             if rating in new_ratings:
#                 new_ratings[rating] = self[rating] + other[rating]
#             else:
#                 new_ratings[rating] = other[rating]
#         return Trait(ratings=new_ratings)
#
#     def __iadd__(self, other):
#         trait = self + other
#         self.ratings = trait.ratings
#         return self
#
#     def nice_string(self):
#         rate_str = " ".join([f"{short[rating]} {self.ratings[rating]*20:+.1f}" for rating in self.ratings])
#         return f"{self.name.title()} ({rate_str})"
#
#     def __str__(self):
#         rate_str = " ".join([f"{short[rating]}:{self.ratings[rating]:.2f}" for rating in self.ratings])
#         return f"Trait '{self.name}': {rate_str}"
#
#     def __repr__(self):
#         return f"Trait {self.name} at {hex(id(self))}"
#
#
# class TraitsList:
#     """A helper class to pull traits from a dictionary
#     """
#     def __init__(self, traits: list):
#         self.trait_names = []
#         self.traits = {}
#
#         for trait in traits:
#             self.trait_names += [trait]
#             self.traits[trait] = traits[trait]
#
#         self.shuffle_threshold = len(traits) / 2
#         self.trait_deck = []
#         self.shuffle()
#
#     def shuffle(self):
#         """re-shuffle the traits deck"""
#         self.trait_deck = self.trait_names.copy()
#         shuffle(self.trait_deck)
#
#     def draw(self):
#         """
#         Draw a new trait from the deck, shuffling if needed.
#         """
#         if len(self.trait_deck) < self.shuffle_threshold:
#             self.shuffle()
#         new_trait_name = self.trait_deck.pop()
#         new_trait = Trait(new_trait_name, self.traits[new_trait_name], normalize=True)
#         return new_trait
#
#
# personality_traits = TraitsList(playertraits.PERSONALITY_TRAITS)
#
# if __name__ == "__main__":
#     first_trait = list(playertraits.PERSONALITY_TRAITS.keys())[0]
#
#     t = Trait("First Trait", playertraits.PERSONALITY_TRAITS[first_trait], normalize=True)
#     print(t)
#
#     pt = personality_traits
#
#     for i in range(0, 3):
#         nt = pt.draw()
#         print(nt)
#         t += nt
#
#     print(t)

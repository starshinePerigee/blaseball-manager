"""
Defines a trait - any statistical modifier that is applied to a player.

They're basically fancy dictionaries
"""

from random import shuffle, random
from collections.abc import Mapping
from typing import Union, Type

from data import playertraits
from blaseball.util.statshortener import short


class Trait(Mapping):
    """
    A representation of a single trait.

    A trait is a modifier for a player - they affect stats, can have additional affects, and
    can be lost / gained / expire.

    Note that trait values are stored from 0-20, so this normalizes them as well.
    """

    def __init__(self, name=None, ratings: dict = None, normalize=False):
        if name is None:
            self.name = f"temp trait {str(random())[2:]}"
        else:
            self.name = name

        if normalize:
            self.ratings = {rating: ratings[rating] / 20 for rating in ratings}
            # rating no longer looks like a word
        else:
            self.ratings = ratings

    def __getitem__(self, item) -> Union[str, float]:
        try:
            return self.ratings[item]
        except KeyError:
            if item == "name":
                return self.name
            else:
                return 0.0

    def __iter__(self) -> iter:
        return iter(self.ratings)

    def __len__(self) -> int:
        return len(self.ratings)

    def __contains__(self, item):
        if item == "name":
            return True
        return item in self.ratings

    def __add__(self, other: 'Trait') -> 'Trait':
        new_ratings = self.ratings.copy()
        for rating in other:
            if rating in new_ratings:
                new_ratings[rating] = self[rating] + other[rating]
            else:
                new_ratings[rating] = other[rating]
        return Trait(ratings=new_ratings)

    def __iadd__(self, other):
        trait = self + other
        self.ratings = trait.ratings
        return self

    def __str__(self):
        rate_str = " ".join([f"{short[rating]}:{self.ratings[rating]:.2f}" for rating in self.ratings])
        return f"Trait '{self.name}': {rate_str}"

    def __repr__(self):
        return f"Trait {self.name} at {hex(id(self))}"


class TraitsList:
    """A helper class to pull traits from a dictionary
    """
    def __init__(self, traits: list):
        self.traitnames = []
        self.traits = {}

        for trait in traits:
            self.traitnames += [trait]
            self.traits[trait] = traits[trait]

        self.shuffle_threshold = len(traits) / 2
        self.trait_deck = []
        self.shuffle()

    def shuffle(self):
        """re-shuffle the traits deck"""
        self.trait_deck = self.traitnames
        shuffle(self.trait_deck)

    def draw(self):
        if len(self.trait_deck) < self.shuffle_threshold:
            self.shuffle()
        new_trait_name = self.trait_deck.pop()
        new_trait = Trait(new_trait_name, self.traits[new_trait_name], normalize=True)
        return new_trait


personality_traits = TraitsList(playertraits.PERSONALITY_TRAITS)

if __name__ == "__main__":
    first_trait = list(playertraits.PERSONALITY_TRAITS.keys())[0]

    t = Trait("First Trait", playertraits.PERSONALITY_TRAITS[first_trait], normalize=True)
    print(t)

    pt = personality_traits

    for i in range(0, 3):
        nt = pt.draw()
        print(nt)
        t += nt

    print(t)

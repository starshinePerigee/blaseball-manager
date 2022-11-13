import pytest

from blaseball.stats.modifiers import Modifier, PersonalityTraitDeck
from blaseball.stats.stats import pb
from data.playertraits import PERSONALITY_TRAITS


@pytest.fixture
def modifier_2(stat_1, stat_2):
    test_modifier = Modifier(
        "test modifier",
        {
            stat_1: 0.1,
            stat_2: 0.2,
        },
        ["tag1", "tag2"]
    )
    return test_modifier


class TestModifier:
    def test_init(self, modifier_2):
        test_modifier = Modifier("test mod")
        assert isinstance(test_modifier, Modifier)

    def test_get(self, modifier_2, stat_1):
        assert modifier_2[stat_1] == 0.1
        assert modifier_2['col1'] == 0.1
        assert modifier_2["tag1"]
        assert not modifier_2["tag4"]

    def test_iter(self, modifier_2):
        for value in modifier_2:
            assert isinstance(value, str)
        assert [x for x in modifier_2] == ["col1", "col2", "tag1", "tag2"]

    def test_contains(self, modifier_2, stat_2, stat_3):
        assert stat_2 in modifier_2
        assert stat_3 not in modifier_2
        assert "tag1" in modifier_2
        assert "col1" in modifier_2

    def test_nice_string(self, modifier_2):
        nice_str = modifier_2.nice_string()
        print("\r\n" + nice_str)
        assert "col1" in nice_str
        assert "0.1" in nice_str
        assert "tag1" in nice_str
        assert "Test Modifier" in nice_str

    def test_strings(self, modifier_2):
        print("")
        print(str(modifier_2))
        assert isinstance(str(modifier_2), str)
        assert "test modifier" in str(modifier_2)
        print(repr(modifier_2))
        assert isinstance(repr(modifier_2), str)

class TestPersonalityTraitDeck:
    def test_parse_trait(self, arbitrary_pb):
        test_deck = PersonalityTraitDeck({}, arbitrary_pb)
        # "demanding": {"determination": 1, "stability": 1, },
        parsed = test_deck.parse_trait('test trait', {"col1": 1, "col2": 1, })
        assert parsed.name == 'test trait'
        assert parsed["col1"] == pytest.approx(0.1)
        parsed_2 = test_deck.parse_trait('test trait', {"col1": 1, "col2": 1, })
        assert parsed_2 is not parsed

    def test_live_data(self):
        deck = PersonalityTraitDeck(PERSONALITY_TRAITS, pb)
        upcoming_trait = deck.trait_deck[0]
        trait_1 = deck.draw()
        assert trait_1.name == upcoming_trait
        assert trait_1.name not in deck.trait_deck
        trait_2 = deck.draw()
        assert trait_1.name != trait_2.name

    def test_shuffle(self):
        deck = PersonalityTraitDeck(PERSONALITY_TRAITS, pb)
        total_cards = len(deck)
        for i in range(0, int(total_cards/2) - 1):
            deck.draw()
        half_empty = len(deck.trait_deck)
        assert half_empty < total_cards
        for i in range(3):
            deck.draw()
        assert len(deck.trait_deck) > half_empty

    def test_forever(self):
        deck = PersonalityTraitDeck(PERSONALITY_TRAITS, pb)
        for i in range(0, 1000):
            assert isinstance(deck.draw(), Modifier)


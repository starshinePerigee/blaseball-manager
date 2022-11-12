import pytest

from blaseball.stats.modifiers import Modifier
from blaseball.stats.stats import Stat


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
        assert modifier_2["tag1"]
        assert not modifier_2["tag4"]

    def test_iter(self, modifier_2):
        for i, value in enumerate(modifier_2):
            if i < len(modifier_2.stat_effects):
                assert isinstance(value, Stat)
            else:
                assert isinstance(value, str)

    def test_contains(self, modifier_2, stat_2, stat_3):
        assert stat_2 in modifier_2
        assert stat_3 not in modifier_2
        assert "tag1" in modifier_2

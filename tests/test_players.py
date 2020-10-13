import pytest

from blaseball.stats.players import Player, PlayerBase


class TestPlayerBase:
    def test_generate(self):
        pb = PlayerBase()
        assert len(pb) == 0
        pb.new_players(10)
        assert len(pb) == 10
        pb.new_players(10)
        assert len(pb) == 20

    def test_indexing(self):
        pass

    def test_generate_random_stats(self):
        pb = PlayerBase()
        pb.new_players(10)
        # check name, stats
        assert True

class TestPlayer:
    def test_generate_name(self):
        assert isinstance(Player.generate_name(), str)
        assert Player.generate_name() != Player.generate_name()

    def test_generate_name_case(self):
        assert Player.generate_name()[0].isupper()
        assert Player.generate_name()[1].islower()


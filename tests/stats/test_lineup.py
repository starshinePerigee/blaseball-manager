import pytest

from blaseball.stats.teams import League
from blaseball.stats import players
from blaseball.stats.lineup import Lineup, Defense


class TestDefense:
    def test_init(self, team_1):
        test_d = Defense()
        assert isinstance(test_d, Defense)

    def test_all_players(self, d_fixture, d_sizes):
        all_players = d_fixture.all_players()
        assert isinstance(all_players, list)
        assert isinstance(all_players[0], players.Player)
        assert isinstance(all_players[-1], players.Player)
        assert len(all_players) == d_sizes
        assert len(d_fixture) == d_sizes

    def test_index(self, d_fixture):
        assert isinstance(d_fixture["catcher"], players.Player)
        assert d_fixture["catcher"]['name'] == "Test0 Bobson"
        assert isinstance(d_fixture["basepeeps"], list)
        assert d_fixture["fielders"][0]['name'] == "Test5 Bobson"


class TestLineup:
    @pytest.mark.xfail
    def test_generate(self, team_1):
        test_lineup = Lineup()
        test_lineup.generate(team_1)
        assert test_lineup.validate()[0]

    def test_index(self, l_fixture):
        assert l_fixture['catcher']['name'] == "Test1 Bobson"
        assert l_fixture['batters'][0]['name'] == "Test1 Bobson"
        assert l_fixture['basepeeps'][2]['name'] == 'Test5 Bobson'

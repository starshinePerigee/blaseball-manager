import pytest

from blaseball.stats.lineup import Lineup, Defense
from blaseball.stats import players


@pytest.fixture
def lineup_1(team_1):
    lineup = Lineup("Test Lineup")
    lineup.generate(team_1, in_order=True)
    return lineup


@pytest.fixture
def defense_1(lineup_1):
    return lineup_1.defense


class TestDefense:
    def test_init(self, team_1):
        test_d = Defense()
        assert isinstance(test_d, Defense)

    def test_all_players(self, defense_1):
        all_players = defense_1.all_players()
        assert isinstance(all_players, list)
        assert isinstance(all_players[0], players.Player)
        assert isinstance(all_players[-1], players.Player)
        assert len(all_players) == 9
        
    # def test_index(self, d_fixture):
    #     assert isinstance(d_fixture["catcher"], players.Player)
    #     assert d_fixture["catcher"]['name'] == "Test0 Bobson"
    #     assert isinstance(d_fixture["basepeeps"], list)
    #     assert d_fixture["fielders"][0]['name'] == "Test5 Bobson"


class TestLineup:
    @pytest.mark.xfail
    def test_generate(self, team_1):
        test_lineup = Lineup()
        test_lineup.generate(team_1)
        assert test_lineup.validate()[0]

    def test_index(self, lineup_1):
        assert lineup_1['pitcher']['name'] == 'Test0 Bobson'
        assert lineup_1['catcher']['name'] == "Test1 Bobson"
        assert lineup_1['batters'][0]['name'] == "Test1 Bobson"
        assert lineup_1['fielder 2']['name'] == "Test7 Bobson"

    def test_string(self, lineup_1):
        assert isinstance(lineup_1.string_summary(), str)
        assert isinstance(lineup_1.__str__(), str)


import pytest

from blaseball.stats import lineup
from blaseball.stats import players


class TestPosition:
    def test_position(self, player_1):
        catcher = lineup.Position('catcher', player_1)
        assert catcher.location.x == 0

        rf = lineup.Position('fielder 3', player_1)
        assert rf.location.theta() > 45
        assert rf.group == 'fielder'

        assert isinstance(str(rf), str)


class TestDefense:
    def test_init(self):
        test_d = lineup.Defense()
        assert isinstance(test_d, lineup.Defense)
        assert len(test_d) == 0

    def test_add(self, team_1):
        test_d = lineup.Defense()
        assert len(test_d) == 0
        test_d.add('catcher', team_1.players[0])
        assert len(test_d) == 1
        assert test_d['catcher'].player == team_1.players[0]

    def test_all_players(self, defense_1):
        all_players = defense_1.all_players()
        assert isinstance(all_players, list)
        assert isinstance(all_players[0], players.Player)
        assert isinstance(all_players[-1], players.Player)
        assert len(all_players) == 9

    def test_index(self, defense_1):
        # assert isinstance(defense_1["catcher"], players.Player)
        assert defense_1["catcher"].player['name'] == "Test1 Bobson"
        assert isinstance(defense_1["basepeep"], list)
        assert defense_1["fielder"][0].player['name'] == "Test6 Bobson"

    def test_find(self, defense_1):
        assert defense_1.find('Test1 Bobson').position == 'catcher'


class TestLineup:
    def test_generate(self, team_1):
        test_lineup = lineup.Lineup('test lineup')
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

    def test_team(self, lineup_1):
        assert lineup_1['team'] == lineup_1['batter 1']['team']
        assert isinstance(lineup_1['team'], str)

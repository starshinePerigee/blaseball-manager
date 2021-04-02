import pytest

from blaseball.stats.teams import Team, League
from blaseball.stats import players
from data import teamdata


@pytest.fixture()
def league_20():
    pb = players.PlayerBase()
    l = League(pb, teamdata.TEAMS_99)
    return l


@pytest.fixture
def team_1(league_20):
    return league_20.teams[0]


class TestTeam:
    def test_init(self):
        pb = players.PlayerBase()
        pb.new_players(10)
        team = Team("test team 1", list(pb.players.values()))
        assert len(team) == 10

    indexes = [0, 2, 9]

    @pytest.mark.parametrize("player_index", indexes)
    def test_get_player_index(self, team_1, player_index):
        test_player = team_1.players[player_index]
        assert team_1.get_player_index(test_player) == player_index
        assert team_1.get_player_index(test_player["name"]) == player_index

    def test_get_player_index_miss(self, team_1):
        with pytest.raises(KeyError):
            assert team_1.get_player_index("Not A Player") == 0

    def test_team_strings(self, team_1):
        assert isinstance(repr(team_1), str)
        assert isinstance(str(team_1), str)


class TestLeague:
    def test_init(self):
        pb = players.PlayerBase()
        league = League(pb, ["test team 1", "test team 2"])
        assert len(league) == 2
        assert pb.verify_players()

    def test_league_strings(self, league_20):
        assert isinstance(repr(league_20), str)
        assert isinstance(str(league_20), str)
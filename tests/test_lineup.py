import pytest

from blaseball.stats.teams import League
from blaseball.stats import players
from blaseball.stats.lineup import Lineup, Defense
from data import teamdata


@pytest.fixture
def league_2():
    pb = players.PlayerBase()
    l = League(pb, teamdata.TEAMS_99[0:2])
    return l


@pytest.fixture
def team_1(league_2):
    return league_2[0]


class TestDefense:
    def test_init(self, team_1):
        test_d = Defense()
        assert isinstance(test_d, Defense)

    @pytest.fixture(params=[6, 10])
    def d_sizes(self, request):
        return request.param

    @pytest.fixture
    def d_fixture(self, d_sizes, team_1):
        i = 0
        d = Defense()
        while i < d_sizes:
            if i <= 0:
                d.catcher = team_1[i]
            elif i <= 1:
                d.shortstop = team_1[i]
            elif i <= 4:
                d.basepeeps += [team_1[i]]
            elif i <= 7:
                d.fielders += [team_1[i]]
            else:
                d.extras += [team_1[i]]
            i += 1
        return d

    def test_all_players(self, d_fixture, d_sizes):
        all_players = d_fixture.all_players()
        assert isinstance(all_players, list)
        assert isinstance(all_players[0], players.Player)
        assert isinstance(all_players[-1], players.Player)
        assert len(all_players) == d_sizes
        assert len(d_fixture) == d_sizes


class TestLineup:
    def test_generate(self, team_1):
        test_lineup = Lineup()
        test_lineup.generate(team_1)
        assert test_lineup.validate[0]

    def test_index(self, lineup):
        # TODO TODO
        pass

import pytest

import pandas as pd

from blaseball.stats.players import Player, PlayerBase


@pytest.fixture
def playerbase_10():
    pb = PlayerBase()
    pb.new_players(10)
    return pb


class TestPlayer:
    def test_generate_name(self):
        assert isinstance(Player.generate_name(), str)
        assert Player.generate_name() != Player.generate_name()

    def test_generate_name_case(self):
        assert Player.generate_name()[0].isupper()
        assert Player.generate_name()[1].islower()

    def test_index_get(self, player_1):
        assert isinstance(player_1["name"], str)
        assert isinstance(player_1["power"], float)

    def test_index_set(self, player_1):
        player_1["name"] = "Test Player"
        assert player_1["name"] == "Test Player"
        player_1["power"] = 0.5
        assert player_1["power"] == 0.5

    stat_dict = {"name": "Test Player2", "contact": 0.75}

    def test_assign_dict(self, player_1):
        player_1.assign(TestPlayer.stat_dict)
        assert player_1["name"] == "Test Player2"
        assert player_1["contact"] == 0.75

    def test_assign_series(self, player_1):
        stat_series = pd.Series(TestPlayer.stat_dict)
        player_1.assign(stat_series)
        assert player_1["name"] == "Test Player2"
        assert player_1["contact"] == 0.75

    def test_eq(self, playerbase_10):
        p1 = playerbase_10.iloc(0)
        p2 = playerbase_10.iloc(1)

        assert p1 != p2

        stat_row = playerbase_10.df.loc[p1.cid]
        p2.assign(stat_row)

        assert p1 == p2

        for key in p1.stat_row().keys():
            assert p1[key] == p2[key]

    def test_iterable(self, player_1):
        for stat, index in zip(player_1, player_1.stat_row().index):
            assert player_1[index] == stat

    def test_strings(self, player_1):
        assert isinstance(player_1.__str__(), str)
        assert isinstance(player_1.__repr__(), str)
        assert isinstance(player_1.total_stars(), str)

    def test_add_average(self, player_1):
        assert player_1['pitches seen'] == 0
        assert player_1['strike rate'] == 0
        assert player_1['hit rate'] == 0
        player_1.add_average(
            ['strike rate', 'ball rate', 'foul rate', 'hit rate', 'pitch read chance'],
            [1, 0, 0, 0, 0]
        )

        assert player_1['pitches seen'] == 1
        assert player_1['strike rate'] == 1
        assert player_1['hit rate'] == 0

        player_1.add_average(
            ['strike rate', 'ball rate', 'foul rate', 'hit rate', 'pitch read chance'],
            [0, 1, 0, 0, 0]
        )

        assert player_1['pitches seen'] == 2
        assert player_1['strike rate'] == 1 / 2
        assert player_1['hit rate'] == 0

    def test_stat_breakdown(self, player_1):
        assert isinstance(player_1.text_breakdown(), str)


class TestPlayerBase:
    def test_generate(self):
        pb = PlayerBase()
        assert len(pb) == 0
        pb.new_players(10)
        assert len(pb) == 10
        pb.new_players(10)
        assert len(pb) == 20
        nb = PlayerBase(15)
        assert len(nb) == 15

    def test_init_verify(self):
        pb = PlayerBase()
        assert pb.verify_players()
        pb.new_players(10)
        assert pb.verify_players()

    def test_verify_players(self, playerbase_10):
        assert playerbase_10.verify_players()
        del_player = playerbase_10.iloc(0)
        del playerbase_10.players[del_player.cid]
        with pytest.raises(RuntimeError):
            playerbase_10.verify_players()
        playerbase_10.df.drop(axis=1, index=del_player.cid, inplace=True)
        assert playerbase_10.verify_players()

    def test_new_players(self):
        pb = PlayerBase()
        new_players = pb.new_players(10)
        assert isinstance(new_players, list)
        assert isinstance(new_players[0], Player)
        for player in new_players:
            assert player == pb[player.df_index()]

    def test_verify_assign(self, playerbase_10):
        cid_0 = playerbase_10.iloc(0).cid
        playerbase_10[cid_0]["name"] = "Test Bobson"
        assert playerbase_10[cid_0]["name"] == "Test Bobson"
        assert playerbase_10.df.loc[cid_0]["name"] == "Test Bobson"

        cid_1 = playerbase_10.iloc(1).cid
        playerbase_10[cid_0] = playerbase_10[cid_1]
        assert playerbase_10[cid_0]["name"] == playerbase_10[cid_1]["name"]
        assert playerbase_10.verify_players()

    def test_verify_functs(self, playerbase_10):
        playerbase_10.iloc(1).initialize(playerbase_10)
        assert playerbase_10.verify_players()
        playerbase_10.iloc(2).randomize()
        assert playerbase_10.verify_players()
        playerbase_10.df.iloc[3] = playerbase_10.df.iloc[4]
        assert playerbase_10.verify_players()
        assert playerbase_10.iloc(3)['name'] == playerbase_10.iloc(4)['name']
        # playerbase_10.df.drop(5, inplace=True)
        # with pytest.raises(RuntimeError):
        #     playerbase_10.verify_players()

    def test_index_get(self, playerbase_10):
        first_player = playerbase_10.iloc(0)
        assert isinstance(playerbase_10[first_player.cid], Player)
        assert playerbase_10[first_player['name']] == first_player
        assert isinstance(playerbase_10[first_player.cid]['speed'], float)

    def test_index_set(self, playerbase_10, player_1):
        player_cids = playerbase_10.df.index
        assert playerbase_10[player_cids[0]] != playerbase_10[player_cids[1]]
        playerbase_10[player_cids[0]] = playerbase_10[player_cids[1]]
        assert playerbase_10[player_cids[0]]['name'] == playerbase_10[player_cids[1]]['name']
        playerbase_10[player_cids[2]]['name'] = 'TEST PLAYER'
        assert playerbase_10[player_cids[2]]['name'] == 'TEST PLAYER'
        assert playerbase_10[player_cids[3]] != player_1
        playerbase_10[player_cids[3]] = player_1
        assert playerbase_10[player_cids[3]]['name'] == player_1['name']

    def test_generate_random_stats(self, playerbase_10):
        cid_a = playerbase_10.iloc(0).cid
        cid_b = playerbase_10.iloc(1).cid
        assert playerbase_10[cid_a]['speed'] != playerbase_10[cid_b]['speed']
        assert playerbase_10[cid_a]['name'] != playerbase_10[cid_b]['name']

    def test_iterable(self, playerbase_10):
        count = 0
        for player in playerbase_10:
            count += 1
            assert isinstance(player, Player)
        assert count == len(playerbase_10)
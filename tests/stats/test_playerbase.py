import pytest

from blaseball.stats import statclasses, players
from blaseball.stats.playerbase import PlayerBase
from blaseball.stats import stats as s


class TestPlayerBasePlayers:
    def test_generate_clear(self):
        pb = PlayerBase(statclasses.RECALCULATION_ORDER_TEST, statclasses.BASE_DEPENDENCIES_TEST)
        name = statclasses.Stat("name", statclasses.Kinds.test, playerbase=pb)
        assert len(pb) == 0
        for __ in range(10):
            new_player = players.Player(pb)
            pb.new_player(new_player)
        assert len(pb) == 10
        pb.clear_players()
        assert len(pb) == 0

    def test_verify_players(self, playerbase_10):
        playerbase_10.verify()
        del_player = playerbase_10.iloc(0)
        del playerbase_10.players[del_player.cid]
        with pytest.raises(RuntimeError):
            playerbase_10.verify()
        playerbase_10.df.drop(axis=1, index=del_player.cid, inplace=True)
        playerbase_10.verify()

    def test_index_get(self, playerbase_10):
        first_player = playerbase_10.iloc(0)
        assert isinstance(playerbase_10[first_player.cid], players.Player)
        assert playerbase_10[first_player.cid]['name'] == first_player['name']
        assert playerbase_10[first_player['name']] == first_player
        assert isinstance(playerbase_10[first_player.cid]['speed'], float)

    def test_del(self, playerbase_10):
        del_player = playerbase_10.iloc(3)
        del playerbase_10[del_player]
        assert len(playerbase_10) == 9
        assert del_player not in playerbase_10.players
        del_player_2 = playerbase_10.iloc(3)
        assert del_player != del_player_2
        del playerbase_10[del_player_2.cid]
        assert len(playerbase_10) == 8

#
#     def test_index_set(self, playerbase_10, player_1):
#         player_cids = playerbase_10.df.index
#         assert playerbase_10[player_cids[0]] != playerbase_10[player_cids[1]]
#         playerbase_10[player_cids[0]] = playerbase_10[player_cids[1]]
#         assert playerbase_10[player_cids[0]]['name'] == playerbase_10[player_cids[1]]['name']
#         playerbase_10[player_cids[2]]['name'] = 'TEST PLAYER'
#         assert playerbase_10[player_cids[2]]['name'] == 'TEST PLAYER'
#         assert playerbase_10[player_cids[3]] != player_1
#         playerbase_10[player_cids[3]] = player_1
#         assert playerbase_10[player_cids[3]]['name'] == player_1['name']
#
#     def test_generate_random_stats(self, playerbase_10):
#         cid_a = playerbase_10.iloc(0).cid
#         cid_b = playerbase_10.iloc(1).cid
#         assert playerbase_10[cid_a]['speed'] != playerbase_10[cid_b]['speed']
#         assert playerbase_10[cid_a]['name'] != playerbase_10[cid_b]['name']
#
#     def test_iterable(self, playerbase_10):
#         count = 0
#         for player in playerbase_10:
#             count += 1
#             assert isinstance(player, Player)
#         assert count == len(playerbase_10)


class TestPlayerBaseStats:
    def test_init(self, arbitrary_pb):
        stat_1 = arbitrary_pb.stats['col1']
        assert isinstance(stat_1, statclasses.Stat)
        assert 'col1' in arbitrary_pb.df.columns

    def test_add_stat(self, arbitrary_pb):
        temp_pb = PlayerBase(statclasses.RECALCULATION_ORDER_TEST, statclasses.BASE_DEPENDENCIES_TEST)
        test_stat = statclasses.Stat("test stat", statclasses.Kinds.test_dependent, default=5, playerbase=temp_pb)
        assert test_stat not in arbitrary_pb.stats
        arbitrary_pb.add_stat(test_stat)
        assert test_stat in arbitrary_pb.stats.values()
        assert arbitrary_pb.df.at[10, 'test stat'] == 5

    def test_remove_stat(self, arbitrary_pb):
        test_stat_2 = statclasses.Stat("test stat 2", statclasses.Kinds.test, playerbase=arbitrary_pb)
        assert test_stat_2 in arbitrary_pb.stats.values()
        arbitrary_pb.remove_stat(test_stat_2)
        assert test_stat_2 not in arbitrary_pb.stats.values()
        assert test_stat_2.name not in arbitrary_pb.df.columns

    def test_get_stats_with(self, arbitrary_pb):
        arbitrary_len = len(arbitrary_pb.df.columns)
        assert len(arbitrary_pb.get_stats_with_kind(statclasses.Kinds.test)) == arbitrary_len
        assert len(arbitrary_pb.get_stats_by_name("col")) == arbitrary_len - 2
        assert len(arbitrary_pb.get_stats_by_name("cola")) == 1
        assert arbitrary_pb.get_stats_by_name("cola")[0] is arbitrary_pb.stats["cola"]

    def test_default_stat_list(self, arbitrary_pb):
        for i in range(len(arbitrary_pb.stats)):
            assert arbitrary_pb._default_stat_list[i] == -1

    def test_recalculate_all(self, arbitrary_pb):
        # make a simple dependent stat
        statclasses.Calculatable(
            "dependent stat",
            statclasses.Kinds.test_dependent,
            lambda pb, cid: pb.df.at[cid, 'col3'],
            arbitrary_pb
        )
        assert list(arbitrary_pb.df["dependent stat"]) == [-1.0] * 5
        assert arbitrary_pb.iloc(1)._stale_dict[statclasses.Kinds.test_dependent]
        arbitrary_pb.recalculate_all()
        assert list(arbitrary_pb.df["dependent stat"]) == list(arbitrary_pb.df['col3'])
        assert not arbitrary_pb.iloc(1)._stale_dict[statclasses.Kinds.test_dependent]


class TestPlayerBase:
    def test_verify(self, arbitrary_pb):
        arbitrary_pb.verify()

    def test_global_pb_verify(self):
        s.pb.verify()

    def test_strings(self):
        assert isinstance(str(s.pb), str)
        assert isinstance(repr(s.pb), str)

    @pytest.mark.parametrize("state", [True, False])
    def test_create_blank_stale_dict(self, state):
        test_dict = s.pb.create_blank_stale_dict(state)
        assert len(test_dict) > 5
        assert not test_dict[statclasses.Kinds.personality]
        assert test_dict[statclasses.Kinds.weight] == state

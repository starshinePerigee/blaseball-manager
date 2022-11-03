import pytest


# class TestPlayerBase:
#     def test_generate(self):
#         pb = PlayerBase()
#         assert len(pb) == 0
#         pb.new_players(10)
#         assert len(pb) == 10
#         pb.new_players(10)
#         assert len(pb) == 20
#         nb = PlayerBase(15)
#         assert len(nb) == 15
#
#     def test_init_verify(self):
#         pb = PlayerBase()
#         assert pb.verify_players()
#         pb.new_players(10)
#         assert pb.verify_players()
#
#     def test_verify_players(self, playerbase_10):
#         assert playerbase_10.verify_players()
#         del_player = playerbase_10.iloc(0)
#         del playerbase_10.players[del_player.cid]
#         with pytest.raises(RuntimeError):
#             playerbase_10.verify_players()
#         playerbase_10.df.drop(axis=1, index=del_player.cid, inplace=True)
#         assert playerbase_10.verify_players()
#
#     def test_new_players(self):
#         pb = PlayerBase()
#         new_players = pb.new_players(10)
#         assert isinstance(new_players, list)
#         assert isinstance(new_players[0], Player)
#         for player in new_players:
#             assert player == pb[player.df_index()]
#
#     def test_verify_assign(self, playerbase_10):
#         cid_0 = playerbase_10.iloc(0).cid
#         playerbase_10[cid_0]["name"] = "Test Bobson"
#         assert playerbase_10[cid_0]["name"] == "Test Bobson"
#         assert playerbase_10.df.loc[cid_0]["name"] == "Test Bobson"
#
#         cid_1 = playerbase_10.iloc(1).cid
#         playerbase_10[cid_0] = playerbase_10[cid_1]
#         assert playerbase_10[cid_0]["name"] == playerbase_10[cid_1]["name"]
#         assert playerbase_10.verify_players()
#
#     def test_verify_functs(self, playerbase_10):
#         playerbase_10.iloc(1).initialize(playerbase_10)
#         assert playerbase_10.verify_players()
#         playerbase_10.iloc(2).randomize()
#         assert playerbase_10.verify_players()
#         playerbase_10.df.iloc[3] = playerbase_10.df.iloc[4]
#         assert playerbase_10.verify_players()
#         assert playerbase_10.iloc(3)['name'] == playerbase_10.iloc(4)['name']
#         # playerbase_10.df.drop(5, inplace=True)
#         # with pytest.raises(RuntimeError):
#         #     playerbase_10.verify_players()
#
#     def test_index_get(self, playerbase_10):
#         first_player = playerbase_10.iloc(0)
#         assert isinstance(playerbase_10[first_player.cid], Player)
#         assert playerbase_10[first_player.cid]['name'] == first_player['name']
#         assert playerbase_10[first_player['name']] == first_player
#         assert isinstance(playerbase_10[first_player.cid]['speed'], float)
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

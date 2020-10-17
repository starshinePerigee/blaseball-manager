import pytest

from blaseball.stats.players import Player, PlayerBase


@pytest.fixture
def playerbase_10():
    pb = PlayerBase()
    pb.new_players(10)
    return pb


@pytest.fixture()
def player_1():
    pb = PlayerBase()
    pb.new_players(1)
    return pb[0]


class TestPlayer:
    def test_generate_name(self):
        assert isinstance(Player.generate_name(), str)
        assert Player.generate_name() != Player.generate_name()

    def test_generate_name_case(self):
        assert Player.generate_name()[0].isupper()
        assert Player.generate_name()[1].islower()

    def test_index_get(self, player_1):
        assert isinstance(player_1["name"], str)
        assert isinstance(player_1["hitting"], float)

    def test_index_set(self, player_1):
        player_1["name"] = "Test Player"
        assert player_1["name"] == "Test Player"
        player_1["hitting"] = 0.5
        assert player_1["hitting"] == 0.5

    def test_eq_1(self, playerbase_10):
        player1 = Player(playerbase_10.df.iloc[0])
        assert player1 == player1
        assert player1 == playerbase_10.df.iloc[0]
        playerbase_10.df.iloc[0]['name'] = 'Test Bobson'
        player1_copy = Player(playerbase_10.df.iloc[0])
        assert player1_copy != player1
        player1_deep = player1
        player1_deep['hitting'] = 0.5
        assert player1 == player1_deep
        for key in player1.stat_row.keys():
            assert player1[key] == player1_deep[key]
        assert playerbase_10[0] != playerbase_10[1]

    def test_iterable(self, player_1):
        for stat, index in zip(player_1, player_1.stat_row.index):
            assert player_1[index] == stat


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

    def test_verify_init(self):
        pb = PlayerBase()
        assert pb.verify_players()
        pb.new_players(10)
        assert pb.verify_players()

    def test_new_players(self):
        pb = PlayerBase()
        new_players = pb.new_players(10)
        assert isinstance(new_players, list)
        assert isinstance(new_players[0], Player)
        for player in new_players:
            assert player == pb[player.df_index()]

    def test_verify_assign(self, playerbase_10):
        playerbase_10[0] = playerbase_10[1]
        assert playerbase_10.verify_players()
        playerbase_10[2] = playerbase_10.df.loc[3]
        assert playerbase_10.verify_players()
        playerbase_10.players[4] = playerbase_10.players[5]
        with pytest.raises(RuntimeError):
            playerbase_10.verify_players()

    def test_verify_functs(self, playerbase_10):
        playerbase_10[1].initialize()
        assert playerbase_10.verify_players()
        playerbase_10[2].randomize()
        assert playerbase_10.verify_players()
        playerbase_10.df.iloc[3] = playerbase_10.df.iloc[4]
        assert playerbase_10.verify_players()
        assert playerbase_10[3]['name'] == playerbase_10[4]['name']
        # playerbase_10.df.drop(5, inplace=True)
        # with pytest.raises(RuntimeError):
        #     playerbase_10.verify_players()

    def test_index_get(self, playerbase_10):
        assert isinstance(playerbase_10[0], Player)
        first_player = playerbase_10[0]
        assert playerbase_10[first_player['name']] == first_player
        assert isinstance(playerbase_10[0]['hitting'], float)

    indexers = [
        [1, 3, 5],
        range(1, 5),
    ]
    @pytest.mark.parametrize("indexer", indexers)
    def test_index_lists(self, playerbase_10, indexer):
        subset = playerbase_10[indexer]
        assert isinstance(subset, list)
        assert isinstance(subset[0], Player)
        for i, j in zip(subset, indexer):
            assert i.df_index() == j

    def test_index_slice(self, playerbase_10):
        subset = playerbase_10[:]
        assert isinstance(subset, list)
        assert isinstance(subset[0], Player)
        for i, j in zip(subset, range(0, 10)):
            assert i.df_index() == j
        subset = playerbase_10[1:7:2]
        assert isinstance(subset, list)
        assert isinstance(subset[0], Player)
        for i, j in zip(subset, [1, 3, 5, 7]):
            assert i.df_index() == j

    def test_index_set(self, playerbase_10, player_1):
        assert playerbase_10[0] != playerbase_10[1]
        playerbase_10[0] = playerbase_10[1]
        assert playerbase_10[0]['name'] == playerbase_10[1]['name']
        playerbase_10[2]['name'] = 'TEST PLAYER'
        assert playerbase_10[2]['name'] == 'TEST PLAYER'
        assert playerbase_10[3] != player_1
        playerbase_10[3] = player_1
        assert playerbase_10[3]['name'] == player_1['name']

    def test_generate_random_stats(self, playerbase_10):
        assert playerbase_10[1]['hitting'] != playerbase_10[2]['hitting']
        assert playerbase_10[1]['name'] != playerbase_10[2]['name']

    def test_iterable(self, playerbase_10):
        count = 0
        for player in playerbase_10:
            count += 1
            assert isinstance(player, Player)
        assert count == len(playerbase_10)

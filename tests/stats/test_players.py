import pytest

from blaseball.stats import players, playerbase, modifiers, statclasses
from blaseball.stats import stats as s
from blaseball.stats.stats import pb


@pytest.fixture
def player_dependent(player_1):
    independent = statclasses.Stat("independent", statclasses.Kinds.test, -2.0)
    dependent = statclasses.Calculatable(
        "dependent",
        statclasses.Kinds.test_dependent,
        None,
        lambda independent: independent * 2,  # noqa - of course this shadows, that's intentional
    )
    player_1[independent] = 0.5
    player_1.recalculate()
    return player_1


class TestPlayerIndexing:
    def test_init(self):
        player = players.Player(pb)
        assert player.cid in pb.df.index
        assert pb.df.at[player.cid, "name"] == 'WYATT MASON'
        assert len(player.modifiers) > 2

        player.initialize()
        assert isinstance(pb.df.at[player.cid, "name"], str)
        assert pb.df.at[player.cid, "name"] != 'WYATT MASON'

    def test_index_fresh(self, player_1):
        p1_insight = pb.df.at[player_1.cid, "insight"]
        assert not player_1._stale_dict[s.insight.kind]
        assert player_1[s.insight] == p1_insight

    def test_index_cid(self, player_1):
        assert player_1['cid'] == player_1.cid

    def test_index_string(self, player_1):
        assert player_1['insight'] == player_1[s.insight]

    def test_set(self, player_1):
        player_1[s.insight] = 1.33
        assert player_1[s.insight] == 1.33
        for kind in statclasses.dependents[s.insight.kind]:
            assert player_1._stale_dict[kind]
            player_1._stale_dict[kind] = False  # reset this
        assert not any(player_1._stale_dict.values())  # make sure no others got set

    def test_index_calculatable(self, player_dependent):
        assert player_dependent['independent'] == pytest.approx(0.5)
        assert player_dependent['dependent'] == pytest.approx(1.0)

    def test_index_stale(self, player_dependent):
        assert player_dependent['dependent'] == pytest.approx(1.0)
        player_dependent['independent'] = 1.0
        assert player_dependent._stale_dict[statclasses.Kinds.test_dependent]
        assert player_dependent['dependent'] == pytest.approx(2.0)
        assert player_dependent.pb.df.at[player_dependent.cid, 'dependent'] == pytest.approx(1.0)

    def test_recalculate(self, player_dependent):
        player_dependent['independent'] = 1.0
        player_dependent.recalculate()
        assert player_dependent['independent'] == 1.0
        assert player_dependent['dependent'] == pytest.approx(2.0)

        player_dependent['independent'] = 0.33
        assert player_dependent['dependent'] == pytest.approx(0.66)  # cache miss
        assert player_dependent.pb.df.at[player_dependent.cid, 'dependent'] == pytest.approx(2.0)
        player_dependent.recalculate()
        assert player_dependent['dependent'] == pytest.approx(0.66)  # cache hit
        assert player_dependent.pb.df.at[player_dependent.cid, 'dependent'] == pytest.approx(0.66)

    def test_player_modifiers(self, player_1):
        pass


class TestPlayerOther:
    def test_strings(self, player_1):
        assert isinstance(str(player_1), str)
        assert player_1[s.name].lower() in str(player_1).lower()
        assert isinstance(repr(player_1), str)

    def test_add_modifiers(self, player_1):
        player_1[s.insight] = 0.5
        test_mod = modifiers.Modifier("test mod", {s.insight: 0.5})
        player_1.add_modifier(test_mod)
        assert player_1[s.insight] == pytest.approx(1.0)
        assert test_mod in player_1.modifiers

    def test_remove_modifiers(self, player_1):
        player_1[s.insight] = 0.5
        test_mod = modifiers.Modifier("test mod", {s.insight: 0.5})
        player_1.add_modifier(test_mod)
        assert player_1[s.insight] == pytest.approx(1.0)
        player_1.remove_modifier(test_mod)
        assert player_1[s.insight] == pytest.approx(0.5)
        assert len(player_1.modifiers) == 0

    def test_eq_assign(self, player_1):
        player_2 = players.Player(s.pb)
        player_2.initialize()
        player_2.modifiers = []
        player_2.recalculate()

        assert player_1 != player_2
        player_2.assign(player_1)
        assert player_1 == player_2

    #
    # def test_eq(self, playerbase_10):
    #     p1 = playerbase_10.iloc(0)
    #     p2 = playerbase_10.iloc(1)
    #
    #     assert p1 != p2
    #
    #     stat_row = playerbase_10.df.loc[p1.cid]
    #     p2.assign(stat_row)
    #
    #     assert p1 == p2
    #
    #     for key in p1.stat_row().keys():
    #         assert p1[key] == p2[key]
    #
    # def test_iterable(self, player_1):
    #     for stat, index in zip(player_1, player_1.stat_row().index):
    #         assert player_1[index] == stat
    #
    # def test_strings(self, player_1):
    #     assert isinstance(player_1.__str__(), str)
    #     assert isinstance(player_1.__repr__(), str)
    #     assert isinstance(player_1.total_stars(), str)
    #
    # def test_initialize(self, player_1):
    #     player_1.initialize(player_1.pb)
    #     assert player_1['name'] == 'WYATT MASON'
    #     assert player_1['leadership'] == 0
    #     assert player_1['pitches seen'] == 0
    #
    # def test_generate_player_number(self, player_1, monkeypatch):
    #     # this runction is not really essential but it's a good place to practice monkeypatch
    #     # force non-unusual
    #     monkeypatch.setattr('random.random', lambda: 0.9)
    #
    #     def min_randrange(start, stop, step=1):
    #         return start
    #
    #     monkeypatch.setattr('random.randrange', min_randrange)
    #     # range is 0 to 45
    #     player_1.cid = 1001  # THIS BREAKS EVERYTHING (except player numbers)
    #     assert player_1.generate_player_number() == 1
    #     player_1.cid = 1051
    #     assert 0 < player_1.generate_player_number() < 45
    #
    #     # force unusual
    #     monkeypatch.setattr('random.random', lambda: 0.01)
    #     player_1.cid = 1001
    #     assert player_1.generate_player_number() < 0
    #
    # def test_set_all_stats(self, player_1):
    #     player_1.set_all_stats(0.3)
    #     for stat in statclasses.all_stats['personality'] + statclasses.all_stats['rating']:
    #         assert player_1[stat] == 0.3
    #
    #     assert player_1['pitches seen'] == 0
    #
    # def test_reset_tracking(self, player_1):
    #     player_1['thrown strike rate'] = 0.5
    #     player_1['total pitches thrown'] = 20
    #     player_1.reset_tracking()
    #     assert player_1['thrown strike rate'] == 0
    #     assert player_1['total pitches thrown'] == 0
    #
    # def test_add_remove_trait(self, player_1):
    #     player_1.set_all_stats(0.5)
    #     assert player_1['determination'] == 0.5
    #     determination_trait = modifiers.Trait(ratings={'determination': 0.5})
    #     player_1.add_trait(determination_trait)
    #     assert player_1['determination'] == pytest.approx(1.0)
    #
    #     player_1.remove_trait(determination_trait)
    #     assert player_1['determination'] == pytest.approx(0.5)
    #
    # def test_generate_stats(self, player_1, monkeypatch):
    #     player_1.set_all_stats(0)
    #     determination_trait = modifiers.Trait(ratings={'determination': 0.25})
    #     monkeypatch.setattr('random.randrange', lambda start, stop, step=1: 2)
    #     monkeypatch.setattr(modifiers.TraitsList, 'draw', lambda tl: determination_trait)
    #
    #     monkeypatch.setattr('random.random', lambda: 0.5)
    #     player_1.randomize()
    #     assert player_1['enthusiasm'] == pytest.approx(0.5)
    #     assert player_1['determination'] == pytest.approx(1.0)
    #     assert player_1['speed'] == pytest.approx(0.25)
    #     assert player_1['power'] == pytest.approx(0.5)
    #
    #     monkeypatch.setattr('random.random', lambda: 1.0)
    #     player_1.randomize()
    #     assert player_1['enthusiasm'] == pytest.approx(1.0)
    #     assert player_1['determination'] == pytest.approx(1.5)
    #     assert player_1['speed'] == pytest.approx(1.0)
    #     assert player_1['power'] == pytest.approx(1.5)
    #
    # def test_add_average(self, player_1):
    #     assert player_1['pitches seen'] == 0
    #     assert player_1['strike rate'] == 0
    #     assert player_1['hit rate'] == 0
    #     player_1.add_average(
    #         ['strike rate', 'ball rate', 'foul rate', 'hit rate', 'pitch read chance'],
    #         [1, 0, 0, 0, 0]
    #     )
    #
    #     assert player_1['pitches seen'] == 1
    #     assert player_1['strike rate'] == 1
    #     assert player_1['hit rate'] == 0
    #
    #     player_1.add_average(
    #         ['strike rate', 'ball rate', 'foul rate', 'hit rate', 'pitch read chance'],
    #         [0, 1, 0, 0, 0]
    #     )
    #
    #     assert player_1['pitches seen'] == 2
    #     assert player_1['strike rate'] == 1 / 2
    #     assert player_1['hit rate'] == 0
    #
    # def test_stat_breakdown(self, player_1):
    #     assert isinstance(player_1.text_breakdown(), str)
#
#
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

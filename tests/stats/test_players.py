import pytest

from blaseball.stats import players, playerbase, modifiers, statclasses
from blaseball.stats import stats as s


@pytest.fixture
def player_dependent(player_1):
    independent = statclasses.Stat("independent", statclasses.Kinds.rating, -2.0)
    dependent = statclasses.Calculatable(
        "dependent",
        statclasses.Kinds.weight,
        None,
        lambda independent: independent * 2,  # noqa - of course this shadows, that's intentional
    )
    player_1[independent] = 0.5
    player_1.recalculate()
    yield player_1
    s.pb.remove_stat(independent)
    s.pb.remove_stat(dependent)


class TestPlayerIndexing:
    def test_init(self, empty_all_base):
        player = players.Player(s.pb)
        assert player.cid in s.pb.df.index
        assert s.pb.df.at[player.cid, "name"] == 'Wyatt Mason'
        assert len(player.modifiers) > 2

        player.initialize()
        assert isinstance(s.pb.df.at[player.cid, "name"], str)
        assert s.pb.df.at[player.cid, "name"] != 'Wyatt Mason'
        assert s.pb.df.at[player.cid, "element"] != "basic"

    def test_index_fresh(self, player_1):
        p1_insight = s.pb.df.at[player_1.cid, "insight"]
        assert not player_1._stale_dict[s.insight.kind]
        assert player_1[s.insight] == p1_insight

    def test_index_cid(self, player_1):
        assert player_1['cid'] == player_1.cid

    def test_index_string(self, player_1):
        assert player_1['insight'] == player_1[s.insight]

    def test_set(self, player_1):
        player_1[s.insight] = 1.33
        assert player_1[s.insight] == 1.33
        for kind in s.pb.dependents[s.insight.kind]:
            assert player_1._stale_dict[kind]
            player_1._stale_dict[kind] = False  # reset this
        assert not any(player_1._stale_dict.values())  # make sure no others got set

    def test_index_calculatable(self, player_dependent):
        assert player_dependent['independent'] == pytest.approx(0.5)
        assert player_dependent['dependent'] == pytest.approx(1.0)

    def test_index_stale(self, player_dependent):
        assert player_dependent['dependent'] == pytest.approx(1.0)
        player_dependent['independent'] = 1.0
        assert player_dependent._stale_dict[statclasses.Kinds.weight]
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
        assert player_1 != player_2
        assert list(player_1.stat_row()) == list(player_2.stat_row())

    def test_set_all_stats(self, player_1):
        player_1.set_all_stats(0.66)
        assert player_1[s.determination] == 0.66
        assert player_1[s.speed] == 0.66
        assert len(player_1.modifiers) == 0
        assert player_1[s.defense] == 0.66

    def test_get_total_stars(self, player_1):
        player_1.set_all_stats(0.0)
        for modifier in player_1.modifiers:
            player_1.remove_modifier(modifier)
        player_1.recalculate()
        # TODO: this fails with "-" when run with the entire test
        assert player_1.total_stars() == "0"
        player_1.set_all_stats(1.0)
        assert player_1.total_stars() == "*****"

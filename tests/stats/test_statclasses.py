import pytest
import pandas as pd

from blaseball.stats import statclasses, playerbase


@pytest.fixture
def playerbase_2():
    pb = playerbase.PlayerBase()
    statclasses.Stat("test 1", statclasses.Kinds.test, 1, pb)
    statclasses.Stat("test 2", statclasses.Kinds.test, 2, pb)
    return pb


@pytest.fixture
def stat_1(playerbase_2):
    return playerbase_2.stats["test 1"]


@pytest.fixture
def arbitrary_pb():
    test_dataframe = pd.DataFrame(
        data={
            'col1': [1, 2, 3, 4, 5],
            'col2': [6, 7, 8, 9, 10],
            'cola': ['a', 'b', 'c', 'd', 'e'],
            'col3': [0.1, 0.2, 0.3, 0.4, 0.5],
        },
        index=[10, 11, 12, 13, 14]
    )
    pb = playerbase.PlayerBase()
    pb.players = {i: None for i in test_dataframe.index}
    pd.stats = {name: statclasses.Stat(name, statclasses.Kinds.test, None, pb) for name in test_dataframe.columns}
    pb.df = test_dataframe
    for stat in pb.stats.values():
        stat._linked_dataframe = test_dataframe
    return pb


class TestStatsBase:
    def test_stat_creation(self):
        pb = playerbase.PlayerBase()
        test_stat = statclasses.Stat("test stat", statclasses.Kinds.test, None, pb)
        assert str(test_stat) == "Test Stat"
        assert pb.stats['test stat'] is test_stat

        with pytest.raises(KeyError):
            test_stat_err = statclasses.Stat("test stat", statclasses.Kinds.test, None, pb)

    def test_stat_abbreviation(self, playerbase_2):
        playerbase_2.stats["test 1"].abbreviate("TS1")
        assert playerbase_2.stats["test 1"].abbreviation == "TS1"

        playerbase_2.stats["test 1"].abbreviate("TS2")
        assert playerbase_2.stats["test 1"].abbreviation == "TS2"

        with pytest.raises(KeyError):
            playerbase_2.stats["test 2"].abbreviate("TS2")

    def test_stat_get(self, arbitrary_pb):
        test_stat = arbitrary_pb.stats['col1']
        assert test_stat[10] == 1
        assert test_stat[13] == 4

    def test_stat_hash(self, playerbase_2):
        assert hash(playerbase_2.stats["test 1"]) != hash(playerbase_2.stats["test 2"])
        new_pb = playerbase.PlayerBase()
        new_test_1 = statclasses.Stat("test 1", statclasses.Kinds.test, None, new_pb)
        assert hash(playerbase_2.stats["test 1"]) != hash(new_pb.stats["test 1"])


@pytest.fixture
def calculatable_1(arbitrary_pb):
    calculatable = statclasses.Calculatable(
        "test c",
        statclasses.Kinds.test_dependent,
        initial_formula=lambda col1: col1,
        value_formula=lambda col2, col3: col2 + col3,
        pb=arbitrary_pb,
    )
    return calculatable


class TestCalculatable:
    def test_calculatable_fixture(self, calculatable_1):
        assert isinstance(calculatable_1, statclasses.Calculatable)

    def test_calculate(self, calculatable_1):
        assert calculatable_1.calculate_initial(10) == 1
        assert calculatable_1.calculate_initial(13) == 4
        assert calculatable_1.calculate_value(10) == pytest.approx(6.1)
        assert calculatable_1.calculate_value(14) == pytest.approx(10.5)

    def test_add(self, arbitrary_pb):
        new_calc = statclasses.Calculatable(
            "new stat",
            statclasses.Kinds.test,
            initial_formula=lambda col1, col2: col1 * col2,
            value_formula=lambda col1, col3:  col1 + col3,
            pb=arbitrary_pb
        )

        assert arbitrary_pb.df["new stat"][10] == 6
        assert arbitrary_pb.df["new stat"][14] == 50

    def test_add_empty(self):
        pb = playerbase.PlayerBase()
        statclasses.Calculatable(
            "new stat",
            statclasses.Kinds.test,
            pb=pb
        )

        assert "new stat" in pb.stats
        assert "new stat" in pb.df.columns

#
# class TestAllStats:
#     stat_param_ids = "name, default"
#     stat_params = [
#         ("determination", 0),
#         ("batting", -1),
#         ("i.t.", 0),
#         ("total pitches called", 0),
#         ("average pitch distance from edge", 0),
#         ("element", "Basic")
#     ]
#
#     @pytest.mark.parametrize(stat_param_ids, stat_params)
#     def test_build_all_stats(self, name, default):
#         assert name in all_stats
#
#     def test_len_all_stats(self):
#         assert len(all_stats) > 20
#
#     @pytest.mark.parametrize(stat_param_ids, stat_params)
#     def test_index_all_stats(self, name, default):
#         assert isinstance(all_stats[name], stats.Stat)
#         assert all_stats[name].default == default
#
#     def test_get_kind(self):
#         p_stats = all_stats['personality']
#         assert isinstance(p_stats, list)
#         assert len(p_stats) > 2
#         for stat in p_stats:
#             assert stat.default == 0
#             assert stat.kind == 'personality'
#
#     def test_get_personality(self):
#         d_stats = all_stats.all_personality('determination')
#         for stat in d_stats:
#             assert stat.personality == 'determination'
#
#     def test_initialize_all(self, arbitrary_df, stats_dict):
#         pass  # operates on all
#
#
# class TestNewStat:
#     # not using a fixture because this is basically modifying a global
#     test_stat = stats.Stat('test_stat', 'test')
#
#     def test_stat_addition(self):
#         assert TestNewStat.test_stat in all_stats
#         assert 'test_stat' in all_stats
#
#     def test_stat_attributes(self):
#         TestNewStat.test_stat.categorize(stats.baserunning)
#         TestNewStat.test_stat.personalize(stats.enthusiasm)
#
#         assert TestNewStat.test_stat in all_stats.all_category('baserunning')
#         assert TestNewStat.test_stat.personality is 'enthusiasm'
#

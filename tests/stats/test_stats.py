import pytest
import pandas as pd

from blaseball.stats import stats


@pytest.fixture
def stats_dict():
    stats_dict = {}
    stats.Stat("test 1", stats.Kinds.test, stats_dict)
    stats.Stat("test 2", stats.Kinds.test, stats_dict)
    return stats_dict


@pytest.fixture
def stat_1(stats_dict):
    return stats_dict["test 1"]


class TestStatsBase:
    def test_stat_creation(self):
        test_dict = {}
        test_stat = stats.Stat("test stat", stats.Kinds.test, test_dict)
        assert str(test_stat) == "Test Stat"

        with pytest.raises(KeyError):
            test_stat_err = stats.Stat("test stat", stats.Kinds.test, test_dict)

    def test_stat_abbreviation(self, stats_dict):
        stats_dict["test 1"].abbreviate("TS1")
        assert stats_dict["test 1"].abbreviation == "TS1"

        stats_dict["test 1"].abbreviate("TS2")
        assert stats_dict["test 1"].abbreviation == "TS2"

        with pytest.raises(KeyError):
            stats_dict["test 2"].abbreviate("TS2")


@pytest.fixture
def arbitrary_df():
    test_dataframe = pd.DataFrame(
        data={
            'col1': [1, 2, 3, 4, 5],
            'col2': [6, 7, 8, 9, 10],
            'cola': ['a', 'b', 'c', 'd', 'e'],
            'col3': [0.1, 0.2, 0.3, 0.4, 0.5],
        },
        index=[10, 11, 12, 13, 14]
    )
    return test_dataframe


@pytest.fixture
def calculatable_1(arbitrary_df, stats_dict):
    calculatable = stats.Calculatable("test c", stats.Kinds.test_dependent, stats_dict)
    calculatable.initial_formula = lambda col1: col1
    calculatable.value_formula = lambda col2, col3: col2 + col3
    calculatable.initialize_functions(arbitrary_df)


class TestCalculatable:
    def test_create(self, calculatable_1):
        assert isinstance(calculatable_1, stats.Calculatable)

    def test_calculate(self, calculatable_1):
        assert calculatable_1.calculate_initial(10) == 1
        assert calculatable_1.calculate_initial(13) == 4
        assert calculatable_1.calculate_value(10) == pytest.approx(6.1)
        assert calculatable_1.calculate_value(14) == pytest.approx(10.5)

    def test_uninitialized(self, stats_dict):
        calculatable = stats.Calculatable("test c", stats.Kinds.test_dependent, stats_dict)
        calculatable.initial_formula = lambda col1: col1
        assert stats_dict['test 1'].calculate_initial(10) is None

        with pytest.raises(RuntimeError):
            assert calculatable.calculate_initial(10) == 0


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

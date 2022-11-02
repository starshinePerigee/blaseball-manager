import pytest

from blaseball.stats import stats


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

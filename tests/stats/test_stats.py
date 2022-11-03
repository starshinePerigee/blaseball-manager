import pytest

from blaseball.stats import stats


class TestCharacterStats:
    def test_generate_name(self):
        assert isinstance(stats._generate_name(None, None), str)
        assert stats._generate_name(None, None) != stats._generate_name(None, None)

    def test_generate_name_case(self):
        assert stats._generate_name(None, None)[0].isupper()
        assert stats._generate_name(None, None)[1].islower()

    def test_generate_cid(self):
        assert isinstance(stats._generate_number(None, 10), int)
        # TODO



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
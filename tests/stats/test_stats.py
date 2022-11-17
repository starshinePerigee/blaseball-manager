import pytest

from blaseball.stats import stats, statclasses


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


class TestAllBase:
    def test_existence(self):
        assert "name" in stats.pb.stats

    def test_default_dict(self):
        assert len(stats.pb.stats) == len(stats.pb._default_stat_list)
        for stat, default in zip(stats.pb.stats.values(), stats.pb._default_stat_list):
            assert stat.default == default


class TestAllStats:
    stat_param_ids = "name, default"
    stat_params = [
        ("determination", 1.0),
        ("batting", -1),
        ("i.t.", -1),
        # ("total pitches called", 0),
        # ("average pitch distance from edge", 0),
        # ("element", "Basic")
    ]

    @pytest.mark.parametrize(stat_param_ids, stat_params)
    def test_build_all_stats(self, name, default):
        assert name in stats.pb.stats

    def test_len_all_stats(self):
        assert len(stats.pb.stats) > 20

    @pytest.mark.parametrize(stat_param_ids, stat_params)
    def test_index_all_stats(self, name, default):
        assert isinstance(stats.pb.stats[name], statclasses.Stat)
        assert stats.pb.stats[name].default == default

    def test_get_kind(self):
        p_stats = stats.pb.get_stats_with_kind(statclasses.Kinds.personality)
        assert isinstance(p_stats, list)
        assert len(p_stats) > 2
        for stat in p_stats:
            assert stat.default == 1.0
            assert stat.kind == 'personality'

    def test_get_personality(self):
        d_stats = stats.pb.get_stats_with_personality(stats.determination)
        for stat in d_stats:
            assert stat.personality == 'determination'

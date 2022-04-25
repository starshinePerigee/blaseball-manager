import pytest

from blaseball.stats import stats
from blaseball.util.statshortener import short, long


all_stats = stats.all_stats


class TestAllStats:
    stat_param_ids = "name, default"
    stat_params = [
        ("determination", 0),
        ("batting", -1),
        ("i.t.", 0),
        ("total pitches called", 0),
        ("average pitch distance from edge", 0),
        ("element", "Basic")
    ]

    @pytest.mark.parametrize(stat_param_ids, stat_params)
    def test_build_all_stats(self, name, default):
        assert name in all_stats

    def test_len_all_stats(self):
        assert len(all_stats) > 20

    @pytest.mark.parametrize(stat_param_ids, stat_params)
    def test_index_all_stats(self, name, default):
        assert isinstance(all_stats[name], stats.Stat)
        assert all_stats[name].default == default

    def test_get_kind(self):
        p_stats = all_stats['personality']
        assert isinstance(p_stats, list)
        assert len(p_stats) > 2
        for stat in p_stats:
            assert stat.default == 0
            assert stat.kind == 'personality'

    def test_get_personality(self):
        d_stats = all_stats.all_personality('determination')
        for stat in d_stats:
            assert stat.personality == 'determination'


class TestNewStat:
    # not using a fixture because this is basically modifying a global
    test_stat = stats.Stat('test_stat', 'test')

    def test_stat_addition(self):
        assert TestNewStat.test_stat in all_stats
        assert 'test_stat' in all_stats

    def test_stat_attributes(self):
        TestNewStat.test_stat.categorize(stats.baserunning)
        TestNewStat.test_stat.personalize(stats.enthusiasm)

        assert TestNewStat.test_stat in all_stats.all_category('baserunning')
        assert TestNewStat.test_stat.personality is 'enthusiasm'


class TestStatShortener:

    @pytest.mark.parametrize(
        "long_text, short_text",
        [
            ('batting', 'BAT'),
            ('battin', 'BAT'),
            ('trick', 'TRK'),
        ]
    )
    def test_short(self, long_text, short_text):
        assert short[long_text] == short_text

    def test_ambiguous_error(self):
        with pytest.raises(KeyError):
            assert short['stam'] == 'STM'

    def test_lookup_error(self):
        with pytest.raises(KeyError):
            assert short['XYZZY'] == 'xyz'
        with pytest.raises(KeyError):
            assert long['xyz'] == 'XYZZY'

    @pytest.mark.parametrize(
        'short_text, long_text',
        [
            ('ELE', 'element'),
            ('TOF', 'total offense'),
            ('tri', 'trickery'),
            ('sta', 'stamina'),
            ('stam', 'stamina')
        ]
    )
    def test_long(self, short_text, long_text):
        assert long[short_text] == long_text

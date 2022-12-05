import pytest

from blaseball.stats import statclasses, playerbase
from blaseball.stats import stats as s


@pytest.fixture
def playerbase_2():
    pb = playerbase.PlayerBase(statclasses.RECALCULATION_ORDER_TEST, statclasses.BASE_DEPENDENCIES_TEST)
    statclasses.Stat("test 1", statclasses.Kinds.test, 1, None, None, pb)
    statclasses.Stat("test 2", statclasses.Kinds.test, 2, None, None, pb)
    return pb


class TestStatsBase:
    def test_stat_creation(self):
        pb = playerbase.PlayerBase(statclasses.RECALCULATION_ORDER_TEST, statclasses.BASE_DEPENDENCIES_TEST)
        test_stat = statclasses.Stat("test stat", statclasses.Kinds.test, None, None, None, pb)
        assert str(test_stat) == "Test Stat"
        assert pb.stats['test stat'] is test_stat

        with pytest.raises(KeyError):
            test_stat_err = statclasses.Stat("test stat", statclasses.Kinds.test, None, None, None, pb)  # noqa

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
        # new_pb = playerbase.PlayerBase()
        # new_test_1 = statclasses.Stat("test 1", statclasses.Kinds.test, None, None, new_pb)
        # assert hash(playerbase_2.stats["test 1"]) != hash(new_pb.stats["test 1"])

    def test_hash_access(self, stat_1, stat_2, stat_3, arbitrary_pb):
        d = {stat_1: 1}
        assert d["col1"] == 1
        d[stat_2] = 2
        assert d[stat_2] == 2
        assert len(arbitrary_pb.df[stat_3]) == len(arbitrary_pb.players)


@pytest.fixture(scope='function')
def calculatable_1(arbitrary_pb):
    calculatable = statclasses.Calculatable(
        "test c",
        statclasses.Kinds.test_dependent,
        value_formula=lambda pb, cid: pb.stats['col2'][cid] + pb.stats['col3'][cid],
        playerbase=arbitrary_pb,
    )
    return calculatable


class TestCalculatable:
    def test_calculatable_fixture(self, calculatable_1):
        assert isinstance(calculatable_1, statclasses.Calculatable)

    def test_calculate(self, calculatable_1):
        assert calculatable_1.calculate_value(10) == pytest.approx(6.1)
        assert calculatable_1.calculate_value(14) == pytest.approx(10.5)

    def test_add(self, arbitrary_pb):
        new_stat = statclasses.Calculatable(
            "new stat",
            statclasses.Kinds.test_dependent,
            value_formula=lambda pb, cid: pb.stats['col1'][cid] * pb.stats['col2'][cid],
            playerbase=arbitrary_pb
        )

        assert new_stat[10] == 6
        assert new_stat[14] == 50

    def test_add_empty(self):
        pb = playerbase.PlayerBase(statclasses.RECALCULATION_ORDER_TEST, statclasses.BASE_DEPENDENCIES_TEST)
        statclasses.Calculatable(
            "new stat",
            statclasses.Kinds.test,
            playerbase=pb
        )
        pb.write_stats_to_dataframe()

        assert "new stat" in pb.stats
        assert "new stat" in pb.df.columns


class TestWeight:
    def test_weighting(self, arbitrary_pb):
        test_weight = statclasses.Weight("test weight", kind=statclasses.Kinds.test_dependent, playerbase=arbitrary_pb)

        stat_1 = statclasses.Stat("s1", statclasses.Kinds.test, 0.5, None, None, arbitrary_pb)
        stat_1.weight(test_weight, 2)

        stat_2 = statclasses.Stat("s2", statclasses.Kinds.test, 1, None, None, arbitrary_pb)
        stat_2.weight(test_weight, 1)

        assert test_weight.calculate_value(10) == pytest.approx((0.5 * 2 + 1) / 3)


@pytest.fixture
def test_descriptor(arbitrary_pb):
    return statclasses.Descriptor("test descriptor", kind=statclasses.Kinds.test_dependent, playerbase=arbitrary_pb)


class TestDescriptor:
    def test_value_dict(self):
        value_dict = {2: "two"}
        assert statclasses.Descriptor._parse_value_dict(value_dict, 1.0) == "two"

        assert isinstance(statclasses.Descriptor._parse_value_dict(value_dict, 2.1), str)

        value_dict[1] = "one"
        assert statclasses.Descriptor._parse_value_dict(value_dict, 0.5) == "one"
        assert statclasses.Descriptor._parse_value_dict(value_dict, 1.5) == "two"

    def test_uninitialize(self, test_descriptor):
        assert test_descriptor.calculate_value(10) == test_descriptor.default

    def test_parse_second_level_weird(self, arbitrary_pb):
        col3 = arbitrary_pb.stats['col3']
        assert statclasses.Descriptor._parse_second_level("test str", col3, 0.1, 10, 1.0) == "test str"

        value_dict = {2: "two", 1: "one"}
        assert statclasses.Descriptor._parse_second_level(value_dict, col3, 0.5, 10, 1.0) == "one"

        fail_dict = {col3: "merp nerp"}
        with pytest.raises(RuntimeError):
            statclasses.Descriptor._parse_second_level(fail_dict, col3, 0.1, 10, 1.0)

    # _parse_second_level(first_level_result, highest_stat, highest_value, player_index, secondary_threshold):
    def test_parse_second_level_str(self, arbitrary_pb):
        col3 = arbitrary_pb.stats['col3']
        col4 = arbitrary_pb.stats['col4']
        col5 = arbitrary_pb.stats['col5']
        test_dict = {
            col3: "three",
            col4: "four",
            col5: "five"
        }
        # test with no secondary
        assert statclasses.Descriptor._parse_second_level(test_dict, col4, 1.0, 10, 1.0) == "four"
        # test secondary
        assert statclasses.Descriptor._parse_second_level(test_dict, col4, 0.5, 10, 0.1) == "three"
        # test zeros
        assert statclasses.Descriptor._parse_second_level(test_dict, col4, 0.0, 10, 0.1) == "three"

    def test_parse_second_level_value_dict(self, arbitrary_pb):
        value_dict = {2: "two", 1: "one"}
        col3 = arbitrary_pb.stats['col3']

        assert statclasses.Descriptor._parse_second_level(value_dict, col3, 0.4, 10, 1.0) == "one"

    def test_single_str(self, test_descriptor, arbitrary_pb):
        test_descriptor.add_weight(arbitrary_pb.stats['col3'], "col3 focused")
        test_descriptor.add_weight(arbitrary_pb.stats['col4'], "col4 focused")

        assert test_descriptor.calculate_value(10) == "col4 focused"
        assert test_descriptor.calculate_value(14) == "col3 focused"

        # just make sure it doesn't die if they're equal:
        assert isinstance(test_descriptor.calculate_value(12), str)

    def test_single_thresholds(self, test_descriptor, arbitrary_pb):
        test_descriptor.add_weight(
            arbitrary_pb.stats['col3'],
            {0: "0", 0.15: "0.15", 0.35: "0.35", 0.6: "0.6", 2: "2"}
        )

        assert test_descriptor.calculate_value(10) == "0.15"
        assert test_descriptor.calculate_value(14) == "0.6"

    def test_second_order_stats(self, test_descriptor, arbitrary_pb):
        col3 = arbitrary_pb.stats['col3']
        col4 = arbitrary_pb.stats['col4']

        test_descriptor.add_weight(
            col3,
            {col3: "11", col4: "12"}
        )
        test_descriptor.add_weight(
            col4,
            {col3: "21", col4: "22"}
        )

        # 0.33, 0.66, 1, 0.75, 0.6
        test_descriptor.secondary_threshold = 0.63

        assert test_descriptor.calculate_value(10) == "22"
        assert test_descriptor.calculate_value(11) == "21"
        assert test_descriptor.calculate_value(13) == "12"
        assert test_descriptor.calculate_value(14) == "11"
        assert isinstance(test_descriptor.calculate_value(12), str)

    def test_single_second_order(self, test_descriptor, arbitrary_pb):
        pass  # TODO

    def test_all(self, test_descriptor, arbitrary_pb):
        stat_1 = arbitrary_pb.stats['col3']
        stat_2 = arbitrary_pb.stats['col4']

        test_descriptor.add_weight(
            stat_1,
            {stat_1: "11", stat_2: "12"}
        )
        test_descriptor.add_weight(
            stat_2,
            {stat_1: "21", stat_2: "22"}
        )
        test_descriptor.add_all(
            {stat_1: "all_1", stat_2: "all_2"}
        )
        test_descriptor.secondary_threshold = 0.6

        assert test_descriptor.calculate_value(10) == "22"
        assert test_descriptor.calculate_value(11) == "all_2"
        assert "all" in test_descriptor.calculate_value(12)
        assert test_descriptor.calculate_value(13) == "all_1"
        assert test_descriptor.calculate_value(14) == "11"

    def test_all_zeros_integrated(self, player_1):
        player_1.set_all_stats(0)
        assert player_1[s.defense_descriptor] == "Force Pitcher"

    # dict-dict-dict is not supported. If we need it, we can implement it.
    # def test_third_order_stats_dict_x3(self, test_descriptor, arbitrary_pb):
    #     stat_1 = arbitrary_pb.stats['col3']
    #     stat_2 = arbitrary_pb.stats['col4']
    #     stat_3 = statclasses.Stat(
    #         'col5',
    #         statclasses.Kinds.test,
    #         0.4,
    #         arbitrary_pb
    #     )
    #
    #     test_descriptor.secondary_threshold = 0.63
    #
    #     test_descriptor.add_weight(
    #         stat_1,
    #         {
    #             stat_1: {stat_1: "111", stat_2: "112", stat_3: "113"},
    #             stat_2: {stat_1: "121", stat_2: "122", stat_3: "123"},
    #         }
    #     )
    #     test_descriptor.add_weight(
    #         stat_2,
    #         {
    #             stat_1: {stat_1: "211", stat_2: "212", stat_3: "213"},
    #             stat_2: {stat_1: "221", stat_2: "222", stat_3: "223"},
    #         }
    #     )
    #     assert test_descriptor.calculate_value(10) == "223"
    #     assert test_descriptor.calculate_value(11) == "213"
    #     assert test_descriptor.calculate_value(13) == "123"
    #     assert test_descriptor.calculate_value(14) == "111"
    #     assert isinstance(test_descriptor.calculate_value(12), str)

    def test_third_order_stats_dict_dict_list(self, test_descriptor, arbitrary_pb):
        col_3 = arbitrary_pb.stats['col3']
        col_4 = arbitrary_pb.stats['col4']

        test_descriptor.add_weight(
            col_3,
            {
                col_3: {0: "11.0", 0.35: "11.35", 0.6: "11.6"},
                col_4: {0: "12.0", 0.35: "12.35", 0.6: "12.6"}
            }
        )
        test_descriptor.add_weight(
            col_4,
            {
                col_3: {0: "21.0", 0.35: "21.35", 0.6: "21.6"},
                col_4: {0: "22.0", 0.35: "22.35", 0.6: "22.6"}
            }
        )
        test_descriptor.secondary_threshold = 0.63

        # reminder:
        # 'col3': [0.1, 0.2, 0.3, 0.4, 0.5],
        # 'col4': [0.3, 0.3, 0.3, 0.3, 0.3]

        assert test_descriptor.calculate_value(10) == "22.35"
        assert test_descriptor.calculate_value(11) == "21.35"
        assert test_descriptor.calculate_value(13) == "12.6"
        assert test_descriptor.calculate_value(14) == "11.6"
        assert isinstance(test_descriptor.calculate_value(12), str)

    def test_all_zeros(self, test_descriptor, arbitrary_pb):
        col_3 = arbitrary_pb.stats['col3']
        col_4 = arbitrary_pb.stats['col4']
        arbitrary_pb.df['col3'] = 0
        arbitrary_pb.df['col4'] = 0
        test_descriptor.add_weight(
            col_3,
            {
                col_3: {0: "11.0", 0.35: "11.35", 0.6: "11.6"},
                col_4: {0: "12.0", 0.35: "12.35", 0.6: "12.6"}
            }
        )
        test_descriptor.add_weight(
            col_4,
            {
                col_3: {0: "21.0", 0.35: "21.35", 0.6: "21.6"},
                col_4: {0: "22.0", 0.35: "22.35", 0.6: "22.6"}
            }
        )
        assert isinstance(test_descriptor.calculate_value(12), str)


class TestRating:
    @pytest.mark.parametrize(
        "cid, result",
        [(10, 0.25), (11, 0.25), (12, 0.4), (13, 1.1), (14, 1.5)]
    )
    def test_initial(self, arbitrary_pb, patcher, cid, result):
        patcher.patch('blaseball.stats.statclasses.rand', lambda: 0.5)
        personality = arbitrary_pb.stats['col5']
        test_rating = statclasses.Rating('test rating', personality, None, arbitrary_pb, statclasses.Kinds.test)
        assert test_rating.calculate_initial(cid) == pytest.approx(result)


def test_averaging(arbitrary_pb):
    count = statclasses.Stat(
        'base_count',
        statclasses.Kinds.test,
        0,
        playerbase=arbitrary_pb
    )

    average, total = statclasses.build_averaging(
        count,
        "averaging",
        "total",
        average_kind=statclasses.Kinds.test_dependent,
        total_kind=statclasses.Kinds.test,
        playerbase=arbitrary_pb
    )

    assert arbitrary_pb.stats['averaging'] is average

    # test div 0
    assert average[10] == 0

    player_0 = arbitrary_pb[10]
    player_0[count] += 2

    assert player_0[average] == 0

    player_0[total] += 5
    assert player_0[average] == pytest.approx(2.5)

    player_0.recalculate()
    assert player_0[average] == pytest.approx(2.5)

    player_0.save_to_pb()
    assert arbitrary_pb.df['averaging'][10] == pytest.approx(2.5)

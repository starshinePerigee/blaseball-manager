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
            'col4': [0.3, 0.3, 0.3, 0.3, 0.3],
            'col5': [0, 0.2, 0.8, 1.6, 2.0]
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


class TestWeight:
    def test_weighting(self, arbitrary_pb):
        test_weight = statclasses.Weight("test weight", pb=arbitrary_pb)

        stat_1 = statclasses.Stat("s1", statclasses.Kinds.test, 0.5, arbitrary_pb)
        stat_1.weight(test_weight, 2)

        stat_2 = statclasses.Stat("s2", statclasses.Kinds.test, 1, arbitrary_pb)
        stat_2.weight(test_weight, 1)

        assert test_weight.calculate_value(10) == pytest.approx((0.5 * 2 + 1) / 3)


@pytest.fixture
def test_descriptor(arbitrary_pb):
    return statclasses.Descriptor("test descriptor", pb=arbitrary_pb)


class TestDescriptor:
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

        # 0.33, 0.66, 1, 0.75, 0.6
        test_descriptor.secondary_threshold = 0.63

        assert test_descriptor.calculate_value(10) == "22"
        assert test_descriptor.calculate_value(11) == "21"
        assert test_descriptor.calculate_value(13) == "12"
        assert test_descriptor.calculate_value(14) == "11"
        assert isinstance(test_descriptor.calculate_value(12), str)

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
        test_rating, test_rating_base = statclasses.build_rating('test rating', personality, None, arbitrary_pb)
        assert test_rating_base.calculate_initial(cid) == pytest.approx(result)

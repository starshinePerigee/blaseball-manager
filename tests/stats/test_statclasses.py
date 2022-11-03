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
            'col4': [0.3, 0.3, 0.3, 0.3, 0.3]
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

    def test_third_order_stats_dict_dict_list(self):
        # TODO
        pass

    def test_third_order_stats_dict_x3(self):
        #TODO
        pass
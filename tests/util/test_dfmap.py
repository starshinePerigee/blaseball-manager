import pytest
import pandas as pd

from blaseball.util.dfmap import dataframe_map

test_dataframe = pd.DataFrame(
    data={
        'col1': [1, 2, 3, 4, 5],
        'col2': [6, 7, 8, 9, 10],
        'cola': ['a', 'b', 'c', 'd', 'e'],
        'col3': [0.1, 0.2, 0.3, 0.4, 0.5],
    },
    index=[10, 11, 12, 13, 14]
)


def test_dataframe_map_single():
    def test_add(col1, col3):
        return col1 + col3

    mapped_add = dataframe_map(test_add, test_dataframe)

    assert mapped_add(11) == 2.2
    assert mapped_add(14) == 5.5


def test_dataframe_map_multiple():
    def test_add(col1, col3):
        return col1 + col3
    mapped_add = dataframe_map(test_add, test_dataframe)

    def test_concat(cola, col1):
        return cola + str(col1)
    mapped_cat = dataframe_map(test_concat, test_dataframe)

    assert mapped_add(10) == 1.1
    assert mapped_cat(13) == 'd4'
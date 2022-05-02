"""This holds functions useful for mocking and tests, such as replacements for random.

This used to be in tests/ but pycharm debug + pytest really didn't like it for some reason?"""


from scipy.stats import norm


def random_across_range(target_function, my_monkeypatch):
    """This mocks out rand() calls in a for loop to test random parameters and get averages"""
    for i in range(0, 100):
        # for cleanliness, we want to inclue 0 and 1, but also want 100 values exactly
        value = i / 99
        my_monkeypatch.setattr(target_function, lambda: value)
        yield value



def normal_across_range(target_function, my_monkeypatch):
    """This mocks out norm() but also inclues one in a million outliers in either direction"""
    worst_case_order_of_magnitude = 6
    neg_outliers = [1 / 10 ** x for x in range(worst_case_order_of_magnitude, 2, -1)]
    pos_outliers = [1 - x for x in neg_outliers[::-1]]
    remaining = 100 - len(neg_outliers) * 2
    normal_values = [i / (remaining + 1) for i in range(1, remaining + 1)]
    all_values = neg_outliers + normal_values + pos_outliers

    for value in all_values:
        my_monkeypatch.setattr(target_function, lambda loc, scale=1: norm.ppf(value) * scale + loc)
        yield value
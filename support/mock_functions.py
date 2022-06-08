"""This holds functions useful for mocking and tests, such as replacements for random.

This used to be in tests/ but pycharm debug + pytest really didn't like it for some reason?"""


from scipy.stats import norm
from typing import Callable
from functools import partial


def random_across_range(target_function: str, my_monkeypatch):
    """This mocks out rand() calls in a for loop to test random parameters and get averages"""
    for i in range(0, 100):
        # for cleanliness, we want to inclue 0 and 1, but also want 100 values exactly
        value = i / 99
        my_monkeypatch.setattr(target_function, lambda: value)
        yield value


def normal_across_range(target_function: str, my_monkeypatch):
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


class FunctionPatched:
    # quick helper class to make data a little clearer
    def __init__(self, target_function: str, replacement_function: Callable, iterations=10, my_monkeypatch=None):
        self.target_function = target_function
        # replacement_function is a function that takes all normal arguments as the original function, but
        # also includes an iteration keyword parameter.
        self.replacement_function = replacement_function
        self.iterations = iterations
        self.monkeypatch = my_monkeypatch

    def apply(self, this_iteration: int):
        """Apply this patch"""
        iterated_function = partial(self.replacement_function, iteration=this_iteration)
        self.monkeypatch.setattr(
            self.target_function,
            iterated_function
        )


class FunctionPatcher:
    """A class designed to handle multiple random calls in a single instance."""
    def __init__(self, my_monkeypatch):
        # as before, calling the monkeypatch test fixture from here breaks, so we have to pass a monkeypatch
        # initialized from our test fixture.
        self.monkeypatch = my_monkeypatch
        self.functions = []

    def total_iterations(self):
        iterations = 1
        for function in self.functions:
            iterations *= function.iterations
        return iterations

    def patch(self, target_function: str, replacement_function: Callable, iterations=10) -> None:
        """Set a call to rand() to be patched when you iterate over this RandomPatcher"""
        self.functions += [FunctionPatched(target_function, replacement_function, iterations, self.monkeypatch)]

    def __len__(self):
        return self.total_iterations()

    def __iter__(self):
        if len(self.functions) < 1:
            raise RuntimeError("Patch random functions before iterating!")
        for iteration in range(0, self.total_iterations()):
            current_depth = 1
            for function in self.functions:
                sub_iteration = int(iteration / current_depth) % function.iterations
                current_depth *= function.iterations
                function.apply(sub_iteration)
            yield iteration

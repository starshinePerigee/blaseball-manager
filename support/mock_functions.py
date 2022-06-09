"""This holds functions useful for mocking and tests, such as replacements for random.

This used to be in tests/ but pycharm debug + pytest really didn't like it for some reason?"""


from scipy.stats import norm
from typing import Callable
from functools import partial
from inspect import signature


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


def build_random_across_range(iterations) -> Callable:
    if iterations == 1:
        def new_random_across_range(iteration):
            return 0.5
    else:
        def new_random_across_range(iteration):
            # iterate from 0 to 1 inclusive
            return iteration / (iterations - 1)
    return new_random_across_range


def build_normal_across_range(iterations, worst_case_order_of_magnitude=6) -> Callable:
    """This mocks out norm() but also inclues one in a million outliers in either direction"""
    if iterations == 1:
        def new_normal_across_range(loc, scale=1, iteration=0):
            return loc
    else:
        if iterations <= 10:
            # build three outliers
            neg_orders_of_mag = list(range(worst_case_order_of_magnitude, 2, -2))[:3]
            neg_outliers = [1/10 ** x for x in neg_orders_of_mag]
        else:
            neg_outliers = [1 / 10 ** x for x in range(worst_case_order_of_magnitude, 2, -1)]
        pos_outliers = [1 - x for x in neg_outliers[::-1]]
        remaining = 100 - len(neg_outliers) * 2
        normal_values = [i / (remaining + 1) for i in range(1, remaining + 1)]
        all_values = neg_outliers + normal_values + pos_outliers

        def new_normal_across_range(loc, scale=1, iteration=0):
            return norm.ppf(all_values[iteration]) * scale + loc
    return new_normal_across_range


class FunctionPatcher:
    """A class designed to handle multiple random calls in a single instance.
    Take a look at test_swing_stats_tracking for the full usage of this module.
    """
    def __init__(self, my_monkeypatch):
        # as before, calling the monkeypatch test fixture from here breaks, so we have to pass a monkeypatch
        # initialized from our test fixture.
        self.monkeypatch = my_monkeypatch
        self.functions = []

    def reset(self):
        """Clears the function stack.
        DOES NOT UNDO ANY EXISTING MONKEYPATCHES!"""
        self.functions = []

    def total_iterations(self):
        iterations = 1
        for function in self.functions:
            iterations *= function.iterations
        return iterations

    def patch(self, target_function: str, replacement_function: Callable, iterations=1) -> None:
        """Set a call to rand() to be patched when you iterate over this RandomPatcher"""
        if iterations == 1:
            if 'iteration' in signature(replacement_function).parameters:
                iterated_function = partial(replacement_function, iteration=0)
                self.monkeypatch.setattr(target_function, iterated_function)
            else:
                self.monkeypatch.setattr(target_function, replacement_function)
        else:
            if 'iteration' not in signature(replacement_function).parameters:
                raise NameError("Include keyword argument 'iteration' in all iterated patch functions!")
            self.functions += [FunctionPatched(target_function, replacement_function, iterations, self.monkeypatch)]

    def patch_rand(self, target_function: str, iterations=100):
        self.functions += [FunctionPatched(
            target_function,
            build_random_across_range(iterations),
            iterations,
            self.monkeypatch)
        ]

    def patch_normal(self, target_function: str, iterations=100, worst_case_order_of_magnitude=6):
        self.functions += [FunctionPatched(
            target_function,
            build_normal_across_range(iterations, worst_case_order_of_magnitude),
            iterations,
            self.monkeypatch)
        ]

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

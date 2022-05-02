import pytest
from _pytest.monkeypatch import MonkeyPatch

from prototypes import justrand
from tests import conftest
from scipy.stats import norm
from random import random

import functools


def random_return_point_four():
    return 0.4


def random_across_range():
    previous = 1
    while previous <= 2:
        previous += 0.01
        yield previous


def monkey_across_range(target_fn):
    previous = 1
    monkeypatch = MonkeyPatch()
    while previous <= 2:
        previous += 0.01
        monkeypatch.setattr(target_fn, lambda: previous)
        yield previous


def indirect_monkey_range(target_fn, monkey):
    previous = 1
    while previous <= 2:
        previous += 0.01
        monkey.setattr(target_fn, lambda: previous)
        yield previous


@pytest.fixture
def fixture_monkey_range(monkeypatch):
    return functools.partial(indirect_monkey_range, monkey=monkeypatch)


def test_norm_range():
    worst_case_order_of_magnitude = 6
    neg_outliers = [1 / 10 ** x for x in range(worst_case_order_of_magnitude, 2, -1)]
    pos_outliers = [1 - x for x in neg_outliers[::-1]]
    remaining = 100 - len(neg_outliers) * 2
    normal_values = [i / (remaining + 1) for i in range(1, remaining + 1)]
    all_values = neg_outliers + normal_values + pos_outliers
    for i, value in enumerate(all_values):
        yield all_values[i], norm.ppf(value)

for n in test_norm_range():
    print(n)


print(len([x for x in test_norm_range()]))


class TestRandom:
    def test_justrandom(self, monkeypatch):
        monkeypatch.setattr('prototypes.justrand.random', random_return_point_four)

        assert 0.39 < justrand.just_random() < 0.41

    def test_justrandom_across(self, monkeypatch):
        n = 0
        for x in random_across_range():
            monkeypatch.setattr('prototypes.justrand.random', lambda: x)
            n += justrand.just_random()

        assert n / 100 == pytest.approx(1.505)

    def test_monkey_across(self):
        n = 0
        for __ in monkey_across_range('prototypes.justrand.random'):
            n += justrand.just_random()
        assert n/100 == pytest.approx(1.505)

    def test_monkey_cleanest(self, fixture_monkey_range):
        n = 0
        for __ in fixture_monkey_range('prototypes.justrand.random'):
            n += justrand.just_random()
        assert n/100 == pytest.approx(1.505)

    def test_from_conf(self, monkey_rand_100):
        n = 0
        for __ in monkey_rand_100('prototypes.justrand.random'):
            n += justrand.just_random()
        assert n/100 == pytest.approx(0.5)

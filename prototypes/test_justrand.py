import pytest

from prototypes import justrand
from random import random


def random_return_point_four():
    return 0.4


class TestRandom:
    def test_justrandom(self, monkeypatch):
        monkeypatch.setattr('prototypes.justrand.random', random_return_point_four)

        assert 0.39 < justrand.just_random() < 0.41

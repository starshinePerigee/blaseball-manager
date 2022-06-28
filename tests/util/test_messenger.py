from enum import Enum

from blaseball.util.messenger import Messenger, CircuitBreaker, CountStore

import pytest


class Receiver:
    def __init__(self, messenger=None):
        self.count = 0
        if messenger is not None:
            messenger.subscribe(self.increment, TestTags.count)

    def increment(self, number):
        self.count += number

    def decrement(self, number):
        self.count -= number


class Bidirectional(Receiver):
    def __init__(self, messenger=None):
        super().__init__(messenger)
        self.messenger = messenger

    def send(self, value):
        self.messenger.send(value, TestTags.count)


class TestTags(Enum):
    count = "count",
    decount = "decount",
    count_2 = "count 2",
    count_3 = "count 3"


class TestMessenger:
    def test_one_to_one(self):
        m = Messenger()
        r = Receiver(m)

        assert r.count == 0
        m.send(1, TestTags.count)
        assert r.count == 1

        m.subscribe(r.decrement, TestTags.decount)
        m.send(2, TestTags.decount)
        assert r.count == -1

    def test_many_to_many(self):
        m = Messenger()
        r = Receiver(m)
        b1 = Bidirectional(m)
        b2 = Bidirectional(m)

        m.send(1, TestTags.count)
        assert r.count == 1
        assert b1.count == 1

        b1.send(2)
        assert r.count == 3
        assert b1.count == 3
        assert b2.count == 3

        m.subscribe(b2.increment, TestTags.count_2)
        m.subscribe(b1.increment, [TestTags.count_2, TestTags.count_3])
        m.send(6, TestTags.count_2)
        m.send(10, TestTags.count_3)
        assert r.count == 3
        assert b1.count == 19
        assert b2.count == 9

    def test_null(self):
        m1 = Messenger()
        l1 = Receiver()
        m1.subscribe(l1.increment)

        m1.send(4)
        assert l1.count == 4

    def test_null_error(self):
        m = Messenger()
        l1 = Receiver(m)

        with pytest.raises(KeyError):
            m.send(4)

    def test_unsubscribe(self):
        m = Messenger()
        r = Receiver(m)
        m.subscribe(r.increment, [TestTags.count_2, TestTags.count_3])
        m.unsubscribe(r.increment, [TestTags.count, TestTags.count_2])
        m.send(2, TestTags.count)
        m.send(3, TestTags.count_2)
        m.send(5, TestTags.count_3)
        assert r.count == 5

    def test_strings(self):
        m = Messenger()
        assert "0 tags" in str(m)
        assert "0 total listeners" in str(m)

        r = Receiver(m)
        m.subscribe(r.decrement, TestTags.decount)
        m.subscribe(r.decrement, TestTags.count)

        assert "2 tags" in str(m)
        assert "3 total listeners" in str(m)

        assert isinstance(repr(m), str)


class TestListeners:
    def test_circuitbreaker(self):
        m = Messenger()
        circuitbreaker = CircuitBreaker(m, TestTags.count, [list, str])

        m.send("test", TestTags.count)
        m.send([1, 2, 3], TestTags.count)

        with pytest.raises(TypeError):
            m.send(1, TestTags.count)

    def test_countstore(self):
        m = Messenger()
        count_store_unlimited = CountStore(m, TestTags.count, -1)
        count_store_none = CountStore(m, TestTags.count, 0)
        count_store_3 = CountStore(m, TestTags.count, 3)

        for i in range(10):
            m.send(i, TestTags.count)

        for count_store in [count_store_unlimited, count_store_3, count_store_none]:
            assert count_store.count == 10

        assert count_store_unlimited.items == [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
        assert count_store_unlimited[-1] == 0
        assert len(count_store_unlimited) == 10
        assert count_store_none.items == []
        assert count_store_3.items == [9, 8, 7]
        assert len(count_store_3) == 3

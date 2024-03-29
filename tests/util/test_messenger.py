from enum import Enum

from blaseball.util.messenger import Messenger, CircuitBreaker, BreakerError, CountStore, ReceivedArgument

import pytest


class Receiver:
    class_numbers = []
    running_id = 1

    @classmethod
    def reset(cls):
        cls.running_id = 1
        cls.class_numbers = []

    def __init__(self, messenger=None):
        self.count = 0
        if messenger is not None:
            messenger.subscribe(self.increment, TestTags.count)
        self.id = Receiver.running_id
        Receiver.running_id += 1

    def increment(self, number):
        self.count += number

    def decrement(self, number):
        self.count -= number

    def append(self):
        self.class_numbers += [self.id]


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
    append = "append"


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

    def test_handle_error(self, logger_store):
        m = Messenger()
        counter = Receiver(m)
        m.send("this will throw an error", TestTags.count)
        assert "TypeError" in logger_store

    def test_null_priority(self):
        Receiver.reset()
        m = Messenger()
        r1 = Receiver(m)
        r2 = Receiver(m)

        m.subscribe(r1.append, TestTags.append)
        m.subscribe(r2.append, TestTags.append)

        m.send(tags=TestTags.append)
        assert r1.class_numbers == [1, 2]

        m.send(tags=TestTags.append)
        assert r1.class_numbers == [1, 2, 1, 2]

    def test_priority(self):
        Receiver.reset()
        m = Messenger()
        r1 = Receiver(m)
        r2 = Receiver(m)
        r3 = Receiver(m)
        r4 = Receiver(m)

        m.subscribe(r1.append, TestTags.append)  # priority 0
        m.subscribe(r2.append, TestTags.append, priority=10)
        m.subscribe(r3.append, TestTags.append, priority=-1)
        m.subscribe(r4.append, TestTags.append, priority=5)

        m.send(tags=TestTags.append)
        assert r1.class_numbers == [2, 4, 1, 3]

        m.send(tags=TestTags.append)
        assert r1.class_numbers == [2, 4, 1, 3] * 2


class TestQueues:
    global_messenger = Messenger()
    global_list = []

    def test_queue_priority(self):
        TestQueues.global_list = []

        def fast_fn():
            TestQueues.global_list += [3]

        TestQueues.global_messenger.subscribe(fast_fn, TestTags.count_3)

        def slow_fn():
            TestQueues.global_list += [2]

        TestQueues.global_messenger.subscribe(slow_fn, TestTags.count_2)

        def outer_fn():
            TestQueues.global_list += [1]
            TestQueues.global_messenger.queue(tags=TestTags.count_2)
            TestQueues.global_messenger.send(tags=TestTags.count_3)

        TestQueues.global_messenger.subscribe(outer_fn, TestTags.count)

        TestQueues.global_messenger.queue(tags=TestTags.count)
        assert TestQueues.global_list == [1, 3, 2]

        TestQueues.global_list = []
        TestQueues.global_messenger.send(tags=TestTags.count)
        # because this uses send, the event queue gets initialized inside outer_fn
        # instead of in the test_queue_priority context,
        # and thus slow_fn triggers before fast_fn
        assert TestQueues.global_list == [1, 2, 3]


def fake_messenger_send(argument=None, tags=""):
    if not isinstance(tags, list):
        tags = [tags]

    return fake_receive(argument)


def fake_receive(argument=None):
    return ReceivedArgument(argument)


class TestListeners:
    def test_circuitbreaker(self):
        m = Messenger()
        circuitbreaker = CircuitBreaker(m, TestTags.count, [list, str])

        m.send("test", TestTags.count)
        m.send([1, 2, 3], TestTags.count)

        with pytest.raises(BreakerError):
            m.send(1, TestTags.count)

    @pytest.mark.parametrize(
        "tags",
        [
            [None],
            [TestTags.count],
            [TestTags.count_2, TestTags.count_3]
        ]
    )
    def test_received_argument(self, tags):
        test_argument = fake_messenger_send("test", tags)
        assert test_argument.great_grand_caller.function == "test_received_argument"
        assert test_argument.tags == tags
        assert isinstance(str(test_argument), str)
        assert test_argument.argument == "test"

    def test_countstore(self):
        m = Messenger()
        count_store_unlimited = CountStore(m, TestTags.count, -1)
        count_store_none = CountStore(m, TestTags.count, 0)
        count_store_3 = CountStore(m, TestTags.count, 3)

        for i in range(10):
            m.send(i, TestTags.count)

        for count_store in [count_store_unlimited, count_store_3, count_store_none]:
            assert count_store.count == 10

        assert [item.argument for item in count_store_unlimited.items] == [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
        assert count_store_unlimited[-1] == 0
        assert len(count_store_unlimited) == 10
        assert count_store_none.items == []
        assert [item.argument for item in count_store_3.items] == [9, 8, 7]
        assert len(count_store_3) == 3

    def test_countstore_clear(self):
        m = Messenger()
        count_store_3 = CountStore(m, TestTags.count, 3)

        for i in range(2):
            m.send(i, TestTags.count)

        count_store_3.clear()

        assert len(count_store_3) == 0
        assert count_store_3.items == []

    def test_countstore_tag_inventory(self):
        m = Messenger()
        count_store = CountStore(m, TestTags.count, -1)
        m.subscribe(count_store.respond, TestTags.count_2)
        m.subscribe(count_store.respond, TestTags.count_3)

        for i in range(4):
            m.send(1, TestTags.count)

        m.send(2, TestTags.count_2)

        inventory = count_store.tag_inventory()
        assert inventory[TestTags.count] == 4
        assert inventory[TestTags.count_2] == 1
        assert inventory[TestTags.count_3] == 0

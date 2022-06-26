from blaseball.util.messenger import Messenger


class Receiver:
    def __init__(self, messenger=None):
        self.count = 0
        if messenger is not None:
            messenger.subscribe(self.increment, 'count')

    def increment(self, number):
        self.count += number

    def decrement(self, number):
        self.count -= number


class Bidirectional(Receiver):
    def __init__(self, messenger=None):
        super().__init__(messenger)
        self.messenger = messenger

    def send(self, value):
        self.messenger.send(value, 'count')


class TestMessenger:
    def test_one_to_one(self):
        m = Messenger()
        r = Receiver(m)

        assert r.count == 0
        m.send(1, 'count')
        assert r.count == 1

        m.subscribe(r.decrement, 'decount')
        m.send(2, 'decount')
        assert r.count == -1

    def test_many_to_many(self):
        m = Messenger()
        r = Receiver(m)
        b1 = Bidirectional(m)
        b2 = Bidirectional(m)

        m.send(1, 'count')
        assert r.count == 1
        assert b1.count == 1

        b1.send(2)
        assert r.count == 3
        assert b1.count == 3
        assert b2.count == 3

        m.subscribe(b2.increment, 'count 2')
        m.subscribe(b1.increment, ['count 2', 'count 3'])
        m.send(6, 'count 2')
        m.send(10, 'count 3')
        assert r.count == 3
        assert b1.count == 19
        assert b2.count == 9

    def test_unsubscribe(self):
        m = Messenger()
        r = Receiver(m)
        m.subscribe(r.increment, ['count 2', 'count 3'])
        m.unsubscribe(r.increment, ['count', 'count 2'])
        m.send(2, 'count')
        m.send(3, 'count 2')
        m.send(5, 'count 3')
        assert r.count == 5

    def test_strings(self):
        m = Messenger()
        assert "0 tags" in str(m)
        assert "0 total listeners" in str(m)

        r = Receiver(m)
        m.subscribe(r.decrement, 'decount')
        m.subscribe(r.decrement, 'count')

        assert "2 tags" in str(m)
        assert "3 total listeners" in str(m)

        assert isinstance(repr(m), str)

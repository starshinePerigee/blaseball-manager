import pytest

from blaseball.playball import event


@pytest.fixture
def test_event():
    return event.Event('test event')


class TestEvent:
    def test_update_init(self, test_event):
        assert isinstance(str(test_event), str)
        assert test_event.feed_text() == []

    def test_update_add(self, test_event):
        new_update = event.Update("test update")
        test_event += new_update
        assert test_event.feed_text() == ['test update']

        test_event += event.Update()
        assert test_event.feed_text() == ['test update']

        test_event += event.Update("test 2")
        assert test_event.feed_text() == ['test update', 'test 2']
    
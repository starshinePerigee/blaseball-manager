"""Just checking on repeated calls and how the call stack forms"""

from enum import Enum
from blaseball.util.messenger import Messenger


class CallTags(Enum):
    one = 1
    two = 2
    three = 3
    four = 4
    five = 5


m = Messenger()


QUEUE = True


def respond_one():
    print("one")
    if QUEUE:
        m.queue(tags=CallTags.two)
    else:
        m.send(tags=CallTags.two)


def respond_two():
    print("two")
    if QUEUE:
        m.queue(tags=CallTags.three)
    else:
        m.send(tags=CallTags.three)


def respond_three():
    print("three")
    if QUEUE:
        m.queue(tags=CallTags.four)
    else:
        m.send(tags=CallTags.four)


def respond_four():
    print("four")
    if QUEUE:
        m.queue(tags=CallTags.five)
    else:
        m.send(tags=CallTags.five)


def respond_five():
    # at this point we should be ten deep in the stack if we're not using the queue, and two deep if we are.
    print("five")


m.subscribe(respond_one, CallTags.one)
m.subscribe(respond_two, CallTags.two)
m.subscribe(respond_three, CallTags.three)
m.subscribe(respond_four, CallTags.four)
m.subscribe(respond_five, CallTags.five)


if QUEUE:
    m.queue(tags=CallTags.one)
else:
    m.send(tags=CallTags.one)


print("")

"""
Messenger impliments the Observer pattern, to send information between classes.

Some guidelines and caveats:

1. Mssenger is best when:
    a: you don't care if there is a response
        messenger is meant to carry information in a single direction - from a class/module to another one.
        carrying information back couples modules a little too tightly, although you can call messenger again
            DO NOT send a message on a tag that you are responding on - that will recurse!
    b:  you don't care about what the receiver does
        the receiver can error (in which case, it gets caught by messenger and logged, but execution continues)
        the receiver could have been changed since you last wrote the sender
    c: you don't really care about execution order
        there is a priority option to configure messenger order, but because the way the stack works (see the next
        caveat) execution order can get pretty weird!

2. messenger sends broadcast to many targets at once, but it's important not to forget what a broadcast is:
it's a remote function call. This is a way of making one module call functions in none/some/many other modules.

These modules can (and often do!) send their own messages. These messages are propagated and handled from the
point of call. This means they are executed before later listeners up the "messenger stack"!

As an example:

    Alice subscribes Appraise() to Messenger M1 tag new_house
    Bob subscribes Bellow() to M1 tag new_house
    Bob also subscribes Bellow() to M1 tag announce

    if Alice's Appraise() sends a message on the announce tag, then this is the order of execution:

    1. caller sends on new_house
    2.  Appraise() is called from messenger
    3.  Appraise() sends a message on announce
    4.   This calls Bellow()
    5.  Bellow() is called from the new_house tag

this results in Bob bellowing the results of the appraisal before bellowing the new house! this may or may not be
what you want.

"""

from collections import defaultdict
from enum import Enum
import inspect
from loguru import logger

from typing import Callable, Union, List, Type, Optional


class Messenger:
    """A go-between for many-to-many communication between parts of the program.

    Listeners (any section of code) can subscribe to a Messenger, hooking up a function to be called.
    Senders send the message out into the void by calling send,

    This broadcasts once to every subscribed listener with at least one common tag.
    """
    running_id = 1

    def __init__(self):
        """
        Creates an empty messenger. Because most of the configuration occurs on subscribe, an
        empty messenger isn't different from another empty messenger.
        """
        # listeners is a dictionary of list of tuples:
        """
        {
           tag1: [(4, funct1), (1, funct2), (-2, funct3)]
           tag2: [(1, funct2)]
        }
        """
        self.listeners = defaultdict(list)
        self._queue = []
        self._broadcasting = False
        self.id = Messenger.running_id
        Messenger.running_id += 1

    def subscribe(self, function: Callable, tags: Union[Enum, List[Enum]] = "", priority=0) -> None:
        """Subscribe function to tags. Whenever messenger is sent, this function will be called """
        if not isinstance(tags, list):
            tags = [tags]

        for tag in tags:
            if function in [listener[1] for listener in self.listeners[tag]]:
                raise ValueError(f"Function '{function}' already subscribed to tag {tag}!")
            self.listeners[tag] += [(priority, function)]
            self.listeners[tag].sort(key=lambda x: x[0], reverse=True)

    def unsubscribe(self, function: Callable, tags: Union[Enum, List[Enum]] = "") -> None:
        """Unsubscribe the function from the tags."""
        if not isinstance(tags, list):
            tags = [tags]

        for tag in tags:
            for priority_tuple in self.listeners[tag]:
                if priority_tuple[1] == function:
                    self.listeners[tag].remove(priority_tuple)

    def send(self, argument=None, tags: Union[Enum, List[Enum]] = "", queue=False) -> None:
        """Send a message."""
        if queue and self._broadcasting:
            self._queue += [(argument, tags)]
            return

        self._broadcasting = True
        sent = set()

        if tags == "":
            if len(self.listeners) > 1 or "" not in self.listeners:
                raise KeyError(f"Tag required for messenger with tagged subscribers. "
                               f"Received argument: {argument} of type {type(argument)}")

        if not isinstance(tags, list):
            tags = [tags]

        for tag in tags:
            if tag in self.listeners:
                recipients = [priority_tuple[1] for priority_tuple in self.listeners[tag]]
                for recipient in recipients:
                    if recipient not in sent:
                        try:
                            if argument is None:
                                recipient()
                            else:
                                recipient(argument)
                        except Exception as err:
                            # a bare exception is a dangerous thing, but in this case we genuinely
                            # want messenger to be a "firewall"
                            if isinstance(err, BreakerError):
                                raise

                            caller = inspect.stack()[1]  # respond(), messenger.send(), caller
                            logger.exception(f"{type(err).__name__}: {str(err)}. "
                                             f"Exception raised while processing tags '{tag_string(tags)}' "
                                             f"from function {caller.function}")
                        finally:
                            sent.add(recipient)

        self._broadcasting = False
        if len(self._queue) > 0:
            self.send(*self._queue.pop(0))

    def __str__(self):
        total_listeners = sum([len(self.listeners[key]) for key in self.listeners])
        return f"Messenger {self.id} with {len(self.listeners)} tags and {total_listeners} total listeners."

    def __repr__(self):
        return f"<Messenger ID {self.id}>"


def tag_string(tags: List[Optional[Enum]]):
    if tags[0] is None:
        return ""
    else:
        return "+".join([tag.name for tag in tags])


class Listener:
    """An abstract base class for any of several utilities that exist to limpet on to a messenger."""
    def __init__(self, messenger: Messenger, tags: Union[Enum, List[Enum]], priority=0):
        messenger.subscribe(self.respond, tags, priority)

    def respond(self, argument):
        pass


class ReceivedArgument:
    """I can't believe I'm doing this, but it's basically a namedtuple with a str method"""
    def __init__(self, argument=None):
        callers = inspect.stack()[2:4]  # respond(), messenger.send(), caller
        self.argument = argument
        self.tags = callers[0].frame.f_locals['tags']
        self.great_grand_caller = callers[1]

    def __str__(self):
        return f"[{tag_string(self.tags)}] {self.great_grand_caller.function}: {self.argument}"

    def as_padded_string(self):
        return (f"{tag_string(self.tags):30} {self.great_grand_caller.function:20} "
                f"{str(self.argument):80} {type(self.argument)}")

    def __repr__(self):
        return f"ReceivedArgument({self.argument})"


class Printer(Listener):
    """Messenger demo class, helps with debugging a messenger stream."""
    def respond(self, argument):
        print(f"[{type(argument)}] <{argument}>")


class BreakerError(TypeError):
    pass


class CircuitBreaker(Listener):
    def __init__(self, messenger: Messenger, tags: Union[Enum, List[Enum]], types: Union[Type, List[Type]]):
        if not isinstance(types, list):
            types = [types]
        self.types = types
        super().__init__(messenger, tags, 90)

    def respond(self, argument):
        arg_type = type(argument)
        if arg_type not in self.types:
            raise BreakerError(f"Circuitbreaker detected invalid type: {arg_type}, expected {self.types}")


class CountStore(Listener):
    def __init__(self, messenger: Messenger, tags: Union[Enum, List[Enum]] = "", items_to_store=-1):
        """Count the number of items passing through this message with tags, and optionally save them.
        If items_to_store is 0, no items will be saved. if items_to_store is -1, all items will be saved."""
        super().__init__(messenger, tags, 100)
        self.items_to_store = items_to_store
        self.count = 0
        self.items = []

    def respond(self, argument=None):
        self.count += 1
        if self.items_to_store != 0:
            self.items.insert(0, ReceivedArgument(argument))
            if self.items_to_store > 0:
                if len(self.items) > self.items_to_store:
                    del(self.items[-1])

    def tag_inventory(self):
        all_tags = defaultdict(int)
        for item in self.items:
            for tag in item.tags:
                all_tags[tag] += 1
        return all_tags

    def clear(self):
        self.items = []
        self.count = 0

    def __getitem__(self, item):
        return self.items[item].argument

    def __len__(self):
        return len(self.items)

    def print_all(self):
        for i, item in enumerate(self.items[::-1]):
            print(f"{'[' + str(i) + ']':>6} {item.as_padded_string()}")

"""
This is how we're going to pass messages between classes.
"""

from collections import defaultdict
from enum import Enum

from typing import Callable, Union, List, Type


class Messenger:
    """A go-between for many-to-many communication between parts of the program.

    Listeners (any section of code) can subscribe to a Messenger, hooking up a function to be called.
    Senders send the message out into the void by calling send,

    This broadcasts once to every subscribed listener with at least one common tag.
    """
    running_id = 1

    def __init__(self):
        self.listeners = defaultdict(list)
        self.id = Messenger.running_id
        Messenger.running_id += 1

    def subscribe(self, function: Callable, tags: Union[Enum, List[Enum]] = "") -> None:
        """Subscribe function to tags. Whenever messenger is sent, this function will be called """
        if not isinstance(tags, list):
            tags = [tags]

        for tag in tags:
            self.listeners[tag] += [function]

    def unsubscribe(self, function: Callable, tags: Union[Enum, List[Enum]] = "") -> None:
        """Unsubscribe the function from the tags."""
        if not isinstance(tags, list):
            tags = [tags]

        for tag in tags:
            self.listeners[tag].remove(function)

    def send(self, argument=None, tags: Union[Enum, List[Enum]] = "") -> None:
        """Send a message."""
        sent = set()

        if tags == "":
            if len(self.listeners) > 1 or "" not in self.listeners:
                raise KeyError(f"Tag required for messenger with tagged subscribers. "
                               f"Received argument: {argument} of type {type(argument)}")

        if not isinstance(tags, list):
            tags = [tags]

        for tag in tags:
            if tag in self.listeners:
                recipients = self.listeners[tag]
                for recipient in recipients:
                    if recipient not in sent:
                        if argument is None:
                            recipient()
                        else:
                            recipient(argument)
                        sent.add(recipient)

    # TODO: add "send queue" for optional timing management

    def __str__(self):
        total_listeners = sum([len(self.listeners[key]) for key in self.listeners])
        return f"Messenger {self.id} with {len(self.listeners)} tags and {total_listeners} total listeners."

    def __repr__(self):
        return f"<Messenger ID {self.id}>"


class Listener:
    """An abstract base class for any of several utilities that exist to limpet on to a messenger."""
    def __init__(self, messenger: Messenger, tags: Union[Enum, List[Enum]]):
        messenger.subscribe(self.respond, tags)

    def respond(self, argument):
        pass


class Printer(Listener):
    """Messenger demo class, helps with debugging a messenger stream."""
    def respond(self, argument):
        print(f"[{type(argument)}] <{argument}>")


class CircuitBreaker(Listener):
    def __init__(self, messenger: Messenger, tags: Union[Enum, List[Enum]], types:Union[Type, List[Type]]):
        if not isinstance(types, list):
            types = [types]
        self.types = types
        super().__init__(messenger, tags)

    def respond(self, argument):
        arg_type = type(argument)
        if arg_type not in self.types:
            raise TypeError(f"Circuitbreaker detected invalid type: {arg_type}, expected {self.types}")


class CountStore(Listener):
    def __init__(self, messenger: Messenger, tags: Union[Enum, List[Enum]], items_to_store=-1):
        """Count the number of items passing through this message with tags, and optionally save them.
        If items_to_store is 0, no items will be saved. if items_to_store is -1, all items will be saved."""
        super().__init__(messenger, tags)
        self.items_to_store = items_to_store
        self.count = 0
        self.items = []

    def respond(self, argument):
        self.count += 1
        if self.items_to_store != 0:
            self.items.insert(0, argument)
            if self.items_to_store > 0:
                if len(self.items) > self.items_to_store:
                    del(self.items[-1])

    def __getitem__(self, item):
        return self.items[item]

    def __len__(self):
        return len(self.items)
"""
This is how we're going to pass messages between classes.
"""

from typing import Callable, Union, List


"""
how does this work:

something happens in class A
class A calls "notify" with a data object and tags

Messenger iterates through objects subscribed to those tags, calling their registered functions 



sidethought on tags:
tags let multiple receivers listen on a specific tag, and let a source broadcast to many different locations
(without doubling up). the alternative is destination filtering, which is slower?

the problem with tags is it means the actual messenger has to be a global, or tags become a subset?

which might not actually be a problem, if we're disciplined with tags?
this does make threading HELL though. we will eventually want to thread out background games, etc.


so we do need a shared class, which can handle synchronization. make send a module function and we can add
synchronization to it later?

"""

class Messenger:
    """A go-between for many-to-many communication between parts of the program.

    Listeners (any section of code) can subscribe to a Messenger, hooking up a function to be called.
    Senders send the message out into the void by calling send,

    This broadcasts once to every subscribed listener with at least one common tag.
    """

    def __init__(self):
        self.listeners = {}

    def subscribe(self, tags: Union[str, List[str]], function: Callable) -> None:
        if not isinstance(tags, list):
            tags = [tags]

        for tag in tags:
            if tag in self.listeners:
                self.listeners[tag] += [function]
            else:
                self.listeners[tag] = [function]

    def send(self, tags: Union[str, List[str]], argument=None) -> None:
        sent = set()

        if not isinstance(tags, list):
            tags = [tags]

        for tag in tags:
            if tag in self.listeners:
                recipients = self.listeners[tag]
                for recipient in recipients:
                    if recipient not in sent:
                        recipient(argument)
                        sent.add(recipient)


class Sender:
    def __init__(self, name, messenger):
        self.name = name
        self.messenger = messenger

    def say_hi(self):
        print(f"hello from {self.name}")
        self.messenger.send("greeting", self.name)


class Listener:
    def __init__(self, name, messenger):
        self.name = name
        messenger.subscribe('greeting', self.respond)

    def respond(self, other_name):
        print(f"hi {other_name}, this is {self.name}.")


class Bidirectional:
    def __init__(self, name, messenger):
        self.name = name
        self.messenger = messenger
        messenger.subscribe('greeting', self.respond)

    def respond(self, other_name):
        print(f"hi {other_name}, this is {self.name}.")

    def say_hi(self):
        print(f"hello from {self.name}")
        self.messenger.send("greeting", self.name)



m = Messenger()

s_a = Sender("Alice", m)
s_d = Sender("Dave", m)

l_b = Listener("Bob", m)
l_c = Listener("Charlie", m)

s_a.say_hi()
s_d.say_hi()

b_e = Bidirectional("Elise", m)
b_f = Bidirectional("Frank", m)
b_g = Bidirectional("Gilbert", m)

b_g.say_hi()
b_f.say_hi()


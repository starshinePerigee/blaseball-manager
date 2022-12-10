"""
Updates are things that happen during the game. This is generic, but in a nutshell, an event is:
- something that happens
- because of a player, other event, or external factor
- affects the game state
- updates the display
- has text for the event log
- during a game

Think of an event as a single message in a game feed.

An Event is a container for multiple updates. A single pitch+hit+field is an Event, but so are things like incinerations
or game substitutions.

Events are not currently used. # TODO
We will eventually be having a separate listener that bundles together updates into Events and stores them for reference
and use.

"""

from typing import List, Callable, Union, TYPE_CHECKING
if TYPE_CHECKING:
    from blaseball.playball.gamestate import GameState


class Update:
    """An update is a single moment, which updates the game state, draws on the image, or adds text."""
    def __init__(self, text: str = None):
        self.text = text

    def __str__(self):
        if self.text is not None:
            return self.text
        else:
            return "[empty Update]"

    def __repr__(self):
        return f"<Update: {self.text}>"


class Event:
    """An event is a single gameplay step, such as a single pitch + hit, a steal attempt, or an incineration."""

    def __init__(self, name=None):
        self.name = name
        self.updates = []

    def feed_text(self, debug=False) -> List[str]:
        return [__.text for __ in self.updates if __.text is not None]

    def __str__(self):
        name = self.name if self.name is not None else id(self)
        return f"Event {name}"

    def __add__(self, other):
        if isinstance(other, Update):
            self.updates += [other]
        elif isinstance(other, Event):
            self.updates += other.updates
        else:
            raise ValueError(f'Invalid type: {type(other)}')
        return self

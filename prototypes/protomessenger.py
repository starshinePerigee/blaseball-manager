"""
This is how we're going to pass messages between classes.
"""

from typing import Callable


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



"""
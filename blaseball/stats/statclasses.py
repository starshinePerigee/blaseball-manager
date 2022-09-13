"""
This defines classes that manipulate and store stats. stats.py actually defines and contains stats.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from blaseball.stats.players import Player

from collections.abc import Collection
from typing import Union, List



class AllStats(Collection):
    """A singleston class meant to contain all stats and provide convenient indexing methods."""
    def __init__(self):
        self._stats_dict = {}

    def _get_all_with_kind(self, kind: StatKinds):
        return [x for x in self._stats_dict.values() if x.kind == kind]

    def _get_all_with_personality(self, personality: "Stat"):
        return [x for x in self._stats_dict.values() if x.personality == personality]

    def _get_all_with_category(self, category: "Stat"):
        return [x for x in self._stats_dict.values() if x.category == category]

    def _get_all_by_name_partial(self, identifier: str):
        return [self._stats_dict[x] for x in self._stats_dict if identifier in x]

    def __getitem__(self, item: Union['Stat', StatKinds, str]) -> Union['Stat', List]:
        """Get stats that match a criteria.
        Do not use this in core loops, index by dot directly."""
        if isinstance(item, Stat):
            if item.kind is StatKinds.personality:
                return self._get_all_with_personality(item)
            elif item.kind is StatKinds.category:
                return self._get_all_with_category(item)
        elif isinstance(item, StatKinds):
            return self._get_all_with_kind(item)
        else:
            if item in self._stats_dict:
                return self._stats_dict[item]
            else:
                return self._get_all_by_name_partial(item)

    def __setitem__(self, key: str, value: 'Stat'):
        self._stats_dict[key] = value

    def __contains__(self, item):
        if isinstance(item, Stat):
            return item.name in self._stats_dict
        return item in self._stats_dict

    def __iter__(self):
        return iter(self._stats_dict.values())

    def __len__(self):
        return len(self._stats_dict)

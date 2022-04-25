"""
A quick utility to convert stat/rating names into 3 letter strings and back

also does lookups for first three characters, case sensitivity, underscores, etc.

this breaks if you try to add stats anywhere but the stat module.
"""

from blaseball.stats.stats import all_stats

long_to_short = {stat.name: stat.abbreviation for stat in all_stats if stat.abbreviation is not None}
short_to_long = {stat.abbreviation: stat.name for stat in all_stats if stat.abbreviation is not None}


class Shortener:
    def __init__(self):
        self.lookup = long_to_short

        self.first_three = {}
        first_three_cache = []
        self.first_three_exclusion = {}

        for item in self.lookup:
            abbr = item[0:3]
            if abbr in first_three_cache:
                if abbr in self.first_three:
                    # this is the first collision
                    del self.first_three[abbr]
                    self.first_three_exclusion[abbr] = [item]
                else:
                    # we've collided before:
                    self.first_three_exclusion[abbr] = self.first_three_exclusion[abbr] + [item]
            else:
                first_three_cache += [abbr]
                self.first_three[abbr] = item

    def __getitem__(self, item: str) -> str:
        try:
            return self.lookup[item]
        except KeyError:
            pass
        item = item.lower().replace("_", " ")
        if item in self.lookup:
            return self.lookup[item]
        if item[0:3] in self.first_three:
            return self.lookup[self.first_three[item[0:3]]]
        if item[0:3] in self.first_three_exclusion:
            raise KeyError(f"First three characters {item[0:3]} ambiguous to "
                           f"{self.first_three_exclusion[item[0:3]]}")
        raise KeyError(f"Could not locate string '{item}' in shortener!")


short = Shortener()


class Lengthener:
    def __init__(self):
        self.lookup = short_to_long

    def __getitem__(self, item: str) -> str:
        try:
            return self.lookup[item]
        except KeyError:
            pass
        item = item[0:3].upper()
        if item in self.lookup:
            return self.lookup[item]
        if item.lower() in short.first_three:
            return short.first_three[item.lower()]
        raise KeyError(f"Could not locate string '{item}' in lengthener!")


long = Lengthener()


if __name__ == "__main__":
    print(short["batting"])
    print(short["battin"])
    print(short["trick"])
    try:
        print(short["stam"])
    except KeyError:
        print("shortener raises an error if a shortened form is not a 3 letter abbreviation and is also ambiguous")

    print(long["ELE"])
    print(long["TOF"])
    print(long["tri"])
    print(long["sta"])
    print(long["stam"])
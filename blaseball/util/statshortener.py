"""
A quick utility to convert stat/rating names into 3 letter strings and back

also does lookups for first three characters, case sensitivity, underscores, etc.
"""

PAIRS = [
    ("name", "NAME"),
    ("total offense", "TOF"),
    ("total defense", "TDF"),
    ("vibes", "VIB"),
    ("stamina", "STA"),
    ("mood", "MOD"),
    ("soul", "SOL"),
    ("batting", "BAT"),
    ("running", "RUN"),
    ("defense", "DEF"),
    ("pitching", "PCH"),
    ("edge", "EDG"),
    ("vitality", "VIT"),
    ("social", "SOC"),
    ("determination", "DTR"),
    ("enthusiasm", "ENT"),
    ("stability", "STB"),
    ("insight", "INS"),
    ("element", "ELE"),
    ("power", "POW"),
    ("contact", "CON"),
    ("control", "CTR"),
    ("discipline", "DSC"),
    ("speed", "SPD"),
    ("bravery", "BRV"),
    ("timing", "TMG"),
    ("calling", "CAL"),
    ("reach", "RCH"),
    ("reaction", "RCT"),
    ("throwing", "TRW"),
    ("force", "FOR"),
    ("accuracy", "ACC"),
    ("trickery", "TRK"),
    ("awareness", "AWR"),
    ("strategy", "STG"),
    ("leadership", "LED"),
    ("heckling", "HCK"),
    ("cheers", "CHE"),
    ("endurance", "EDR"),
    ("positivity", "POS"),
    ("energy", "ENG"),
    ("recovery", "RCV"),
    ("teaching", "TCH"),
    ("cool", "COO"),
    ("hangouts", "HNG"),
    ("support", "SUP"),
    ("clutch", "CLT"),
    # ("", ""),
]

long_to_short = {pair[0]: pair[1] for pair in PAIRS}
short_to_long = {pair[1]: pair[0] for pair in PAIRS}

# throw error if duplicates exist
if len(long_to_short) != len(PAIRS):
    raise KeyError("Duplicate long name present!")

if len(short_to_long) != len(PAIRS):
    raise KeyError("Duplicate short name present!")


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
            return self.first_three[item[0:3]]
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
            return self.lookup[short.first_three[item.lower()]]
        raise KeyError(f"Could not locate string '{item}' in lengthener!")

long = Lengthener()



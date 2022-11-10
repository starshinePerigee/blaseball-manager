stat_one = 1  # does suggest

stat_dict = {
    "stat_two": 2  # does not suggest
}

stat_dict["stat_three"] = 3  # does not suggest

class StatClass:
    stat_four = 4  # does suggest on both class and instance

    def __init__(self):
        self.stat_five = 5  # does suggest on instance


stat_class = StatClass()

stat_class.stat_six = 6  # does not suggest

stat_seven, stat_eight = (7, 8)  # does suggest

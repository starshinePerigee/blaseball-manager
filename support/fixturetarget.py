from numpy.random import rand


def add_average_1(x):
    return x + rand() * 2


def add_average_2(x):
    return x + rand() * 4


def add_average_3(x):
    return x + rand() * 6


def add_all_average(x):
    return add_average_1(x) + add_average_2(x) + add_average_3(x)


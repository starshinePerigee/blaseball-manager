"""this is a test class for handling mocks"""

from random import random

def just_random() -> float:
    return random()

if __name__ == '__main__':
    print(just_random())
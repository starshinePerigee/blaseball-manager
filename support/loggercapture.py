"""This contains a logger class uesd as a loguru sink so we can test and examine log messages. """

from collections import defaultdict


class LoggerCapture:
    def __init__(self):
        self.log = []
        self.level_inventory = defaultdict(int)

    def receive(self, msg):
        self.log += [msg]
        self.level_inventory[msg.record['level'].name] += 1

    def __getitem__(self, item):
        return self.log[item]

    def __len__(self):
        return len(self.log)

    def __contains__(self, item):
        return any([item in message for message in self.log])
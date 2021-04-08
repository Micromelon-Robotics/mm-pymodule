from ._singleton import Singleton
from enum import Enum

MAX_WARNINGS_PER_CATEGORY = 1


class RangeErrorCategory(Enum):
    SPEED = 1
    SERVO_DEGREES = 2
    DISTANCE = 3
    SECONDS = 4


class Logger(metaclass=Singleton):
    def __init__(self):
        self._rangeErrorCounts = {}
        self.clearRangeErrorCounts()

    def clearRangeErrorCounts(self):
        for name, member in RangeErrorCategory.__members__.items():
            self._rangeErrorCounts[member] = 0

    def displayWarning(self, mesg, category=None):
        if category:
            self._rangeErrorCounts[category] = self._rangeErrorCounts[category] + 1
            count = self._rangeErrorCounts[category]
            if count > MAX_WARNINGS_PER_CATEGORY:
                return
            if count == MAX_WARNINGS_PER_CATEGORY:
                print("Inputs automatically constrained")
        print("Warning: " + str(mesg))

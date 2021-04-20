from enum import Enum
import logging

__all__ = [
    "warnRangeCategory",
    "clearRangeErrorCounts",
    "RangeErrorCategory",
]

MAX_WARNINGS_PER_CATEGORY = 1


class RangeErrorCategory(Enum):
    SPEED = 1
    SERVO_DEGREES = 2
    DISTANCE = 3
    SECONDS = 4


_rangeErrorCounts = {member: 0 for _, member in RangeErrorCategory.__members__.items()}


def getLogger():
    return logging.getLogger("Micromelon")


def clearRangeErrorCounts():
    for name, member in RangeErrorCategory.__members__.items():
        _rangeErrorCounts[member] = 0


def warnRangeCategory(mesg, category: RangeErrorCategory = None):
    logger = getLogger()
    if category:
        _rangeErrorCounts[category] = _rangeErrorCounts[category] + 1
        count = _rangeErrorCounts[category]
        if count > MAX_WARNINGS_PER_CATEGORY:
            return
        if count == MAX_WARNINGS_PER_CATEGORY:
            logger.warning("Inputs automatically constrained")
    logger.warning(str(mesg))

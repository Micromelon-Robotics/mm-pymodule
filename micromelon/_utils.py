from ._mm_logging import RangeErrorCategory, warnRangeCategory
from .helper_math import constrain
from time import sleep

MAX_SPEED = 30
MAX_DISTANCE = 3276.7
MAX_TIME = 120
MAX_SERVO_DEGREES = 90


def delay(seconds) -> None:
    """
    Alias to Python time.sleep(seconds)

    Args:
        seconds (number): see Python time.sleep documentation

    Returns:
        None
    """
    sleep(seconds)


def isNumber(x):
    return isinstance(x, (int, float))

def mathModulo(n, mod):
    return ((n % mod ) + mod ) % mod

def mathModuloDistance(x, y, mod):
    return min(mathModulo(x - y, mod), mathModulo(y - x, mod))

# Speed should be in cm/s with a maximum of 30
def restrictSpeed(speed):
    if not isNumber(speed):
        raise Exception("Speed must be a number")

    if abs(speed) > MAX_SPEED:
        # raise Exception('Speed must be between -30 and 30. You gave ' + speed);
        warnRangeCategory(
            "Speed must be between -{0} and {0}. You gave {1}".format(MAX_SPEED, speed),
            RangeErrorCategory.SPEED,
        )

    return constrain(speed, -MAX_SPEED, MAX_SPEED)


# Distance given in cm returns errors or distance in mm
def restrictDistance(dist):
    if not isNumber(dist):
        raise Exception("Distance must be a number")

    if abs(dist) > MAX_DISTANCE:
        # raise Exception(
        #     `Distance must be between -${MAX_DISTANCE} and ${MAX_DISTANCE}. You gave ${dist}`);
        warnRangeCategory(
            "Distance must be between "
            + "-{0} and {0}. You gave {1}".format(MAX_DISTANCE, dist),
            RangeErrorCategory.DISTANCE,
        )
    return constrain(dist, -MAX_DISTANCE, MAX_DISTANCE) * 10


# Returns time in seconds if it's a valid number
def restrictTime(secs):
    if not isNumber(secs):
        raise Exception("Seconds must be a number")

    if secs < 0:
        raise Exception("Seconds can't be negative.  You gave {}".format(secs))

    if abs(secs) > 120:
        warnRangeCategory(
            "Command would take {} seconds.  Maximum is {}.".format(secs, MAX_TIME),
            RangeErrorCategory.SECONDS,
        )

    return constrain(secs, 0, 120)


# Returns time in seconds if it's a valid number
def restrictRadius(r):
    if not isNumber(r):
        raise Exception("Radius must be a number")

    if r < 0:
        raise Exception("Radius cannot be a negative number. You gave: {}.".format(r))

    return r


def restrictServoDegrees(d):
    if not isNumber(d):
        raise Exception("Degrees must be a number")
    d = round(d)
    if abs(d) > 90:
        warnRangeCategory(
            "Degrees must be between "
            + "-{0} and {0}. You gave {1}".format(MAX_SERVO_DEGREES, d),
            RangeErrorCategory.SERVO_DEGREES,
        )
    return constrain(d, -MAX_SERVO_DEGREES, MAX_SERVO_DEGREES)

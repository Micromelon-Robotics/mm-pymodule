from .._robot_comms import RoverController, MicromelonType as OPTYPE

from .._utils import *

_rc = RoverController()

__all__ = [
    "left",
    "right",
    "setBoth",
    "read",
]


def _setServos(s1, s2):
    """
    Sets both servos to desired degrees
    Degrees must be between -90 and 90
    If an argument is 255 then that servo will be left as is

    Args:
      s1 (int): degrees to set the left servo to
      s2 (int): degrees to set the right servo to
    """
    # Flag to leave a servo as it is is 0xFF (255)
    # so only apply the 90 offset if it's in a range to be set
    if s1 <= 90:
        s1 += 90
    if s2 <= 90:
        s2 += 90
    return _rc.writeAttribute(OPTYPE.SERVO_MOTORS, [s1, s2])


def left(degrees):
    """
    Turns the left servo to the specified number of degrees

    Args:
      degrees (number): must be between -90 and 90 and will be rounded

    Raises:
      Exception if degrees is not a number

    Returns:
      None
    """
    degrees = restrictServoDegrees(degrees)
    return _setServos(degrees, 0xFF)


def right(degrees):
    """
    Turns the right servo to the specified number of degrees

    Args:
      degrees (number): must be between -90 and 90 and will be rounded

    Raises:
      Exception if degrees is not a number

    Returns:
      None
    """
    degrees = restrictServoDegrees(degrees)
    return _setServos(0xFF, degrees)


def setBoth(s1, s2):
    """
    Sets both servo motors to specified number of degrees

    Args:
      s1, s2 (number): degrees for left and right servos respectively
                        must be between -90 and 90 and will be rounded

    Raises:
      Exception if s1 or s2 is not a number

    Returns:
      None
    """
    s1 = restrictServoDegrees(s1)
    s2 = restrictServoDegrees(s2)
    return _setServos(s1, s2)


def read():
    """
    Returns:
      Array of degrees [left, right] that is the current set points of the left and right servos
    """
    degrees = _rc.readAttribute(OPTYPE.SERVO_MOTORS)
    # unsigned read so offset back to -90 to 90 range
    return [degrees[0] - 90, degrees[1] - 90]

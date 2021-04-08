from .._robot_comms import RoverController, MicromelonType as OPTYPE
from .._binary import bytesToIntArray

_rc = RoverController()

__all__ = [
    "readAll",
    "readLeft",
    "readRight",
]


def readAll():
    """
    Read both left and right distance sensors at the same time

    Returns:
      Array of floats [left, right] as distances in cm
    """
    result = _rc.readAttribute(OPTYPE.TIME_OF_FLIGHT)
    mm = bytesToIntArray(result, 2, signed=False)
    return [mm[0] / 10, mm[1] / 10]


def readLeft():
    """
    Read the left IR distance sensor

    Returns:
      Distance in cm as a float from left sensor
    """
    return readAll()[0]


def readRight():
    """
    Read the right IR distance sensor

    Returns:
      Distance in cm as a float from right sensor
    """
    return readAll()[1]

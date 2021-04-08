from .._robot_comms import RoverController, MicromelonType as OPTYPE
from .._binary import bytesToIntArray

_rc = RoverController()

__all__ = [
    "read",
]


def read():
    """
    Returns:
      The number of cm to the nearest object in the ultrasonic sensor's field of view
    """
    reading = _rc.readAttribute(OPTYPE.ULTRASONIC)
    return bytesToIntArray(reading, 2, signed=False)[0]

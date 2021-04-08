from .._robot_comms import RoverController, MicromelonType as OPTYPE
from .._binary import bytesToIntArray

_rc = RoverController()

__all__ = [
    "readVoltage",
    "readPercentage",
    "readCurrent",
]


def readVoltage():
    """
    Reads the voltage of the internal battery

    Returns:
      float value in volts
    """
    milliVolts = _rc.readAttribute(OPTYPE.BATTERY_VOLTAGE)
    milliVolts = bytesToIntArray(milliVolts, 2, False)[0]
    return float(milliVolts) / 1000.0


def readPercentage():
    """
    Reads the state of internal battery charge as a percentage

    Returns:
      integer percentage
    """
    return _rc.readAttribute(OPTYPE.STATE_OF_CHARGE)[0]


def readCurrent():
    """
    Reads the current output of the internal battery in milliamps

    Returns:
      integer value in milliamps
    """
    milliAmps = _rc.readAttribute(OPTYPE.CURRENT_SENSOR)
    return bytesToIntArray(milliAmps, 2)[0]

from .._utils import *
from .._robot_comms import RoverController, MicromelonType as OPTYPE
from .._binary import bytesToIntArray

_rc = RoverController()

__all__ = [
    "readAccel",
    "readGyro",
    "readGyroAccum",
    "isFlipped",
    "isRighted",
]


def _div1000(n):
    return n / 1000


def readAccel(n=None):
    """
    Reads the axes of the accelerometer (in Gs)
    The accelerometer reads the magnitude of acceleration the robot is experiencing in each axis

    Args:
      n (int): must be either 0, 1, 2, or None to read x, y, z, or all axes respectively

    Raises:
      Exception if n is not a valid argument

    Returns:
      Values are float values in units of Gs (9.81m/s^2)
      Returns [x, y, z] iff (if and only if) argument n is None
      Iff n == 0 returns x axis
      Iff n == 1 returns y axis
      Iff n == 2 returns z axis
    """
    if n != None and (not isNumber(n) or n < 0 or n > 2):
        raise Exception("Argument to IMU.readAccel must be a number between 0 and 2")
    accel = _rc.readAttribute(OPTYPE.ACCL)
    accel = bytesToIntArray(accel, 2, signed=True)
    accel = list(map(_div1000, accel))
    if n == None:
        return accel
    return accel[n]


def readGyro(n=None):
    """
    Reads the axes of the gyroscope (in degrees per second)
    The gyroscope reads the rate at which the robot is rotating about each axis

    Args:
      n (int): must be either 0, 1, 2, or None to read x, y, z, or all axes respectively

    Raises:
      Exception if n is not a valid argument

    Returns:
      Values are float values in units of degrees per second
      Returns [x, y, z] iff (if and only if) argument n is None
      Iff n == 0 returns x axis
      Iff n == 1 returns y axis
      Iff n == 2 returns z axis
    """
    if n != None and (not isNumber(n) or n < 0 or n > 2):
        raise Exception("Argument to IMU.readGyro must be a number between 0 and 2")
    gyro = _rc.readAttribute(OPTYPE.GYRO)
    gyro = bytesToIntArray(gyro, 4, signed=True)
    gyro = list(map(_div1000, gyro))
    if n == None:
        return gyro
    return gyro[n]


def readGyroAccum(n=None):
    """
    Reads the accumulated gyroscope readings (in degrees)
    This is an approximation of the number of degrees the
    robot has rotated in each axis since it started

    Args:
      n (int): must be either 0, 1, 2, or None to read x, y, z, or all axes respectively

    Raises:
      Exception if n is not a valid argument

    Returns:
      Values are float values in units of degrees
      Returns [x, y, z] iff (if and only if) argument n is None
      Iff n == 0 returns x axis
      Iff n == 1 returns y axis
      Iff n == 2 returns z axis
    """
    if n != None and (not isNumber(n) or n < 0 or n > 2):
        raise Exception(
            "Argument to IMU.readGyroAccum must be a number between 0 and 2"
        )
    gyro = _rc.readAttribute(OPTYPE.GYRO_ACCUM)
    gyro = bytesToIntArray(gyro, 4, signed=True)
    gyro = list(map(_div1000, gyro))
    if n == None:
        return gyro
    return gyro[n]


def isFlipped():
    """
    Returns:
      True iff (if and only if) the robot is upside down. False otherwise
    """
    return readAccel()[2] < 0


def isRighted():
    """
    Returns:
      True iff (if and only if) the robot is the right way up. False otherwise
    """
    return readAccel()[2] >= 0

import time
import math
from .._robot_comms import (
    RoverController,
    MicromelonType as OPTYPE,
    MicromelonOpCode as OPCODE,
)
from .._utils import *
from .._binary import intArrayToBytes

_rc = RoverController()

__all__ = [
    "write",
    "moveDistance",
    "turn",
    "turnDegrees",
    "setDegreesOffset",
]

_TRACK_LENGTH = 8.5  # cm - axle to axle
_ROBOT_WIDTH = 10.5  # cm - middle of track to middle of track
_AXLE_HYPOTHENUSE = math.sqrt(
    _TRACK_LENGTH * _TRACK_LENGTH + _ROBOT_WIDTH * _ROBOT_WIDTH
)
_SLIP_FACTOR = (_AXLE_HYPOTHENUSE / 2 * _TRACK_LENGTH / _ROBOT_WIDTH) * 0.75

_degreesCalibrationOffset = 0


def write(left, right=None, secs=0):
    """
    Set the speed of the robot motors in cm/s
    If only one argument is given then both motors will be set to the same speed
    If secs is given then the set the motor speeds and block (wait) for that many seconds
    and then stop the motors

    Args:
      left, right (float): motor speeds must be between -30 and 30 (cm/s)
      secs (float): Optional number of seconds to wait for after setting the speeds then stop

    Raises:
      Exception on invalid arguments

    Returns:
      None
    """
    if right == None:
        right = left
    left = restrictSpeed(left)
    right = restrictSpeed(right)
    secs = restrictTime(secs)

    _rc.writeAttribute(OPTYPE.MOTOR_SET, _buildMotorPacketData([left, right]))
    if secs != 0:
        time.sleep(secs)
        _rc.writeAttribute(OPTYPE.MOTOR_SET, _buildMotorPacketData([0, 0]))


def _buildMotorValuesArray(lDist, lSpeed=15, rDist=None, rSpeed=None, syncStop=False):
    if rSpeed == None:
        rSpeed = lSpeed
    lSpeed = restrictSpeed(lSpeed)
    rSpeed = restrictSpeed(rSpeed)

    if rDist == None:
        rDist = lDist
    lDist = restrictDistance(lDist)
    rDist = restrictDistance(rDist)

    if lDist == 0 and rDist == 0:
        write(0)
        return

    if lSpeed < 0:
        lDist *= -1
        lSpeed *= -1

    if rSpeed < 0:
        rDist *= -1
        rSpeed *= -1

    return [lSpeed, rSpeed, lDist, rDist, syncStop]


def moveDistance(lDist, lSpeed=15, rDist=None, rSpeed=None, syncStop=False):
    """
    Drives each side of the robot by the distances and speeds specified.
    If only lDist is specified then both motors will drive that distance at 15cm/s
    If lDist and lSpeed are specified then both motors will drive that distance at that speed
    If syncStop is True then both motors will stop when one completes its operation

    Note that this is a blocking call and won't return until the operation has completed
    Note that operations that will take longer than 2 minutes will time out

    Args:
      lDist (float): distance in cm for left motor
      lSpeed (float): speed in cm/s for left motor (must be between -30 and 30)
      rDist (float): distance in cm for right motor
      lSpeed (float): speed in cm/s for left motor (must be between -30 and 30)
      syncStop (boolean): whether or not to stop both motors as soon as one completes

    Raises:
      Exception on invalid arguments

    Returns:
      None
    """
    motorValues = _buildMotorValuesArray(lDist, lSpeed, rDist, rSpeed, syncStop)
    # Give it two minutes max to complete the operation
    _rc.doMotorOperation(
        OPTYPE.MOTOR_SET, _buildMotorPacketData(motorValues), timeout=120
    )


def turn(speed, secs=None, radius=0, reverse=False):
    """
    Makes the robot turn at the specified speed for the specified number of seconds.
    If seconds is a number > 0 the function will block (wait) until that time has elapsed and stop the motors
    If seconds is None then the speeds will be set and the function will return
    Negative speed is a left turn. Speeds are cm/s must be between -30 and 30.
    By default it turns on the spot, but a radius in cm can be specified.

    Args:
      speed (float): Motor speed to base the turn off.  If turning on the spot this will be actual speed.
                    Will be scaled if radius > 0. Must be between -30 and 30 (cm/s)
      secs (float): Optional number of seconds to leave the motors running at the desired speed before stopping
      radius (float): Optional radius (in cm) to make the turn in
      reverse (boolean): If True then the turn will be done in reverse

    Raises:
      Exception on invalid arguments

    Returns:
      None
    """
    speed = restrictSpeed(speed)
    radius = restrictRadius(radius)

    params = _calcMotorSpeedsAndTime(speed, radius, None, reverse)
    speeds = params["speeds"]

    if secs != None:
        secs = restrictTime(secs)
    else:
        secs = 0
    write(speeds[0], speeds[1], secs)


def turnDegrees(degrees, speed=15, radius=0, reverse=False):
    """
    Makes the robot turn at the specified number of degrees.
    Function will block (wait) until the operation has completed
    Negative speed is a left turn. Speeds are cm/s must be between -30 and 30.
    By default it turns on the spot, but a radius in cm can be specified.

    Note that operations that will take longer than 2 minutes will time out

    Args:
      degrees (float): Number of degrees to turn.  Negative degrees is a left turn
      speed (float): Motor speed to base the turn off.  If turning on the spot this will be actual speed.
                    Will be scaled if radius > 0. Must be between -30 and 30 (cm/s)
      radius (float): Optional radius (in cm) to make the turn in
      reverse (boolean): If True then the turn will be done in reverse

    Raises:
      Exception on invalid arguments

    Returns:
      None
    """
    speed = restrictSpeed(speed)
    radius = restrictRadius(radius)
    if not isNumber(degrees):
        raise Exception("Degrees must be a number")

    if degrees == 0:
        return True

    params = _calcMotorSpeedsAndTime(speed, radius, degrees, reverse)

    motorValues = _buildMotorValuesArray(
        params["distances"][0],
        params["speeds"][0],
        params["distances"][1],
        params["speeds"][1],
        True,
    )

    if _rc.connectedRobotIsSimulated():
        motorValues.append(abs(degrees))
        # Give it two minutes max to complete the operation
        _rc.doMotorOperation(
            OPTYPE.TURN_DEGREES, _buildMotorPacketData(motorValues), timeout=120
        )
        return

    # Fall back to move distance for non-simulated robots
    return moveDistance(
        params["distances"][0],
        params["speeds"][0],
        params["distances"][1],
        params["speeds"][1],
        True,
    )

    # Both the below approaches should work:
    #   Time control prevents error accumulation in the encoders but relies on good latency
    # return moveDistance(params['distances'][0], params['speeds'][0],
    #     params['distances'][1], params['speeds'][1], True)
    # return write(params['speeds'][0], params['speeds'][1], params['seconds'])


def setDegreesOffset(offset):
    """
    Applies offset as a difference to all degrees arguments in the Motor control functions.
    If it is big enough to change the sign of degrees it will not be applied.

    Args:
      offset (float): Number of degrees offset to apply to all motor functions that take degrees
                      as an argument

    Raises:
      Exception if offset is not a number

    Returns:
      None
    """
    if not isNumber(offset):
        raise Exception("Degrees offset must be a number")
    global _degreesCalibrationOffset
    _degreesCalibrationOffset = offset


def _buildMotorPacketData(d):
    if len(d) == 2:
        d = d + [0, 0, 0]
    # Scale speeds to 8 bit

    d[0] = round(d[0] / max(30, abs(d[0])) * 127)
    d[1] = round(d[1] / max(30, abs(d[1])) * 127)

    d[2] = round(d[2])
    d[3] = round(d[3])

    # Allocate lspeed, rspeed, ldist * 2, rdist * 2, syncstop
    data = intArrayToBytes(d[0:2], 1) + intArrayToBytes(d[2:4], 2) + [0]

    if d[4]:  # Write 1 or 0 for syncstop
        data[6] = 1
    else:
        data[6] = 0

    if len(d) == 6:  # Add unsigned degrees info
        data = data + intArrayToBytes([d[5]], 2, False)

    return data


# Speed in cm/s and radius in cm, degrees should not be zero
def _calcMotorSpeedsAndTime(speed, radius, degrees=None, reverse=False):
    lDist = None
    rDist = None
    global _degreesCalibrationOffset
    d = degrees
    if degrees == None:
        d = 90
    else:
        if degrees < 0:
            degrees += -1 * _degreesCalibrationOffset
        else:
            degrees += _degreesCalibrationOffset

        # only apply modified degrees if doesn't cause a sign change
        if not (d < 0 and degrees > 0) and degrees != 0:
            d = degrees

    if speed < 0:
        speed *= -1
        d *= -1

    if d > 0:
        lDist = d * math.pi / 180 * (radius + (_ROBOT_WIDTH / 2) + _SLIP_FACTOR)
        rDist = d * math.pi / 180 * (radius - (_ROBOT_WIDTH / 2) - _SLIP_FACTOR)
    else:
        lDist = (-d) * math.pi / 180 * (radius - (_ROBOT_WIDTH / 2) - _SLIP_FACTOR)
        rDist = (-d) * math.pi / 180 * (radius + (_ROBOT_WIDTH / 2) + _SLIP_FACTOR)

    maxDist = max(abs(lDist), abs(rDist))
    meanDist = (min(abs(lDist), abs(rDist)) + maxDist) / 2

    # Scale so max motor speed will be 30cm/s
    seconds = meanDist / speed
    if maxDist / seconds > 30:
        seconds = maxDist / 30

    lSpeed = lDist / seconds
    rSpeed = rDist / seconds

    # Speed direction has been set according to sign of distance
    # Distance should always be positive
    lDist = abs(lDist)
    rDist = abs(rDist)

    if reverse:
        lSpeed *= -1
        rSpeed *= -1

    # logger.debug('Speeds: ' + str([lSpeed, rSpeed]))
    # logger.debug('Distances: ' + str([lDist, rDist]))
    # logger.debug('Seconds: ' + str(seconds))
    return {
        "speeds": [lSpeed, rSpeed],
        # Don't include distances or time if no degrees was specified
        "distances": [lDist, rDist] if degrees != None else None,
        "seconds": seconds if degrees != None else None,
    }

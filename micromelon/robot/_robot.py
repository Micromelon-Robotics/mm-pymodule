from .._robot_comms import RoverController, MicromelonType as OPTYPE
from .._binary import (
    bytesToAsciiString,
    stringToBytes,
    bytesToIntArray,
    intArrayToBytes,
)
import numpy

_rc = RoverController()

__all__ = [
    "display",
    "setName",
    "getName",
    "getID",
    "getImageCapture",
    "showSensors",
]


def display(text, label=None):
    """
    Puts the given text or the string representation of it on the robot screen
    If a label is provided the screen will show "`label`: `text`"
    The robot screen can display up to 15 characters at a time

    Arguments will be cast to strings

    Args:
      text (any): content to put on the screen
      label (any): optional label to put before the text

    Returns:
      None
    """
    text = str(text)
    if label:
        text = str(label) + ": " + text
    text = text[:15]
    return _rc.writeAttribute(OPTYPE.DISPLAY_TEXT, stringToBytes(text) + [0])


def setName(name):
    """
    Sets the name of the robot.
    This is cleared with a power cycle and displayed on the robot screen during idle times
    Name will be shortened to 11 characters

    Args:
      name (any): Name to set for the robot.  Will be cast to a string

    Returns:
      None
    """
    name = str(name)[:11]
    return _rc.writeAttribute(OPTYPE.ROBOT_NAME, stringToBytes(name) + [0])


def getName():
    """
    Returns:
      The current name of the robot as a string
    """
    name = _rc.readAttribute(OPTYPE.ROBOT_NAME)
    return bytesToAsciiString(name)


def getID():
    """
    Returns:
      The integer id of the robot.
    """
    id = _rc.readAttribute(OPTYPE.BOTID)
    return bytesToIntArray(id, 2, signed=False)[0]


def getImageCapture(width, height):
    """
    When the rover controller is connected in network mode to a micromelon server on a raspberry pi
    this function can be used to capture an image from the raspberry pi camera

    Note is is not recommended to request images larger than 1640x1232 as the pi camera cannot
    use its video port for images larger than that and will take a long time and risk overflowing memory
    The maximum capture resolutions are 2592x1944 and 3280x2464 for V1 and V2 pi cameras.
    You can request images larger than that but they will be captured at that resolution and linearly scaled up.

    Args:
      width (int): pixel width of image to capture
      height (int): pixel height of image to capture

    Raises:
      Exception if the controller is not in network mode

    Returns:
      A numpy array of the image in bgr colour format
    """
    if not _rc._robotCommunicator.isInTcpMode():
        raise Exception("This operation is only valid over the network to a backpack")

    image = _rc.readAttribute(
        OPTYPE.RPI_IMAGE, intArrayToBytes([width, height], 2, False)
    )
    image = numpy.reshape(image, (height, width, 3))
    return image


def showSensors(secs=0):
    """
    Pause the running of your python program and show the Sensors View
    Useful for debugging at a specific point in your code

    Args:
      secs (number): How many seconds to show the sensors popup before continuing
                  If secs <= 0 the sensors view will stay until you close it manually

    Raises:
      Exception if secs is not a number or the function is not available

    Returns:
      None
    """
    raise Exception("This function is only available inside the Micromelon IDE")

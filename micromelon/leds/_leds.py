from .._robot_comms import RoverController, MicromelonType as OPTYPE
from ..colour._colour import _parseColourArg

_rc = RoverController()

__all__ = [
    "write",
    "writeAll",
    "off",
]


def write(id, c):
    """
    Sets the colour of a specific LED

    Args:
      id (int): The LED to set - must be 1, 2, 3, or 4
      c (array): Colour to set it to - must be in the form [r, g, b]
                with r, g, and b values between 0 and 255 inclusive

    Raises:
      Exception on an invalid LED id or colour
    """
    if id < 1 or id > 4:
        raise Exception("LED id must be 1, 2, 3 or 4. You gave " + id)

    rgb = _parseColourArg(c)
    if rgb:
        # The first byte is a bitmask in the least significant bits of which LEDs to set
        # Following 12 bytes are r,g,b for each LED.
        # Values not masked by the first byte are ignored on the robot
        ledArray = [(1 << (id - 1))] + [0, 0, 0] * 4  # set mask and prefill with 0
        offset = ((id - 1) * 3) + 1
        for i in (0, 1, 2):
            # Set the colour for the masked LED
            ledArray[i + offset] = rgb[i]
        _rc.writeAttribute(OPTYPE.RGBS, ledArray)
        return
    else:
        raise Exception(
            "Invalid colour: " + c + ".  Note rgb values should be in range 0-255"
        )


def writeAll(c1, c2=None, c3=None, c4=None):
    """
    Set the colour of all LEDs at once
    If only one argument is given then all LEDs will be set to that colour
    Colours must be in the form [r, g, b] with values between 0 and 255 inclusive

    Args:
      c1 (array): Colour to set LED 1 or all LEDs if no other arguments
      c2 (array): Colour to set LED 2
      c3 (array): Colour to set LED 3
      c4 (array): Colour to set LED 4

    Raises:
      Exception on invalid number of arguments (anything other than 1 or 4)
      Exception if any of the colour arguments are invalid colours
    """
    rgb1 = _parseColourArg(c1)

    if rgb1:
        ledArray = None
        if c2 and c3 and c4:
            rgb2 = _parseColourArg(c2)
            rgb3 = _parseColourArg(c3)
            rgb4 = _parseColourArg(c4)
            ledArray = rgb1 + rgb2 + rgb3 + rgb4
        elif c2 or c3 or c4:
            raise Exception("Incorrect number of colours provided.  Should be 1 or 4")
        else:
            ledArray = rgb1 * 4
        # 0x0F sets the mask for all 4 LEDs to be set ledArray is 12 bytes for 4 sets of r,g,b
        return _rc.writeAttribute(OPTYPE.RGBS, [0x0F] + ledArray)

    raise Exception("Invalid Colour - Should be in the form [r, g, b]")


def off():
    """
    Turns all LEDs off by setting their colour to black ([0, 0, 0])
    """
    _rc.writeAttribute(OPTYPE.RGBS, [0x0F] + [0] * 12)

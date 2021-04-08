import math
import random
from enum import Enum

from .._robot_comms import RoverController, MicromelonType as OPTYPE
from .._binary import bytesToIntArray

_rc = RoverController()

__all__ = [
    "CS",
    "random",
    "randomHue",
    "rgb",
    "pick",
    "hsv",
    "hue",
    "blend",
    "readAllSensors",
    "readSensor",
    "sensorSees",
    "rgbToHsv",
    "hsvToRgb",
    "hexToRgb",
    "rgbToHex",
]


class CS(Enum):
    """
    A collection of attributes that can be read from the colour sensor
    Values correspond to attribute position in the sensor read array

    CS.HUE = 0
    CS.RED = 1
    CS.GREEN = 2
    CS.BLUE = 3
    CS.BRIGHT = 4
    CS.ALL = 5
    """

    HUE = 0
    RED = 1
    GREEN = 2
    BLUE = 3
    BRIGHT = 4
    ALL = 5


def random():
    """
    Generate a random colour in the rgb colour space

    Returns:
      Array of three integers between 0 and 255 in the form [r, g, b]
    """
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return [r, g, b]


def randomHue():
    """
    Generate a random hue colour with full saturation and brightness

    Returns:
      Array of three integers between 0 and 255 in the form [r, g, b]
    """
    return hsvToRgb(random.randint(0, 359), 1, 1)


def rgb(r, g, b):
    """
    Check the values are valid for an rgb colour and return

    Args:
      r (int): red value - must be between 0 and 255 inclusive
      g (int): green value - must be between 0 and 255 inclusive
      b (int): blue value - must be between 0 and 255 inclusive

    Raises:
      Exception if the values aren't all between 0 and 255 inclusive

    Returns:
      Array of three integers between 0 and 255 in the form [r, g, b]
    """
    return _checkRGB(r, g, b)


def pick(r, g, b):
    """
    Alias for Colour.rgb
    """
    return rgb(r, g, b)


def hsv(h, s, v):
    """
    Validates hsv colour and converts to rgb

    Args:
      h (int): hue value - must be between 0 and 360 inclusive
      s (float): saturation value - must be between 0 and 1 inclusive
      v (float): brightness value - must be between 0 and 1 inclusive

    Raises:
      Exception if the values are outside valid ranges for hsv
        Valid range is 0 - 359 inclusive for hue and 0 - 1 inclusive for saturation and value

    Returns:
      Array of three integers between 0 and 255 in the form [r, g, b] that is equivalent to the hsv arguments
    """
    c = _checkHSV(h, s, v)
    return hsvToRgb(c[0], c[1], c[2])


def hue(hue):
    """
    Validates and calculates rgb colour with full saturation and brightness for the given hue

    Args:
      hue (int): hue value - must be between 0 and 360 inclusive

    Raises:
      Exception if the hue is outside the valid range of 0 - 360 inclusive

    Returns:
      Array of three integers between 0 and 255 in the form [r, g, b]
        that is equivalent to the hsv(hue, 1, 1)
    """
    return hsv(hue, 1, 1)


def blend(c1, c2, ratio, isHSV=False):
    """
    Combine the colours c1 and c2 with the given ratio in the rgb space
    Colour arguments are treated as rgb arrays by default but can be treated as hsv by setting the flag

    Args:
      c1 (array): colour array of [r, g, b] or [h, s, v]
      c2 (array): colour array of [r, g, b] or [h, s, v]
      ratio (float): blend ratio - 0 results in all c1, 1 in all c2
      isHSV (boolean): if true c1 and c2 are treated as hsv arrays

    Raises:
      Exception if the blend ratio is not between 0 and 1 inclusive
      Exception if the colours are not valid (0-255 for r, g, and b values, 0-360 for h, 0-1 for s and v)

    Returns:
      Colour array [r, g, b] of c1 and c2 combined with the given ratio
    """
    if ratio > 1 or ratio < 0:
        raise Exception("Blend ratio must be between 0 and 1")
    if isHSV:
        c1 = hsv(c1[0], c1[1], c1[2])
        c2 = hsv(c2[0], c2[1], c2[2])

    checked = _checkRGB(c1[0], c1[1], c1[2])
    if checked[0] == False:
        return checked

    checked = _checkRGB(c2[0], c2[1], c2[2])
    if checked[0] == False:
        return checked

    r = round(c1[0] * (1 - ratio) + c2[0] * ratio)
    g = round(c1[1] * (1 - ratio) + c2[1] * ratio)
    b = round(c1[2] * (1 - ratio) + c2[2] * ratio)
    return [r, g, b]


def readAllSensors(option=CS.ALL):
    """
    Reads values from the three colour sensors.
    You'll need to calibrate with these values for your situation

    Args:
      option (int): one of CS.HUE, CS.RED, CS.GREEN, CS.BLUE, CS.BRIGHT, and CS.ALL
                defaults to CS.ALL

    Raises:
      Exception if the colour sensor read fails
      Exception if the option argument isn't valid

    Returns:
      Array of sensor readings in the form [left, middle, right]
        CS.RED, CS.GREEN, CS.BLUE, and CS.BRIGHT options give integer readings between 0 and 255 inclusive
        CS.HUE gives integer readings between 0 and 360 inclusive
        CS.ALL gives an array of all readings in the form [HUE, RED, GREEN, BLUE, BRIGHT]
    """
    if isinstance(option, CS):
        option = option.value
    if option < 0 or option > 5:
        raise Exception("Invalid Colour Sensor read option")

    reading = _readRawColourFromRobot()
    if not reading:
        raise Exception("Colour sensor read failed")

    if option == CS.ALL.value:
        return reading

    return [reading[0][option], reading[1][option], reading[2][option]]


def readSensor(option=CS.HUE, sensor=1):
    """
    Reads a value from one of the colour sensors.
    You'll need to calibrate with these values for your situation

    Args:
      option (int): one of CS.HUE, CS.RED, CS.GREEN, CS.BLUE, CS.BRIGHT, and CS.ALL
                defaults to CS.HUE
      sensor (int): 0, 1, or 2 for left, middle, and right sensors

    Raises:
      Exception if the colour sensor read fails
      Exception if the option or sensor arguments aren't valid

    Returns:
      Either integer or array depending on option
        CS.RED, CS.GREEN, CS.BLUE, and CS.BRIGHT options give integer readings between 0 and 255 inclusive
        CS.HUE gives integer readings between 0 and 360 inclusive
        CS.ALL gives an array of all readings in the form [HUE, RED, GREEN, BLUE, BRIGHT]
    """
    if sensor < 0 or sensor > 2:
        raise Exception("Argument for sensor must be 0, 1, or 2")

    reading = readAllSensors(option)
    return reading[sensor]


def sensorSees(option, sensor=None):
    """
    Determines whether or not there is red, green, blue, or white
    visible to the colour sensors

    Args:
      option (int): one of CS.RED, CS.GREEN, CS.BLUE, or CS.BRIGHT
      sensor (int): 0, 1, 2, or None for left, middle, right, or combined sensor readings
                    defaults to None - if two or more sensors see the colour then return true

    Raises:
      Exception for invalid option or sensor arguments
      Exception if the colour sensor read fails

    Returns:
      For RED, GREEN, and BLUE options it will return True if the specific option is
        above a minimum (30) and the hue is within a range
        >330 or <20 for RED, between 85 and 160 for GREEN, and between 190 and 63 for BLUE
      For WHITE (CS.BRIGHT) - True if the sensor reads brightness above 130 and all the colours
        read within 50 of the average colour reading
    """
    if isinstance(option, CS):
        option = option.value
    if sensor != None and (sensor < 0 or sensor > 2):
        raise Exception("Argument for sensor must be 0, 1, or 2")

    if option < 1 or option > 4:
        raise Exception("Invalid sensorSees colour option")

    def colourIs(readValue, option):
        WHITE_DEVIATION_THRESHOLD = 50
        BRIGHTNESS_THRESHOLD = 130
        UPPER_BRIGHTNESS_THRESHOLD = 180
        MINIMUM_COLOUR_VALUE = 30

        h = readValue[CS.HUE.value]
        r = readValue[CS.RED.value]
        g = readValue[CS.GREEN.value]
        b = readValue[CS.BLUE.value]
        w = readValue[CS.BRIGHT.value]

        if option == CS.BRIGHT.value:
            average = (r + g + b) / 3
            if w > BRIGHTNESS_THRESHOLD:
                if (
                    abs(r - average) < WHITE_DEVIATION_THRESHOLD
                    and abs(g - average) < WHITE_DEVIATION_THRESHOLD
                    and abs(b - average) < WHITE_DEVIATION_THRESHOLD
                ):
                    return True
            return False
        if w > UPPER_BRIGHTNESS_THRESHOLD:
            return False  # Too white to be a colour

        if option == CS.RED.value:
            # return (r > b and r > g and r > MINIMUM_COLOUR_VALUE)
            return r > MINIMUM_COLOUR_VALUE and (h < 20 or h > 330)

        if option == CS.GREEN.value:
            # return (g > r and g > b and g > MINIMUM_COLOUR_VALUE)
            return g > MINIMUM_COLOUR_VALUE and (h > 85 and h < 160)

        if option == CS.BLUE.value:
            # return (b > r and b > g and b > MINIMUM_COLOUR_VALUE)
            return b > MINIMUM_COLOUR_VALUE and (h > 190 and h < 263)
        return False

    reading = readAllSensors()
    if sensor == None:
        # voting majority wins
        score = 0
        if colourIs(reading[0], option):
            score += 1
        if colourIs(reading[1], option):
            score += 1
        if colourIs(reading[2], option):
            score += 1
        return score >= 2
    return colourIs(reading[sensor], option)


def rgbToHsv(r, g, b):
    """
    Converts an RGB color value to HSV. Conversion formula
    adapted from http://en.wikipedia.org/wiki/HSV_color_space.

    Args:
      r, g, b (int): red, green, and blue values between 0 and 255 inclusive

    Returns:
      Array [hue, saturation, value]
        hue between 0 and 360 inclusive, s and v between 0 and 1 inclusive
    """
    r /= 255.0
    g /= 255.0
    b /= 255.0

    mx = max(r, g, b)
    mn = min(r, g, b)
    v = mx
    d = mx - mn
    s = 0 if mx == 0 else d / mx
    h = None

    if mx == mn:
        h = 0
        # achromatic
        return [h, s, v]

    if r == mx:
        h = (60 * ((g - b) / d) + 360) % 360
    if g == mx:
        h = (60 * ((b - r) / d) + 120) % 360
    if b == mx:
        h = (60 * ((r - g) / d) + 240) % 360

    return [round(h) % 360, s, v]


def hsvToRgb(h, s, v):
    """
    Converts an HSV color value to RGB. Conversion formula
    adapted from http://en.wikipedia.org/wiki/HSV_color_space.
    Args:
      h (int): hue value between 0 and 360
      s (float): saturation between 0 and 1
      v (float): brightness (value) between 0 and 1

    Returns:
      Array [red, green, blue]
        red, green, and blue values between 0 and 255 inclusive
        hue between 0 and 360 inclusive, s and v between 0 and 1 inclusive
    """
    r = None
    g = None
    b = None

    h60 = h / 60.0
    h60f = math.floor(h60)
    hi = int(h60f) % 6
    f = h60 - h60f
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    r, g, b = 0, 0, 0
    if hi == 0:
        r, g, b = v, t, p
    elif hi == 1:
        r, g, b = q, v, p
    elif hi == 2:
        r, g, b = p, v, t
    elif hi == 3:
        r, g, b = p, q, v
    elif hi == 4:
        r, g, b = t, p, v
    elif hi == 5:
        r, g, b = v, p, q
    r, g, b = round(r * 255), round(g * 255), round(b * 255)
    return [r, g, b]


def hexToRgb(hex):
    """
    Converts hex colour codes eg. #FFF or #00FF0F to rgb array

    Args:
      hex (string): colour code # followed by 3 or 6 hexadecimal digits

    Returns:
      Array [r, g, b] each in the range of 0 - 255 inclusive
    """
    # strip '#'
    if hex[0] == "#":
        hex = hex[1:]
    if len(hex) == 3:
        # Expand shorthand form (e.g. "03F") to full form (e.g. "0033FF")
        return [int(hex[i] * 2, 16) for i in (0, 1, 2)]
    return [int(hex[i : i + 2], 16) for i in (0, 2, 4)]


def rgbToHex(r, g, b):
    """
    Converts r, g, b colour to hex colour codes

    Args:
      r, g, b (int): red, green, and blue values between 0 and 255 inclusive

    Returns:
      hexadecimal string beginning with '#' eg. #00FF0F
    """
    return "#{0:02x}{1:02x}{2:02x}".format(r, g, b)


###############################################################################
###############################################################################
# Helper functions
###############################################################################
###############################################################################


def _parseColourArg(c):
    if not c:
        return None
    rgb = None
    if type(c) is str:
        rgb = hexToRgb(c)
        if rgb:
            return rgb
    elif type(c) is list:
        if len(c) == 3 and _checkRGB(c[0], c[1], c[2]):
            return c
            # return c.map(x => Math.min(Math.max(0, x), 255));
    return None


# Convert colour sensor reading into array of three [h, r, g, b, w] readings
def _readRawColourFromRobot():
    raw = _rc.readAttribute(OPTYPE.COLOUR_ALL)
    raw = bytesToIntArray(raw, 2, signed=False)
    if raw == None:
        return None
    parsed = []
    if len(raw) == 3:
        parsed.append([raw[0]] + hsvToRgb(raw[0], 1, 1) + [128])
        parsed.append([raw[1]] + hsvToRgb(raw[1], 1, 1) + [128])
        parsed.append([raw[2]] + hsvToRgb(raw[2], 1, 1) + [128])
        return parsed

    for i in range(len(raw)):
        if len(raw) == 15 and (i == 4 or i == 9 or i == 14):
            continue  # Hue comes back normal
        # Scaling for sensor on 10 integration cycles and max count of 1024
        raw[i] = (raw[i] / 10240) * 255
        raw[i] = round(raw[i] * 100) / 100

    if len(raw) == 12:
        parsed.append([rgbToHsv(raw[8], raw[9], raw[10])[0]] + raw[8:])
        parsed.append([rgbToHsv(raw[4], raw[5], raw[6])[0]] + raw[4:8])
        parsed.append([rgbToHsv(raw[0], raw[1], raw[2])[0]] + raw[:4])
    elif len(raw) == 15:
        parsed.append([raw[14]] + raw[10:14])
        parsed.append([raw[9]] + raw[5:9])
        parsed.append([raw[4]] + raw[:4])
    else:
        return None  # Unknown length

    # cap non-hue readings to between 0 and 255
    for s in range(3):
        for v in range(1, 5):
            if parsed[s][v] > 255:
                parsed[s][v] = 255
            elif parsed[s][v] < 0:
                parsed[s][v] = 0

    return parsed


def _checkRGB(r, g, b):
    if r < 0 or g < 0 or b < 0 or r > 255 or g > 255 or b > 255:
        raise Exception(
            "Invalid RGB colour: r, g, and b should all be between 0 and 255"
        )
    return [r, g, b]


def _checkHSV(h, s, v):
    if h < 0 or s < 0 or v < 0 or h > 360 or s > 1 or v > 1:
        raise Exception(
            "Invalid HSV colour: Hue must be between 0 and 360\n"
            + "\t\t s and v must be between 0 and 1"
        )
    return [h, s, v]

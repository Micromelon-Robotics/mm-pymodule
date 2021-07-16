import math
import random as _rand
from enum import Enum

from .._robot_comms import RoverController, MicromelonType as OPTYPE
from .._binary import bytesToIntArray
from ..helper_math import constrain, scale
from .._utils import mathModuloDistance, isNumber

_rc = RoverController()

__all__ = [
    "CS",
    "COLOURS",
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

class COLOURS(Enum):
    """
    A collection of predefined colour names mapped to an RGB array
    """

    WHITE = [255, 255, 255]
    GREY = [128, 128, 128]
    BLACK = [0, 0, 0]
    LAVENDER = [220, 190, 255]
    MAGENTA = [240, 50, 230]
    PURPLE = [163, 53, 232]
    CYAN = [70, 240, 240]
    BLUE = [0, 128, 255]
    NAVY = [0, 0, 128]
    MINT = [170, 255, 195]
    GREEN = [0, 255, 0]
    TEAL = [0, 128, 128]
    LIME = [210, 245, 60]
    YELLOW = [255, 255, 0]
    OLIVE = [128, 128, 0]
    APRICOT = [255, 215, 180]
    ORANGE = [255, 128, 0]
    BROWN = [170, 110, 40]
    PINK = [250, 190, 212]
    RED = [255, 0, 34]
    MAROON = [128, 0, 0]


def random():
    """
    Generate a random colour in the rgb colour space

    Returns:
      Array of three integers between 0 and 255 in the form [r, g, b]
    """
    r = _rand.randint(0, 255)
    g = _rand.randint(0, 255)
    b = _rand.randint(0, 255)
    return [r, g, b]


def randomHue():
    """
    Generate a random hue colour with full saturation and brightness

    Returns:
      Array of three integers between 0 and 255 in the form [r, g, b]
    """
    return hsvToRgb(_rand.randint(0, 359), 1, 1)


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
    c = [r, g, b]
    _checkRGB(c)
    return c


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

    _checkRGB(c1)
    _checkRGB(c2)

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


def sensorSees(rgb, sensor=1, tolerance=20):
    """
    Determines whether or not the specified sensor sees the colour within the tolerance

    Args:
      rgb (array): [r, g, b] - An rgb colour in the form of an array [r, g, b] 
                    with each value between 0 and 255 inclusive or a COLOURS enum element
      sensor (int): 0, 1, or 2 for left, middle, right. Defaults to middle
      tolerance (int): How close the colour needs to be to what the sensor detects.
                    If the detected colour hue is within the tolerance and the saturations
                    are within 0.65 then it will return true.
                    For shades (saturation < 0.04 or brightness < 25) the brightness is compared
                    and if they are within a scaled brightness range it will return true.
                    Must be between 0 and 255

    Raises:
      Exception for invalid arguments
      Exception if the colour sensor read fails

    Returns:
      True if the colour matches what the sensor detects within the tolerance range.
      False otherwise
    """
    if sensor not in [0, 1, 2]:
        raise Exception("Argument for sensor must be 0, 1, or 2")
    if isNumber(tolerance) and (tolerance < 0 or tolerance > 255):
        raise Exception("Tolerance must be a number between 0 and 255")
    if isinstance(rgb, COLOURS):
        rgb = rgb.value
    _checkRGB(rgb)

    def colourDetected(sensorRawReading, rgbColour, tolerance):
        sh = sensorRawReading[CS.HUE.value]
        sr = sensorRawReading[CS.RED.value]
        sg = sensorRawReading[CS.GREEN.value]
        sb = sensorRawReading[CS.BLUE.value]
        sw = sensorRawReading[CS.BRIGHT.value]
        hsvReading = rgbToHsv(sr, sg, sb)
        sSat = hsvReading[1]
        
        cr = rgbColour[0]
        cg = rgbColour[1]
        cb = rgbColour[2]
        hsvColour = rgbToHsv(cr, cg, cb)
        ch = hsvColour[0]
        cSat = hsvColour[1]
        cBright = hsvColour[2] * 255
        
        # Need a bit more tolerance around white than black
        rangeScaledWithBrightness = constrain(
            tolerance * scale(cBright, 0, 255, 1.5, 3), 0, 255)
            
        if cBright < 25 or cSat < 0.04:
            # Looking for a shade or close enough
            brightnessMatch = abs(sw - cBright) < rangeScaledWithBrightness
            saturationOrBrightnessLowEnough = sSat < 0.3 or sw < 32
            return saturationOrBrightnessLowEnough and brightnessMatch
        
        # No useful brightness to see a colour
        if sw <= 32:
            return False
        # No useful saturation to see a colour
        if sSat < 0.04:
            return False
        
        hueMatch = mathModuloDistance(ch, sh, 360) < tolerance
        # Be very generous on saturation match
        saturationMatch = abs(sSat - cSat) < 0.65
        return hueMatch and saturationMatch

    reading = readAllSensors()
    return colourDetected(reading[sensor], rgb, tolerance)


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
        if len(c) == 3:
            _checkRGB(c)
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


def _checkRGB(rgb):
    errorStr = "Invalid RGB colour: r, g, and b must all be included and be between 0 and 255"
    if not rgb or len(rgb) != 3:
        raise Exception(errorStr)
    
    r = rgb[0]
    g = rgb[1]
    b = rgb[2]
    if r < 0 or g < 0 or b < 0 or r > 255 or g > 255 or b > 255:
        raise Exception(errorStr)


def _checkHSV(h, s, v):
    if h < 0 or s < 0 or v < 0 or h > 360 or s > 1 or v > 1:
        raise Exception(
            "Invalid HSV colour: Hue must be between 0 and 360\n"
            + "\t\t s and v must be between 0 and 1"
        )
    return [h, s, v]

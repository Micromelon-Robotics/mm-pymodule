"""
Collection of functions for manipulating colour representations.
Includes functions for reading from the robot's colour sensors.
"""
from ._colour import *

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

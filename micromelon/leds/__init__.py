"""
Functions for controlling the RGB LEDs on the corners of the robot
  Top and bottom LEDs are coupled so you can only control 4
  Bottom LEDs mirror the setting of top LEDs
"""
from ._leds import *

__all__ = [
    "write",
    "writeAll",
    "off",
]

"""
Collection of functions to set and get robot attributes and use the onboard screen

If using these functions over the network to a Micromelon server, image capture is available
"""
from ._robot import *

__all__ = [
    "display",
    "setName",
    "getName",
    "getID",
    "getImageCapture",
    "showSensors",
]

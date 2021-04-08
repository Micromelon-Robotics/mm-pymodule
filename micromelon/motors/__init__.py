"""
Collection of functions to control the movement of the robot
"""
from ._motors import *

__all__ = [
    "write",
    "moveDistance",
    "turn",
    "turnDegrees",
    "setDegreesOffset",
]

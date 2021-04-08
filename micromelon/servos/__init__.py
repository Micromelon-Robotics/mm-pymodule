"""
Collection of functions for controlling servo motors connected to
the three pin headers on the back of the robot.
"""
from ._servos import *

__all__ = [
    "left",
    "right",
    "setBoth",
    "read",
]

"""
Functions for reading from the robot's IR time of flight distance sensors.
These sensors read the distance in cm to the nearest object on each side of the robot.
They look out the sides from between the gap in the tracks.
"""
from ._ir import *

__all__ = [
    "readAll",
    "readLeft",
    "readRight",
]

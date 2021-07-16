"""
Python module for connecting to and interacting with the Micromelon Rover
and simulated rovers in the Micromelon Robot Simulator.

Submodules can be accessed with either lower-case or upper case notation.
"""

from ._robot_comms import RoverController
from . import battery as Battery
from . import colour as Colour
from . import i2c as I2C
from . import imu as IMU
from . import ir as IR
from . import leds as LEDs
from . import motors as Motors
from . import robot as Robot
from . import servos as Servos
from . import sounds as Sounds
from . import ultrasonic as Ultrasonic
from .helper_math import _math as Math
from ._utils import delay

CS = Colour.CS
COLOURS = Colour.COLOURS
NOTES = Sounds.NOTES
TUNES = Sounds.TUNES

__all__ = [
    "RoverController",
    "Motors",
    "Ultrasonic",
    "IMU",
    "IR",
    "Battery",
    "Math",
    "Robot",
    "Sounds",
    "NOTES",
    "TUNES",
    "LEDs",
    "Colour",
    "CS",
    "COLOURS",
    "Servos",
    "I2C",
    "delay",
]

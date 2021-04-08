"""
Functions for communicating with I2C devices connected to the expansion header
If the rover controller is in uart operation then these functions are not available
"""
from ._i2c import *

__all__ = [
    "read",
    "write",
    "scan",
]

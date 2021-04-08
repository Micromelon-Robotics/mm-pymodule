"""
Functions to control the onboard buzzer to play tunes or specific frequencies.
Also helpful definitions for musical notes to their frequency and aliases for different preprogrammed tunes.
"""
from ._sounds import *
from ._notes import *

__all__ = ["playNote", "play", "off", "NOTES", "TUNES"]

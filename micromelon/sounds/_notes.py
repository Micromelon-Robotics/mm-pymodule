from enum import Enum

__all__ = [
    "NOTES",
    "TUNES",
]

_NOTE_FREQUENCIES = [
    16.35,
    17.32,
    18.35,
    19.45,
    20.6,
    21.83,
    23.12,
    24.5,
    25.96,
    27.5,
    29.14,
    30.87,
    32.7,
    34.65,
    36.71,
    38.89,
    41.2,
    43.65,
    46.25,
    49,
    51.91,
    55,
    58.27,
    61.74,
    65.41,
    69.3,
    73.42,
    77.78,
    82.41,
    87.31,
    92.5,
    98,
    103.83,
    110,
    116.54,
    123.47,
    130.81,
    138.59,
    146.83,
    155.56,
    164.81,
    174.61,
    185,
    196,
    207.65,
    220,
    233.08,
    246.94,
    261.63,
    277.18,
    293.66,
    311.13,
    329.63,
    349.23,
    369.99,
    392,
    415.3,
    440,
    466.16,
    493.88,
    523.25,
    554.37,
    587.33,
    622.25,
    659.25,
    698.46,
    739.99,
    783.99,
    830.61,
    880,
    932.33,
    987.77,
    1046.5,
    1108.73,
    1174.66,
    1244.51,
    1318.51,
    1396.91,
    1479.98,
    1567.98,
    1661.22,
    1760,
    1864.66,
    1975.53,
    2093,
    2217.46,
    2349.32,
    2489.02,
    2637.02,
    2793.83,
    2959.96,
    3135.96,
    3322.44,
    3520,
    3729.31,
    3951.07,
    4186.01,
    4434.92,
    4698.63,
    4978.03,
    5274.04,
    5587.65,
    5919.91,
    6271.93,
    6644.88,
    7040,
    7458.62,
    7902.13,
]

_NOTE_STRINGS = [
    "C",
    "CsDb",
    "D",
    "DsEb",
    "E",
    "F",
    "FsGb",
    "G",
    "GsAb",
    "A",
    "AsBb",
    "B",
]

_NOTES_DICT = {}

for i in range(int(len(_NOTE_FREQUENCIES) / 12)):
    for j in range(12):
        _NOTES_DICT[_NOTE_STRINGS[j] + str(i)] = _NOTE_FREQUENCIES[i * 12 + j]

NOTES = Enum("NOTES", _NOTES_DICT)
NOTES.__doc__ = """
    A collection of standard musical note frequencies
    As '#' is not valid in a variable name 's' is used instead
    Example: F sharp in the 6th octave would be NOTES.Fs6
              B flat in the 4th octave would be NOTES.Bb4
"""


class TUNES(Enum):
    """
    A collection of pre-programmed tunes the robot can play

    TUNES.UP = 1
    TUNES.DOWN = 2
    """

    UP = 1
    DOWN = 2

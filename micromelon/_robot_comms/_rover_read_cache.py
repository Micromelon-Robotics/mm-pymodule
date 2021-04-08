from enum import Enum
import time
from ._comms_constants import MicromelonType as OPTYPE


class BUFFER_POSITIONS(Enum):
    ULTRASONIC = 0
    ACCL = 2
    GYRO = 8
    COLOUR_ALL = 20
    TIME_OF_FLIGHT = 50
    BATTERY_VOLTAGE = 54
    BATTERY_PERCENTAGE = 56
    PERCENTAGE_PADDING = 57
    BATTERY_CURRENT = 58
    GYRO_ACCUM = 60


class BUFFER_SIZES(Enum):
    ULTRASONIC = 2
    ACCL = 6
    GYRO = 12
    COLOUR_ALL = 30
    TIME_OF_FLIGHT = 4
    BATTERY_VOLTAGE = 2
    BATTERY_PERCENTAGE = 1
    PERCENTAGE_PADDING = 1
    BATTERY_CURRENT = 2
    GYRO_ACCUM = 12


class RoverReadCache:
    def __init__(self) -> None:
        self._allSensors = None
        self._lastUpdatedTime = 0
        self._useByInterval = (
            0.25  # cached values older than 0.25 seconds will be ignored
        )
        self._startAndSizeIndexForOpType = {
            OPTYPE.ULTRASONIC.value: (
                BUFFER_POSITIONS.ULTRASONIC.value,
                BUFFER_SIZES.ULTRASONIC.value,
            ),
            OPTYPE.ACCL.value: (BUFFER_POSITIONS.ACCL.value, BUFFER_SIZES.ACCL.value),
            OPTYPE.GYRO.value: (BUFFER_POSITIONS.GYRO.value, BUFFER_SIZES.GYRO.value),
            OPTYPE.COLOUR_ALL.value: (
                BUFFER_POSITIONS.COLOUR_ALL.value,
                BUFFER_SIZES.COLOUR_ALL.value,
            ),
            OPTYPE.TIME_OF_FLIGHT.value: (
                BUFFER_POSITIONS.TIME_OF_FLIGHT.value,
                BUFFER_SIZES.TIME_OF_FLIGHT.value,
            ),
            OPTYPE.BATTERY_VOLTAGE.value: (
                BUFFER_POSITIONS.BATTERY_VOLTAGE.value,
                BUFFER_SIZES.BATTERY_VOLTAGE.value,
            ),
            OPTYPE.STATE_OF_CHARGE.value: (
                BUFFER_POSITIONS.BATTERY_PERCENTAGE.value,
                BUFFER_SIZES.BATTERY_PERCENTAGE.value,
            ),
            OPTYPE.CURRENT_SENSOR.value: (
                BUFFER_POSITIONS.BATTERY_CURRENT.value,
                BUFFER_SIZES.BATTERY_CURRENT.value,
            ),
            OPTYPE.GYRO_ACCUM.value: (
                BUFFER_POSITIONS.GYRO_ACCUM.value,
                BUFFER_SIZES.GYRO_ACCUM.value,
            ),
        }

    def updateAllSensors(self, data):
        self._allSensors = data
        self._lastUpdatedTime = time.time()

    def setUseByInterval(self, seconds):
        if seconds <= 0:
            raise Exception(
                "Use by interval for RoverReadCache must be a positive non-zero number"
            )
        self._useByInterval = seconds

    def invalidateCache(self):
        self._allSensors = None

    def readCache(self, opType):
        if (
            not self._allSensors
            or time.time() - self._lastUpdatedTime > self._useByInterval
        ):
            return None
        if isinstance(opType, Enum):
            opType = opType.value

        if opType in self._startAndSizeIndexForOpType:
            indices = self._startAndSizeIndexForOpType[opType]
            return self._allSensors[indices[0] : indices[0] + indices[1]]
        return None

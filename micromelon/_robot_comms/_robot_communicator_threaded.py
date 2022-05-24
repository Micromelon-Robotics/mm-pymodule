import threading
import queue
from enum import Enum
import asyncio
import time
from .._mm_logging import getLogger

from ._thread_command import ThreadCommand
from .uart import UartController
from ._comms_constants import (
    MicromelonOpCode as OPCODE,
    MicromelonType as OPTYPE,
    CONNECTION_STATUS,
    DEFAULT_SPAM_INTERVAL_MS,
    MIN_SPAM_INTERVAL_MS,
)
from ._rover_read_cache import RoverReadCache
from .._binary import intArrayToBytes
from ._moving_average import MovingAverage
from .transports import (
    RobotTransportBase,
    RobotTransportBLE,
    RobotTransportSerial,
    RobotTransportTCP,
)

logger = getLogger()


class RobotCommunicatorThread(threading.Thread):
    def __init__(self) -> None:
        super().__init__()

        self.daemon = True
        self._commandQueue = None
        self._eventQueue = None
        self._loop = None
        self._uart = None
        self._connection = None
        self._readCache = RoverReadCache()
        self._currentRequestedUpdateInterval = None
        self._sensorSpamActive = False
        self._threadReady = threading.Event()

        self._TIMING_WINDOW_SIZE = 20
        self._transactionTimings = MovingAverage(self._TIMING_WINDOW_SIZE)

        self._motorsNotificationWatchers = queue.Queue()

        self._connection: RobotTransportBase = None
        self._connectionStatus = CONNECTION_STATUS.NOT_CONNECTED

    def _connectionStatusCallback(self, newStatus):
        self._connectionStatus = newStatus

    def _processIncomingPacket(self, packet):
        self.queueEvent(self._uart.processIncomingPacket, packet)

    def _buttonPressCallback(self, buttonCode):
        logger.info("Button pressed - code: " + str(buttonCode))

    def _sensorErrorMaskCallback(self, errorMask):
        logger.info("Sensor Error Mask received: " + str(errorMask))

    def _motorNotificationCallback(self, data=None):
        while not self._motorsNotificationWatchers.empty():
            temp: threading.Event = None
            try:
                temp = self._motorsNotificationWatchers.get_nowait()
            except Exception:
                return
            temp.set()

    def _batteryPercentageCallback(self, percentage):
        logger.info("Battery percentage update: " + str(percentage) + "%")

    def start(self):
        super().start()
        self._threadReady.wait()

    def isConnected(self):
        return self._connectionStatus == CONNECTION_STATUS.CONNECTED

    def connectSerial(self, port):
        self.disconnect()
        self._connection = RobotTransportSerial(
            self._processIncomingPacket, self._connectionStatusCallback
        )
        self._transactionTimings = MovingAverage(self._TIMING_WINDOW_SIZE)
        self._uart.transport = self._connection
        return self._connection.connect(port)

    def connectIP(self, address, port):
        self.disconnect()
        self._connection = RobotTransportTCP(
            self._processIncomingPacket, self._connectionStatusCallback
        )
        self._transactionTimings = MovingAverage(self._TIMING_WINDOW_SIZE)
        self._uart.transport = self._connection
        return self._connection.connect(address, port)

    def connectBLE(self, botID):
        self.disconnect()
        self._connection = RobotTransportBLE(
            self._processIncomingPacket, self._connectionStatusCallback
        )
        self._transactionTimings = MovingAverage(self._TIMING_WINDOW_SIZE)
        self._uart.transport = self._connection
        return self._connection.connect(botID)

    def disconnect(self):
        if self._connection:
            self._connection.disconnect()
        self.resetCommunications()

    def stop(self):
        self.disconnect()
        if self._connection:
            self._connection.stop()
        command1 = ThreadCommand(None)
        command1.setAsStopCommand()
        self._loop.call_soon_threadsafe(self._commandQueue.put_nowait, command1)
        command2 = ThreadCommand(None)
        command2.setAsStopCommand()
        self._loop.call_soon_threadsafe(self._eventQueue.put_nowait, command2)

        command1.waitForResult()
        command2.waitForResult()

    def clearMotorNotificationWatchers(self):
        self._motorNotificationCallback()

    def getNewMotorNotificationWatcherEvent(self):
        e = threading.Event()
        self._motorsNotificationWatchers.put_nowait(e)
        return e

    def getCommsTimingStats(self):
        averageWriteTime = self._connection.getAverageWriteTimeMS()
        recommendedSpamInterval = self._calcNewSpamInterval()
        averageTransactionTime = self._transactionTimings.getAverage()
        return (averageWriteTime, recommendedSpamInterval, averageTransactionTime)

    def startSensorSpam(self, intervalOverride=None):
        requestedInterval = self._calcNewSpamInterval()
        if intervalOverride:
            requestedInterval = intervalOverride
        self._currentRequestedUpdateInterval = requestedInterval
        # Read directly if more than 1.5 spam intervals old
        self._readCache.setUseByInterval(requestedInterval * 1.8)
        self.writeAttribute(
            OPTYPE.SPAM_RATE.value,
            intArrayToBytes([requestedInterval], 2, signed=False),
        )
        self.writeAttribute(OPTYPE.SPAM_MODE.value, [1])
        logger.debug("Sensor spam activated")
        logger.debug("Requested interval: " + str(requestedInterval))
        self._sensorSpamActive = True

    def _calcNewSpamInterval(self):
        averageWriteTime = self._connection.getAverageWriteTimeMS()
        if averageWriteTime <= 0:
            return DEFAULT_SPAM_INTERVAL_MS
        # Run a little slower if the transport has to manage ACKs itself
        # eg. BLE ACKS are handled by writing with response
        timingFactor = 1.8
        if self._connection.SHOULD_FAKE_PACKET_ACK:
            timingFactor = 1.1

        calculatedInterval = averageWriteTime * timingFactor
        if calculatedInterval < MIN_SPAM_INTERVAL_MS:
            return MIN_SPAM_INTERVAL_MS
        return round(calculatedInterval)

    def stopSensorSpam(self):
        self.writeAttribute(OPTYPE.SPAM_MODE.value, [0])
        self._sensorSpamActive = False

    def writeAttribute(self, opType, data, timeout=None):
        if not self.isConnected():
            raise Exception("No robot connected")
        if isinstance(opType, Enum):
            opType = opType.value
        startTime = time.time()
        result = self.queueCommand(
            self._uart.doUartTransaction, OPCODE.WRITE.value, opType, data, timeout
        ).waitForResult(timeout)
        self._transactionTimings.recordValue((time.time() - startTime) * 1000.0)
        return result

    def writePacket(self, opCode, opType, data=None, waitForAck=True, timeout=None):
        if not self.isConnected():
            raise Exception("No robot connected")
        if data is None:
            data = []
        if isinstance(opCode, Enum):
            opCode = opCode.value
        if isinstance(opType, Enum):
            opType = opType.value
        if waitForAck:
            startTime = time.time()
            result = self.queueCommand(
                self._uart.doUartTransaction, opCode, opType, data, timeout
            ).waitForResult(timeout)
            self._transactionTimings.recordValue((time.time() - startTime) * 1000.0)
            return result
        else:
            return self.queueCommand(
                self._connection.writePacketTimed, [opCode, opType, len(data)] + data
            ).waitForResult(timeout)

    def readAttribute(self, opType, data=None, timeout=None):
        if not self.isConnected():
            raise Exception("No robot connected")
        if data is None:
            data = []
        if isinstance(opType, Enum):
            opType = opType.value
        cachedResult = self._readCache.readCache(opType)
        if cachedResult:
            return cachedResult
        startTime = time.time()
        result = self.queueCommand(
            self._uart.doUartTransaction, OPCODE.READ.value, opType, data, timeout
        ).waitForResult(timeout)
        self._transactionTimings.recordValue((time.time() - startTime) * 1000.0)
        return result

    def isInBluetoothMode(self):
        return type(self._connection) == RobotTransportBLE

    def isInTcpMode(self):
        return type(self._connection) == RobotTransportTCP

    def isInSerialMode(self):
        return type(self._connection) == RobotTransportSerial

    def queueCommand(self, f, *args, **kwargs):
        command = ThreadCommand(f, *args, **kwargs)
        self._loop.call_soon_threadsafe(self._commandQueue.put_nowait, command)
        return command

    def queueEvent(self, f, *args, **kwargs):
        command = ThreadCommand(f, *args, **kwargs)
        self._loop.call_soon_threadsafe(self._eventQueue.put_nowait, command)
        return command

    def resetCommunications(self):
        self._readCache.invalidateCache()
        if self._threadReady.is_set():
            self._loop.call_soon_threadsafe(self._unsafeReset)

    def _unsafeReset(self):
        def emptyThreadCommandQueue(q):
            while not q.empty():
                command: ThreadCommand = q.get_nowait()
                command.result = Exception("Cancelled")
                command.completeEvent.set()
                q.task_done()

        emptyThreadCommandQueue(self._commandQueue)
        emptyThreadCommandQueue(self._eventQueue)
        self._uart.clearResponseQueues()

    def run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._commandQueue = asyncio.Queue()
        self._eventQueue = asyncio.Queue()
        self._uart = UartController(self._connection)
        self._uart.clearResponseQueues()

        self._uart.subscribeToSensor(
            OPTYPE.ALL_SENSORS.value, self._readCache.updateAllSensors
        )
        self._uart.subscribeToSensor(
            OPTYPE.MOTOR_SET.value, lambda data: self._motorNotificationCallback(data)
        )
        self._uart.subscribeToSensor(
            OPTYPE.BUTTON_PRESS.value,
            lambda data: self._buttonPressCallback(int.from_bytes(data, "big")),
        )
        self._uart.subscribeToSensor(
            OPTYPE.STATE_OF_CHARGE.value,
            lambda data: self._batteryPercentageCallback(int.from_bytes(data, "big")),
        )
        self._uart.subscribeToSensor(
            OPTYPE.SENSOR_ERRORS.value,
            lambda data: self._sensorErrorMaskCallback(int.from_bytes(data, "big")),
        )

        self._threadReady.set()

        async def commandExecuter(q: asyncio.Queue):
            while True:
                command: ThreadCommand = await q.get()
                if command.isStopCommand:
                    command.result = True
                    command.completeEvent.set()
                    return
                await command.execute()
                q.task_done()

        self._loop.run_until_complete(
            asyncio.gather(
                commandExecuter(self._commandQueue), commandExecuter(self._eventQueue)
            )
        )
        if self._connection:
            self._connection.disconnect()
        self._connection = None
        self._loop.close()
        self._loop = None
        return

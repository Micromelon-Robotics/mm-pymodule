import logging
from ._robot_transport_base import RobotTransportBase
from .._comms_constants import (
    MicromelonOpCode as OPCODE,
    MicromelonType as OPTYPE,
    CONNECTION_STATUS,
)
from ..._binary import bytesToIntArray
import serial
import threading
from ..._mm_logging import getLogger

logger = getLogger()


class RobotTransportSerial(RobotTransportBase):
    def __init__(self, packetReceivedCallback, connectionStatusCallback):
        super().__init__(packetReceivedCallback, connectionStatusCallback)
        self._connection: serial.Serial = None
        self._readingThread: threading.Thread = None

    def connect(self, port, baudrate=115200):
        if self._connection:
            self._connection.close()
            self._connection.port = port
            self._connection.open()
        else:
            self._connection = serial.Serial(port, baudrate=baudrate)
        self._connection.flushInput()
        self._connection.flushOutput()
        self._readingThread = threading.Thread(target=self._readingRoutine, args=())
        self._readingThread.setDaemon(True)
        self._readingThread.start()
        self._connectionStatusCallback(CONNECTION_STATUS.CONNECTED)

    def writePacket(self, data):
        self._connection.write([0x55] + data)

    def disconnect(self):
        if not self._connection:
            return
        self._connection.close()
        self._connection = None
        self._readingThread.join()
        self._readingThread = None
        self._connectionStatusCallback(CONNECTION_STATUS.DISCONNECTED)

    def stop(self):
        self.disconnect()
        if self._readingThread:
            self._readingThread.join()

    def _readingRoutine(self):
        packet = []
        while True:
            readException = None
            try:
                packet = self._readPacket(blocking=True)
            except Exception as e:
                readException = e
            if readException or len(packet) == 0:
                logger.info("Connection closed")
                # if readException:
                #   logger.error(readException)
                self._connectionStatusCallback(CONNECTION_STATUS.DISCONNECTED)
                return
            self._packetReceivedCallback(packet)

    def _readPacket(self, blocking=True):
        """
        Reads a packet from the transport
          returns packet on success or None iff no packet available and non-blocking
          raises an exception for invalid packets
        """
        if not self._connection:
            raise Exception("Not connected - cannot read packet")
        if not blocking and self._connection.in_waiting <= 0:
            return None
        header = self._connection.read(4)
        if len(header) != 4:
            raise Exception("Invalid header: " + str(header))
        header = list(header)
        # Don't include start byte in packet
        header = header[1:]
        data = []
        dataLen = header[2]
        if (
            header[0] == OPCODE.ACK.value
            and header[1] == OPTYPE.RPI_IMAGE.value
            and dataLen > 0
        ):
            # read the actual dataLen from the 4 bytes of image dimensions
            dimensions = self._connection.read(dataLen)
            dimensions = list(dimensions)
            if len(dimensions) == 0:
                raise Exception("Timeout reading packet data")
            dimensions = bytesToIntArray(dimensions, 2, False)
            dataLen = dimensions[0] * dimensions[1] * 3
            header[2] = dataLen
        if dataLen > 0:
            data = self._connection.read(dataLen)
            data = list(data)
            if len(data) == 0:
                raise Exception("Timeout reading packet data")
        return header + data

from ._robot_transport_serial import RobotTransportSerial
from ._serial_tcp_connection import SerialTCPConnection
from .._comms_constants import CONNECTION_STATUS
import threading


class RobotTransportTCP(RobotTransportSerial):
    def __init__(self, packetReceivedCallback, connectionStatusCallback):
        super().__init__(packetReceivedCallback, connectionStatusCallback)
        self._connection: SerialTCPConnection = None

    def connect(self, address, port):
        if self._connection:
            try:
                self._connection.close()
            except Exception as e:
                pass
        self._connection = SerialTCPConnection(address, port)
        self._connection.open()
        # Flushing not needed for a new socket and slows the connection
        # self._connection.flushInput()
        # self._connection.flushOutput()

        self._readingThread = threading.Thread(target=self._readingRoutine, args=())
        self._readingThread.start()
        self._connectionStatusCallback(CONNECTION_STATUS.CONNECTED)

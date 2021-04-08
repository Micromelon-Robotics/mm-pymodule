from ._robot_transport_base import RobotTransportBase
from ..ble import BleControllerThread


class RobotTransportBLE(RobotTransportBase):
    def __init__(self, packetReceivedCallback, connectionStatusCallback):
        super().__init__(packetReceivedCallback, connectionStatusCallback)
        self._bleThread = None
        self.SHOULD_FAKE_PACKET_ACK = True

    def _packetReceivedCallbackWrapper(self, sender, data):
        self._packetReceivedCallback(list(data))

    def connect(self, botID):
        self._bleThread = BleControllerThread(
            self._packetReceivedCallbackWrapper, self._connectionStatusCallback
        )
        self._bleThread.start()
        return self._bleThread.connectToRobot(botID)

    def writePacket(self, data):
        return self._bleThread.writeUartPacket(data, False)

    def disconnect(self):
        return self._bleThread.disconnect()

    def stop(self):
        if self._bleThread:
            self._bleThread.stop()
            self._bleThread.join()

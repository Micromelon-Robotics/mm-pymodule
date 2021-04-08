import time
from .._moving_average import MovingAverage


class RobotTransportBase:
    def __init__(self, packetReceivedCallback, connectionStatusCallback) -> None:
        self._packetReceivedCallback = packetReceivedCallback
        self._connectionStatusCallback = connectionStatusCallback
        self.SHOULD_FAKE_PACKET_ACK = False
        self._writeTimings = MovingAverage(20)

    def getAverageWriteTimeMS(self):
        return self._writeTimings.getAverage()

    def writePacketTimed(self, data):
        startTime = time.time()
        result = self.writePacket(data)
        self._writeTimings.recordValue((time.time() - startTime) * 1000.0)
        return result

    def writePacket(self, data):
        pass

    def disconnect(self):
        pass

    def stop(self):
        pass

    # Subclasses will need a connect method but they will all have different arguments
    # def connect():
    #  pass

from .._comms_constants import MicromelonOpCode as OPCODE, MicromelonType as OPTYPE
import queue
import asyncio
from ..._mm_logging import getLogger

logger = getLogger()


class _responseQueueEntry:
    def __init__(self, opCode, opType, data, future, timeoutTask):
        self.opCode = opCode
        self.opType = opType
        self.data = data
        self.future: asyncio.Future = future
        self.timeoutTask: asyncio.Task = timeoutTask


class _responseQueue:
    def __init__(self, opTypes):
        self.queue = {}
        for t in opTypes:
            self.queue[t] = queue.Queue()

    def remove(self, opType):
        try:
            return self.queue[opType].get(False)
        except Exception:
            return None


async def _timeout(time, future: asyncio.Future):
    await asyncio.sleep(time)
    if not future.done():
        future.set_exception(TimeoutError("Operation timed out"))


class UartController:
    def __init__(self, transport):
        self.notificationCallbacks = {}
        self.responseQueues = _responseQueue([x.value for x in OPTYPE])
        self.transport = transport

    def subscribeToSensor(self, opType, callback):
        if opType in self.notificationCallbacks:
            self.notificationCallbacks[opType].append(callback)
        else:
            self.notificationCallbacks[opType] = [callback]

    def unsubscribeFromSensor(self, opType):
        self.notificationCallbacks[opType] = []

    def clearSensorSubscriptions(self):
        self.notificationCallbacks = {}

    def clearResponseQueues(self):
        self.responseQueues = _responseQueue([x.value for x in OPTYPE])

    def prettyPrintPacket(self, opCode, opType, data):
        # Check opcode
        printOp = "Unknown Opcode: " + str(opCode)
        if OPCODE(opCode) in OPCODE.__members__.values():
            printOp = OPCODE(opCode).name

        # Check opType
        printType = "Unknown Type: " + str(opType)
        if OPTYPE(opType) in OPTYPE.__members__.values():
            printType = OPTYPE(opType).name

        dataStr = "["
        if data:
            for b in data:
                dataStr += "" + str(b) + ", "

        if dataStr[-2:] == ", ":
            dataStr = dataStr[:-2]
        dataStr += "]"
        return "Packet:" + printOp + " " + printType + " - " + dataStr

    async def doUartTransaction(self, opCode, opType, data=None, timeout=3.0):
        if data is None:
            data = []
        fut = asyncio.get_running_loop().create_future()
        timeoutTask = asyncio.get_running_loop().create_task(_timeout(timeout, fut))
        self.responseQueues.queue[opType].put(
            _responseQueueEntry(opCode, opType, data, fut, timeoutTask)
        )
        p = self.buildPacket(opCode, opType, data)

        try:
            self.transport.writePacketTimed(p)
            # logger.debug('Sent: ' + self.prettyPrintPacket(opCode, opType, data))
            if self.transport.SHOULD_FAKE_PACKET_ACK and opCode == OPCODE.WRITE.value:
                # Fake an ack because handled by writing with response (ble)
                # others need to handle their own ack as could be forwarded over unreliable transports
                self.processIncomingPacket(self.buildPacket(OPCODE.ACK.value, opType))
        except Exception as e:
            self.responseQueues.remove(opType)
            logger.debug(e)
            # TODO: process error to see if BLE should be disconnected
            raise

        return await fut

    def processIncomingPacket(self, data):
        if len(data) < 2:
            raise Exception(
                "Got a uart packet with length "
                + str(len(data))
                + " and opcode "
                + str(data[0])
            )
        opCode = data[0]
        opTypeD = data[1]

        if OPCODE(opCode) not in OPCODE.__members__.values():
            logger.error("Unknown opcode in  _uart.py: ", opCode)
            return

        # logger.debug('Received: ' + str(list(data)))
        payload = []
        if len(data) > 2 and data[2] != 0:
            payload = data[3:]

        if OPCODE(opCode) == OPCODE.ACK:
            responseCallbacks: _responseQueueEntry = self.responseQueues.remove(opTypeD)
            if responseCallbacks:
                responseCallbacks.future.set_result(payload)
                responseCallbacks.timeoutTask.cancel()
            # packetStr = prettyPrintPacket(responseCallbacks.opCode,
            #     responseCallbacks.opType, responseCallbacks.data)
            #
            # responseStr = prettyPrintPacket(opCode, opType, payload)
            # mesg = 'UART completed for ' + packetStr ' with response: ' +
            #     responseStr

        elif OPCODE(opCode) == OPCODE.NOTIFY:
            if opTypeD in self.notificationCallbacks:
                for cb in self.notificationCallbacks[opTypeD]:
                    cb(payload)

        elif OPCODE(opCode) in [
            OPCODE.READ,
            OPCODE.WRITE,
            OPCODE.ERROR_INVALID_OP_CODE,
            OPCODE.ERROR_INVALID_PAYLOAD_SIZE,
            OPCODE.ERROR_INVALID_CHECKSUM,
            OPCODE.ERROR_NOT_IMPLEMENTED,
        ]:
            responseCallbacks = self.responseQueues.remove(opTypeD)
            packetStr = self.prettyPrintPacket(
                responseCallbacks.opCode,
                responseCallbacks.opType,
                responseCallbacks.data,
            )
            responseStr = self.prettyPrintPacket(opCode, opTypeD, payload)
            errorStr = "UART failed for " + packetStr + " with response: " + responseStr
            if OPCODE(opCode) == OPCODE.ERROR_NOT_IMPLEMENTED:
                printType = "Unknown Type: " + str(opTypeD)
                if opTypeD in OPTYPE.__members__.values():
                    printType = OPTYPE(opTypeD).name
                errorStr = (
                    printType
                    + " attribute not implemented on this robot.\r"
                    + "\tCheck that firmware is updated."
                )
            if responseCallbacks:
                responseCallbacks.future.set_exception(Exception(errorStr))
                responseCallbacks.timeoutTask.cancel()
            logger.error(errorStr)

    def buildPacket(self, opCode, opType, data=None):
        if data is None:
            data = []
        packet = [opCode, opType, len(data)]
        packet.extend(data)
        return packet

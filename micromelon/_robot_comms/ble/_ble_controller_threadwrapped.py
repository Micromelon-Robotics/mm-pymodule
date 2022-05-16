import threading
import asyncio
from ._ble_controller import BleController
from .._thread_command import ThreadCommand


class BleControllerThread(threading.Thread):
    """
    Wraps the asyncio BLE API in sync function calls
    by queueing them for execution in the thread

    Make sure to call start before calling any other methods
    Call stop before attempting to join on the thread
    """

    def __init__(self, packetReceivedCallback, connectionStatusCallback) -> None:
        super().__init__()

        self.daemon = True
        self._packetReceivedCallback = packetReceivedCallback
        self._connectionStatusCallback = connectionStatusCallback
        self._commandQueue = None
        self._bleController: BleController = None
        self._loop = None
        self._threadReady = threading.Event()

    def start(self):
        super().start()
        self._threadReady.wait()

    def stop(self):
        command = ThreadCommand(None)
        command.setAsStopCommand()
        self._loop.call_soon_threadsafe(self._commandQueue.put_nowait, command)
        command.waitForResult()

    def updateBotID(self, botID):
        return self.queueCommand(self._bleController.updateBotID, botID).waitForResult()

    def read(self, gattChar):
        return self.queueCommand(self._bleController.read, gattChar).waitForResult()

    def write(self, gattChar, data, response):
        return self.queueCommand(
            self._bleController.write, gattChar, data, response
        ).waitForResult()

    def writeUartPacket(self, packet, withoutResponse):
        return self.queueCommand(
            self._bleController.writeUartPacket, packet, withoutResponse
        ).waitForResult()

    def connectBLE(self, reqServices=None, name=None):
        if reqServices is None:
            reqServices = []
        return self.queueCommand(
            self._bleController.connectBLE, reqServices, name
        ).waitForResult()

    def connectToRobot(self, botID):
        return self.queueCommand(
            self._bleController.connectToRobot, botID
        ).waitForResult()

    def disconnect(self):
        if self._bleController:
            return self.queueCommand(self._bleController.disconnect).waitForResult()

    def queueCommand(self, f, *args, **kwargs):
        command = ThreadCommand(f, *args, **kwargs)
        self._loop.call_soon_threadsafe(self._commandQueue.put_nowait, command)
        return command

    def run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._commandQueue = asyncio.Queue()
        self._bleController = BleController(
            self._packetReceivedCallback, self._connectionStatusCallback
        )
        self._threadReady.set()

        async def commandExecuter():
            while True:
                command: ThreadCommand = await self._commandQueue.get()
                if command.isStopCommand:
                    command.result = True
                    command.completeEvent.set()
                    return
                await command.execute()
                self._commandQueue.task_done()

        self._loop.run_until_complete(commandExecuter())
        self._loop.close()
        self._bleController = None
        self._loop = None
        return

import asyncio
import time
from bleak import BleakClient, BleakScanner
from .._comms_constants import CONNECTION_STATUS
from ..._mm_logging import getLogger
import re

logger = getLogger()

MICROMELON_SERVICE_UUID = "00000001-0000-1000-8000-00805f9b34fb"
HEARTBEAT_UUID = "00001112-0000-1000-8000-00805f9b34fb"
UART_UUID = "00001111-0000-1000-8000-00805f9b34fb"
MICROMELON_OTA_SERVICE_UUID = "00000002-0000-1000-8000-00805f9b34fb"
OTA_SERVICE_UUID = "1d14d6ee-fd63-4fa1-bfa4-8f47b42119f0"

SCAN_TIMEOUT = 10  # s
CONNECT_TIMEOUT = 10  # s
DISCOVER_CHARAC_TIMEOUT = 10  # s

IO_TIMEOUT = 2  # s

HEARTBEAT_TIMEOUT = 1.6  # s
HEARTBEAT_INTERVAL = 4.0  # s
HEARTBEAT_TASK_NAME = "HEARTBEA_TASK"


def _format_bdaddr(a):
    return ":".join("{:02X}".format(x) for x in a.to_bytes(6, byteorder="big"))


def _long_to_short_uuid(u):
    if u.startswith("0000") and u.endswith("-0000-1000-8000-00805f9b34fb"):
        return u[4:8]
    return u


class BleController:
    def __init__(self, packetReceivedCallback, connectionStatusCallback):
        self.status = CONNECTION_STATUS.NOT_CONNECTED
        self.userDisconnected = False
        self.botID = -1
        self.client = ""
        self.discoveredCharacs = {}
        self.deviceName = ""
        self.svcs = ""
        self.address = None

        self._packetReceivedCallback = packetReceivedCallback
        self._connectionStatusCallback = connectionStatusCallback

        self.lastReadWriteTime = 0
        self.pauseHeartBeat = False
        self.heartbeatRequired = True
        self.heartbeatTask = None

        self.scanner = None

    def packetReceivedCallbackWrapper(self, sender, data):
        self.lastReadWriteTime = time.time()
        self._packetReceivedCallback(sender, data)

    def _updateConnectionStatus(self, newStatus):
        self.status = newStatus
        self._connectionStatusCallback(newStatus)

    def updateBotID(self, botID):
        self.botID = botID
        if not re.search("^\d{1,4}$", str(botID)):
            logger.warning(
                "Micromelon Robot IDs should be a number between 0 and 8999 - searching for '"
                + str(botID)
                + "' anyway."
            )
        self.deviceName = "Micromelon" + str(self.botID).zfill(4)

    # BLE IO
    async def read(self, gattChar):
        try:
            res = await self.client.read_gatt_char(gattChar)
            self.lastReadWriteTime = time.time()
            return res
        except Exception as e:
            logger.error(e)
            return False

    async def write(self, gattChar, data, response):
        try:
            res = await self.client.write_gatt_char(gattChar, bytearray(data), response)
            self.lastReadWriteTime = time.time()
            return res
        except Exception as e:
            logger.error(e)
            return False

    async def writeUartPacket(self, packet, withoutResponse):
        return await self.client.write_gatt_char(
            UART_UUID, bytearray(packet), not withoutResponse
        )

    # BLE Connection
    async def _detectionCallback(self):
        while 1:
            await asyncio.sleep(0.1)
            for dev in await self.scanner.get_discovered_devices():
                if self.deviceName == None or self.deviceName == dev.name:
                    self.address = dev.address
                    logger.debug("Found with address: ", dev.address)
                    logger.debug("Found name: " + str(dev.name))
                    # self.scanner.stop()
                    return

    async def connectBLE(self, reqServices=None, name=None):
        if reqServices is None:
            reqServices = []
        # Discover all available devices
        self.scanner = BleakScanner(timeout=SCAN_TIMEOUT)
        self.deviceName = name
        self._updateConnectionStatus(CONNECTION_STATUS.SEARCHING)
        await self.scanner.start()
        try:
            await asyncio.wait_for(self._detectionCallback(), timeout=SCAN_TIMEOUT)
        except asyncio.TimeoutError as e:
            # Add relevant message to exception
            e.args = ("Robot not found - Scan timed out", *e.args)
            raise
        finally:
            await self.scanner.stop()
        if not self.address:
            self._updateConnectionStatus(CONNECTION_STATUS.NOT_CONNECTED)
            raise Exception("Robot address not discovered")

        # Create a client instance for the bot
        self.client = BleakClient(self.address)
        self.client.set_disconnected_callback(self._onDisconnected)
        # Connect to the bot via the recorded address
        try:
            self._updateConnectionStatus(CONNECTION_STATUS.CONNECTING)
            await self.client.connect(timeout=CONNECT_TIMEOUT)
            self._updateConnectionStatus(CONNECTION_STATUS.INTERROGATING)
            # Record the available services
            self.svcs = await self.client.get_services()
            # Record the avaiable characteristics
            self.discoveredCharacs = self.svcs.characteristics
        except Exception as e:
            # Unable to connect so print the error
            logger.error("Bluetooth Error")
            logger.error(e)
            # Disconnect
            await self.disconnect()
            raise

        discoveredServiceUUIDs = [str(x.uuid) for x in self.svcs.services.values()]
        for service in reqServices:
            if (
                service not in discoveredServiceUUIDs
                and _long_to_short_uuid(service) not in discoveredServiceUUIDs
            ):
                logger.debug("Service not found: " + service)
                await self.disconnect()
                raise Exception("Required BLE services not discovered")
        return True

    async def connectToRobot(self, botID):
        self.discoveredCharacs = {}
        self.userDisconnected = False
        self.updateBotID(botID)
        # Connect to device
        connectionResult = await self.connectBLE(
            reqServices=[MICROMELON_SERVICE_UUID], name=self.deviceName
        )

        if (
            not connectionResult
            or not len(self.discoveredCharacs)
            or not self.client.is_connected
        ):
            await self.disconnect()
            return False

        try:
            # Sub to UART and HEARTBEAT characs
            await self.client.start_notify(
                UART_UUID, self.packetReceivedCallbackWrapper
            )
            await self.client.start_notify(
                HEARTBEAT_UUID, self.packetReceivedCallbackWrapper
            )
        except Exception as e:
            logger.error("Connection Incomplete")
            logger.error(e)
            logger.error("Please try again, your robot might need updating")
            await self.disconnect()
            return False

        self._updateConnectionStatus(CONNECTION_STATUS.CONNECTED)
        self.lastReadWriteTime = time.time()
        await self.heartbeat()
        return True

    async def timeout(self, time, cb=None):
        try:
            await asyncio.sleep(time)
            await cb()
        except asyncio.CancelledError:
            return

    async def heartbeat(self):
        if self.status != CONNECTION_STATUS.CONNECTED or not self.heartbeatRequired:
            return
        if (
            time.time() - self.lastReadWriteTime > HEARTBEAT_INTERVAL * 0.8
        ) and not self.pauseHeartBeat:
            try:
                readVal = await asyncio.wait_for(
                    self.read(HEARTBEAT_UUID), timeout=HEARTBEAT_TIMEOUT
                )
                # logger.debug('heartbeat read succeeded: ', readVal[0])
                self.lastReadWriteTime = int(time.time())
            except Exception as e:
                logger.debug("heartbeat read failed", e)
                await self.disconnect()
                return
        self.heartbeatTask = asyncio.create_task(
            self.timeout(HEARTBEAT_INTERVAL, self.heartbeat), name=HEARTBEAT_TASK_NAME
        )

    async def disconnect(self, calledByUser=True):
        self.userDisconnected = calledByUser
        if self.heartbeatTask:
            self.heartbeatTask.cancel()
            self.heartbeatTask = None
        self._updateConnectionStatus(CONNECTION_STATUS.DISCONNECTED)
        if self.client:
            await self.client.disconnect()

    def _onDisconnected(self, client):
        self._updateConnectionStatus(CONNECTION_STATUS.DISCONNECTED)
        logger.info("BLE disconnected event")

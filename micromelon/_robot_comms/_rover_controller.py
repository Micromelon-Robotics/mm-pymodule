import logging
import signal
import sys
import os
from .._singleton import Singleton
from ._comms_constants import (
    MicromelonOpCode as OPCODE,
    MicromelonType as OPTYPE,
    RUNNING_STATES,
)
from ._robot_communicator_threaded import RobotCommunicatorThread
from .._binary import bytesToIntArray
from .._mm_logging import getLogger

logger = getLogger()


class RoverController(metaclass=Singleton):
    """
    Manages connection and packet level communication with the robot
    Is a singleton - get a reference to the instance with constructor

    standard usage
    rc = RoverController()

    Then connect using one of the three methods below
    rc.connectSerial('COM port name')
    rc.connectIP(address, port)
    rc.connectBLE(botID)
    """

    def __init__(self, defaultTimeout=3.0) -> None:
        signal.signal(signal.SIGINT, _sigint_handler)
        self._roverSimInfo = 0
        self._roverCharge = None
        self._roverErrorMask = None
        self._defaultCommunicationTimeout = defaultTimeout
        self._robotCommunicator = RobotCommunicatorThread()
        self._robotCommunicator.start()

    def setDefaultCommunicationTimeout(self, newDefaultTimeout: float) -> None:
        """
        This default timeout (in seconds) is used as a fallback for any communication
        that happens with the robot.
        Can be overridden for individual function calls.
        Set a longer timeout if you expect slow communcation.

        Args:
          newDefaultTimeout (float): time in seconds to timeout on a communication command

        Returns:
          None
        """
        self._defaultCommunicationTimeout = newDefaultTimeout

    def isConnected(self) -> bool:
        return self._robotCommunicator.isConnected()

    def connectedRobotIsSimulated(self) -> bool:
        return self.isConnected() and self._roverSimInfo != 0

    def startRover(self, overrideSensorSpamMode: bool = None) -> None:
        """
        Start sequence depending on robot mode:
          Serial UART: Set rover to Expansion mode to respond to packets from UART on header
          Serial TCP: Write the running state for program start
          Bluetooth: Write the running state for program start and start sensor spam iff not overridden to False

        Args:
          overrideSensorSpamMode (bool):
            - Defaults to None
            - Sensor Spam mode will be activated by default for a Bluetooth connection to improve sensor read speeds
            - It is not activated by default for serial and TCP connections

        Returns:
          None
        """
        if (
            self._robotCommunicator.isInBluetoothMode()
            and overrideSensorSpamMode is None
        ) or overrideSensorSpamMode:
            self._robotCommunicator.startSensorSpam()
        if not self._robotCommunicator.isInSerialMode():
            self.writeAttribute(OPTYPE.BUTTON_PRESS, [RUNNING_STATES.RUNNING.value])

    def _postConnectionSetup(self) -> None:
        """
        Check whether the connected robot is simulated
        Read battery percentage and sensor error mask

        Returns:
          None
        """
        self._roverSimInfo = None
        self._roverCharge = None
        self._roverErrorMask = None
        try:
            self._roverSimInfo = self.readAttribute(OPTYPE.SIMULATOR_INFO)[0]
            logger.debug("Rover siminfo: " + str(self._roverSimInfo))
        except Exception as e:
            # couldn't read simulator info - assume not simulated
            logger.info("Rover siminfo read failed")
            logger.info(e)
            self._roverSimInfo = 0

        try:
            self._roverCharge = self.readAttribute(OPTYPE.STATE_OF_CHARGE)[0]
            logger.info("Rover battery at " + str(self._roverCharge) + "%")
            self._roverErrorMask = bytesToIntArray(
                self.readAttribute(OPTYPE.SENSOR_ERRORS), 2, False
            )[0]
            if self._roverErrorMask == 0:
                logger.info("No sensor errors detected")
            else:
                logger.warning("Sensor errors detected")
                logger.warning("Error mask: " + str(self._roverErrorMask))
        except Exception as e:
            logger.error("Failed to read battery and error mask")
            logger.error(e)

    def connectSerial(self, port="/dev/ttyS0"):
        """
        Connects to the desired port and attempts to set the rover to UART mode
        The default port is the miniUART on a Raspberry Pi (primary UART on Zero W, 3, and 4)
          Other Raspberry Pi models have "/dev/ttyAMA0" as primary UART
          Note: You will need to disable serial console on the UART you choose to use for it to function correctly

        Args:
          port (string): Name of serial COM port

        Returns:
          None
        """
        self._robotCommunicator.connectSerial(port)
        self.setRoverToUART(True)
        self._postConnectionSetup()

    def connectIP(self, address="127.0.0.1", port=9000):
        """
        Connects over TCP to the address and port provided.
        To connect to a simulated robot choose the port to match the BotID shown in the robot
          controls on the top left of the simulator window.

        Args:
          address (string): IP address - defaults to IPv4 loopback (127.0.0.1)
          port (int): TCP port number - defaults to 9000

        Returns:
          None
        """
        self._robotCommunicator.connectIP(address, port)
        self._postConnectionSetup()

    def connectBLE(self, botID):
        """
        Connects over Bluetooth LE to a robot displaying the given ID on its screen.

        Args:
          botID (int): Robot ID number (shown on robot screen)

        Returns:
          None
        """
        self._robotCommunicator.connectBLE(botID)
        self._postConnectionSetup()

    def disconnect(self) -> None:
        self._robotCommunicator.disconnect()

    def getTransmitAverageMS(self) -> int:
        """
        Returns:
          The approximate (moving average) time in ms it takes to transmit a packet to the robot.
        """
        stats = self._robotCommunicator.getCommsTimingStats()
        return stats[0]

    def getTransactionAverageMS(self) -> int:
        """
        Returns:
          The approximate (moving average) time in ms it takes to complete a transaction with the robot.
          A transaction is an attribute write or non-cached attribute read
        """
        stats = self._robotCommunicator.getCommsTimingStats()
        return stats[2]

    def stopRover(self):
        """
        Attempts to stop the rover by setting motor speeds to 0, turning off the buzzer,
        turning sensor spam off, and taking it out of running mode.

        Returns:
          None
        """
        waitForAck = False
        timeout = 0.5
        try:
            self.writePacket(OPCODE.WRITE, OPTYPE.SPAM_MODE, [0], waitForAck, timeout)
            self.writePacket(
                OPCODE.WRITE, OPTYPE.MOTOR_SET, [0] * 7, waitForAck, timeout
            )
            self.writePacket(
                OPCODE.WRITE, OPTYPE.BUZZER_FREQ, [0, 0], waitForAck, timeout
            )
            if not self._robotCommunicator.isInSerialMode():
                self.writePacket(
                    OPCODE.WRITE,
                    OPTYPE.BUTTON_PRESS,
                    [RUNNING_STATES.CLOSED.value],
                    waitForAck,
                    timeout,
                )
        except Exception as e:
            logger.debug("Not all robot stop commands completed")
            logger.debug(e)

    def end(self):
        """
        Stops all communication threads and ends the entire Python program.
        """
        self._robotCommunicator.stop()
        self._robotCommunicator.join()
        try:
            sys.exit(0)
        except Exception:
            # Sometimes threading module has a shutdown exception
            # TODO: investigate further
            os._exit(0)

    def writeAttribute(self, opType, data, timeout=None):
        """
        Blocking Write - writes an attribute and returns once the ACK packet is received from the robot.

        Args:
          opType (int or MicromelonOpType): Attribute to write to.
          data (list of bytes): data to write.
          timeout (number): time in seconds to wait for completion.
                          Uses the default timeout of this controller if not provided

        Raises:
          TimeoutError on timeout.
          Exception on comms failure.

        Returns:
          True on success, False otherwise.
        """
        if timeout is None:
            timeout = self._defaultCommunicationTimeout
        return self._robotCommunicator.writeAttribute(opType, data, timeout)

    def readAttribute(self, opType, data=None, timeout=None):
        """
        Blocking read - returns the raw data from robot response

        Args:
          opType (int or MicromelonOpType): Attribute to write to.
          data (list of bytes): extra read configuration data.
          timeout (number): time in seconds to wait for result.
                          Uses the default timeout of this controller if not provided

        Raises:
          TimeoutError on timeout.
          Exception on comms failure.

        Returns:
          List of bytes on success, None otherwise.
        """
        if data is None:
            data = []
        if timeout is None:
            timeout = self._defaultCommunicationTimeout
        return self._robotCommunicator.readAttribute(opType, data, timeout)

    def writePacket(self, opCode, opType, data=None, waitForAck=True, timeout=None):
        """
        Blocking write - Writes the packet over transport.
        Waits for ack by default.

        Args:
          opCode (int or MicromelonOpCode): Flag for type of operation.
          opType (int or MicromelonOpType): Attribute to write to.
          data (list of bytes): data for packet, defaults to None.
          waitForAck (bool): whether or not to wait for the robot to acknowledge the packet. Defaults to true.
          timeout (number): time in seconds to wait for result. Defaults to None (block indefinitely).
                          Uses the default timeout of this controller if not provided

        Raises:
          TimeoutError on timeout.
          Exception on comms failure.

        Returns:
          True on success, False otherwise.
        """
        if data is None:
            data = []
        if timeout is None:
            timeout = self._defaultCommunicationTimeout
        return self._robotCommunicator.writePacket(
            opCode, opType, data, waitForAck, timeout
        )

    def doMotorOperation(self, opType, data, timeout=120):
        """
        Some motor operations that use encoders or IMU take an unknown amount of time to complete.
        In this case the robot acknowledges receipt of the command and then notifies completion at
        a later time.
        This function writes the motor command and waits for the completion notification.
        Only use this if you're sure you want to.

        Args:
          opType (int or MicromelonOpType): Attribute to write to.
          data (list of bytes): data for packet, defaults to None.
          timeout (number): time in seconds to wait for result. Defaults to 120.
                            If your operation should take more than 2 minutes maybe the approach isn't ideal.

        Raises:
          TimeoutError on timeout.
          Exception on comms failure.

        Returns:
          None
        """
        self._robotCommunicator.clearMotorNotificationWatchers()
        toWait = self._robotCommunicator.getNewMotorNotificationWatcherEvent()
        self.writeAttribute(opType, data)
        timedOut = not toWait.wait(timeout)
        if timedOut:
            raise TimeoutError("Motor Encoder operation timed out")

    def setRoverToUART(self, uartMode: bool) -> None:
        """
        Sets the robot's UART control mode.
        If set to True, the robot will respond to packets over the UART connection
        on the expansion header and will not be available for Bluetooth connections.
        If set to false, the robot will be in normal Bluetooth operation mode

        Args:
          uartMode (bool): Whether or not to be in UART mode.

        Raises:
          TimeoutError on timeout.
          Exception on comms failure.

        Returns:
          None
        """
        data = [0]
        if uartMode:
            data = [1]
        self.writePacket(OPCODE.WRITE, OPTYPE.CONTROL_MODE, data)

_sigintAlreadyReceived = False

def _sigint_handler(sig, frame):
    global _sigintAlreadyReceived
    if _sigintAlreadyReceived:
      os._exit(0)
    logger.info("Received SIGINT... Stopping robot")
    _sigintAlreadyReceived = True
    try:
        rc = RoverController()
        rc.stopRover()
        rc.end()
    except Exception as e:
        pass
    os._exit(0)

from .._robot_comms import RoverController, MicromelonType as OPTYPE

from .._utils import isNumber
from .._binary import numberToByteArray

_rc = RoverController()

__all__ = [
    "read",
    "write",
    "scan",
]


def read(address, register, byteCount, addressIs7Bit=True):
    """
    Reads bytes from the register of the I2C device at the address.

    Args:
      address (int): Target I2C device address
      register (int): Register in the target device to read from
      byteCount (int): Number of bytes to read from the register
      addressIs7Bit (boolean): if True then the address argument will be treated as 7 bits
                            This means the address will be shifted left one bit to
                            allow the R/W bit to be set

    Raises:
      Exception if controller is in UART mode
      Exception if the address is too large to be 7 bit and the 7 bit flag is True
      Exception if the read register is > 255

    Returns:
      Array of bytes read from target device register
    """
    if _rc.isConnected() and _rc.isInSerialMode():
        raise Exception("Expansion header used by UART.  I2C not available")
    sanitisedAddress = None
    if addressIs7Bit:
        if address > 127:
            raise Exception("I2C address is too large to be 7 bit (>127)")
        sanitisedAddress = (address << 1) | 1
        # 1 indicates read
    else:
        sanitisedAddress = address | 1

    if register > 0xFF:
        raise Exception("I2C register >255")

    return _rc.readAttribute(OPTYPE.I2C_HEADER, [sanitisedAddress, register, byteCount])


def write(address, register, value, byteCount, addressIs7Bit=True):
    """
    Writes value to the register of the I2C device at the address.

    Args:
      address (int): Target I2C device address
      register (int): Register in the target device to write to
      value (int): Number to write - must be small enough to fit into byteCount bytes or fewer
      byteCount (int): Number of bytes to write to the register
      addressIs7Bit (boolean): if True then the address argument will be treated as 7 bits
                            This means the address will be shifted left one bit to
                            allow the R/W bit to be cleared

    Raises:
      Exception if controller is in UART mode
      Exception if the address is too large to be 7 bit and the 7 bit flag is True
      Exception if the read register is > 255
      Exception if the value requires more bytes than the byteCount argument allows

    Returns:
      Array of bytes that is the response to the write command
    """
    if _rc.isConnected() and _rc.isInSerialMode():
        raise Exception("Expansion header used by UART.  I2C not available")
    sanitisedAddress = None
    if addressIs7Bit:
        if address > 127:
            raise Exception("I2C address is too large to be 7 bit (>127)")
        sanitisedAddress = (address << 1) & 0xFE
        # 0 for LSB indicates write
    else:
        sanitisedAddress = address & 0xFE

    if register > 0xFF:
        raise Exception("I2C register >255")

    bytesToWrite = numberToByteArray(value, byteCount)
    if byteCount < len(bytesToWrite):
        raise Exception(
            "I2C Data to write requires at least {} bytes".format(len(bytesToWrite))
        )

    return _rc.writeAttribute(
        OPTYPE.I2C_HEADER, [sanitisedAddress, register] + bytesToWrite
    )


def scan():
    """
    Scans for any I2C devices connected to the expansion header

    Raises:
      Exception if controller is in UART mode

    Returns:
      Array of device addresses found.  Empty array if none found
    """
    if _rc.isConnected() and _rc.isInSerialMode():
        raise Exception("Expansion header used by UART.  I2C not available")
    return _rc.readAttribute(OPTYPE.I2C_HEADER)

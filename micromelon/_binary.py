def bytesToIntArray(b, bytesPerInt, signed=True, endianness="little"):
    if len(b) % bytesPerInt != 0:
        raise Exception("Wrong number of bytes for conversion")
    nums = [0] * int((len(b) / bytesPerInt))
    for i in range(0, len(b), bytesPerInt):
        nums[int(i / bytesPerInt)] = int.from_bytes(
            b[i : i + bytesPerInt], byteorder=endianness, signed=signed
        )
    return nums


def intArrayToBytes(nums, bytesPerInt, signed=True, endianness="little"):
    b = []
    for i in range(len(nums)):
        b = b + list(
            (nums[i]).to_bytes(bytesPerInt, byteorder=endianness, signed=signed)
        )
    return b


def bytesToAsciiString(b):
    return "".join(list(map(chr, b)))


def stringToBytes(s, encoding="ascii"):
    return list(bytes(s, encoding=encoding))


def numberToByteArray(n, byteCount=None):
    hexStr = hex(n)[2:]  # skip the '0x'
    if len(hexStr) % 2 != 0:
        hexStr = "0" + hexStr
    if not byteCount:
        byteCount = len(hexStr) / 2
    bytesList = []
    for i in range(0, len(hexStr), 2):
        bytesList.append(int(hexStr[i : i + 2], 16))

    if byteCount > len(bytesList):
        return ([0] * (byteCount - len(bytesList))) + bytesList
    return bytesList

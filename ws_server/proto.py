import enum


@enum.unique
class MsgType(enum.IntEnum):
    COMMAND = 0
    BARCODE_IMG = 1
    BARCODE_DATA = 2


@enum.unique
class CmdType(enum.IntEnum):
    START_BARCODE = 0
    STOP_BARCODE = 1

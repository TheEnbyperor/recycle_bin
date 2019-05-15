import enum


@enum.unique
class MsgType(enum.IntEnum):
    COMMAND = 0
    BARCODE_IMG = 1
    BARCODE_DATA = 2
    LOOKUP_ERROR = 3
    LOOKUP_SUCCESS = 4


@enum.unique
class CmdType(enum.IntEnum):
    START_BARCODE = 0
    STOP_BARCODE = 1
    COMP_ON = 2
    COMP_OFF = 3
    COMP_RESET = 4

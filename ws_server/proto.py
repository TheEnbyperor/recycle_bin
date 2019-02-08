import enum


class MsgType(enum.Enum):
    COMMAND = 0
    BARCODE_DATA = 1


class CmdType(enum.Enum):
    START_BARCODE = 0
    STOP_BARCODE = 1

import spidev
import time
import enum


class MCPMode(enum.Enum):
    NORMAL = 0x00
    SLEEP = 0x20
    LOOPBACK = 0x40
    LISTENONLY = 0x60
    CONFIG = 0x80
    POWERUP = 0xE0


class MCPReg(enum.Enum):
    RXF0SIDH = 0x00
    RXF0SIDL = 0x01
    RXF0EID8 = 0x02
    RXF0EID0 = 0x03
    RXF1SIDH = 0x04
    RXF1SIDL = 0x05
    RXF1EID8 = 0x06
    RXF1EID0 = 0x07
    RXF2SIDH = 0x08
    RXF2SIDL = 0x09
    RXF2EID8 = 0x0A
    RXF2EID0 = 0x0B
    BFPCTRL = 0x0C
    TXRTSCTRL = 0x0D
    CANSTAT = 0x0E
    CANCTRL = 0x0F
    RXF3SIDH = 0x10
    RXF3SIDL = 0x11
    RXF3EID8 = 0x12
    RXF3EID0 = 0x13
    RXF4SIDH = 0x14
    RXF4SIDL = 0x15
    RXF4EID8 = 0x16
    RXF4EID0 = 0x17
    RXF5SIDH = 0x18
    RXF5SIDL = 0x19
    RXF5EID8 = 0x1A
    RXF5EID0 = 0x1B
    TEC = 0x1C
    REC = 0x1D
    RXM0SIDH = 0x20
    RXM0SIDL = 0x21
    RXM0EID8 = 0x22
    RXM0EID0 = 0x23
    RXM1SIDH = 0x24
    RXM1SIDL = 0x25
    RXM1EID8 = 0x26
    RXM1EID0 = 0x27
    CNF3 = 0x28
    CNF2 = 0x29
    CNF1 = 0x2A
    CANINTE = 0x2B
    CANINTF = 0x2C
    EFLG = 0x2D
    TXB0CTRL = 0x30
    TXB1CTRL = 0x40
    TXB2CTRL = 0x50
    RXB0CTRL = 0x60
    RXB0SIDH = 0x61
    RXB1CTRL = 0x70
    RXB1SIDH = 0x71


class CANClock(enum.Enum):
    CAN_20MHZ = 0
    CAN_16MHZ = 1
    CAN_8MHZ = 2


class CANRate(enum.Enum):
    CAN_4K096BPS = 0
    CAN_5KBPS = 1
    CAN_10KBPS = 2
    CAN_20KBPS = 3
    CAN_31K25BPS = 4
    CAN_33K3BPS = 5
    CAN_40KBPS = 6
    CAN_50KBPS = 7
    CAN_80KBPS = 8
    CAN_100KBPS = 9
    CAN_125KBPS = 10
    CAN_200KBPS = 11
    CAN_250KBPS = 12
    CAN_500KBPS = 13
    CAN_1000KBPS = 14


spi = spidev.SpiDev()
spi.open(0, 0)

spi.lsbfirst = False
spi.mode = 0
spi.max_speed_hz = 10000000


def reset():
    spi.xfer2([0xC0])
    time.sleep(0.01)


def read_reg(reg):
    return spi.xfer2([0x03, reg & 0xFF, 0x00])[3]


def read_status():
    return spi.xfer2([0xA0, 0x00])[2]


def write_reg(reg, val):
    spi.xfer2([0x02, reg & 0xFF, val & 0xFF])


def modify_reg(reg, mask, val):
    spi.xfer2([0x05, reg & 0xFF, mask & 0xFF, val & 0xFF])


def set_mode(mode):
    modify_reg(MCPReg.CANCTRL, 0xE0, mode)
    resp = read_reg(MCPReg.CANCTRL)
    resp &= 0xE0
    assert resp == mode


def set_rate(can_clock, can_rate):
    data = []
    assert isinstance(can_clock, CANClock)
    assert isinstance(can_rate, CANRate)
    if can_clock == CANClock.CAN_8MHZ:
        if can_rate == CANRate.CAN_5KBPS:
            data = [0xA7, 0xF6, 0x84]
        elif can_rate == CANRate.CAN_10KBPS:
            data = [0x93, 0xF6, 0x84]
        elif can_rate == CANRate.CAN_20KBPS:
            data = [0x89, 0xF6, 0x84]
        elif can_rate == CANRate.CAN_31K25BPS:
            data = [0x87, 0xE5, 0x83]
        elif can_rate == CANRate.CAN_33K3BPS:
            data = [0x85, 0xF6, 0x84]
        elif can_rate == CANRate.CAN_40KBPS:
            data = [0x84, 0xF6, 0x84]
        elif can_rate == CANRate.CAN_50KBPS:
            data = [0x84, 0xE5, 0x83]
        elif can_rate == CANRate.CAN_80KBPS:
            data = [0x84, 0xD3, 0x81]
        elif can_rate == CANRate.CAN_100KBPS:
            data = [0x81, 0xF6, 0x84]
        elif can_rate == CANRate.CAN_125KBPS:
            data = [0x81, 0xE5, 0x83]
        elif can_rate == CANRate.CAN_200KBPS:
            data = [0x80, 0xF6, 0x84]
        elif can_rate == CANRate.CAN_250KBPS:
            data = [0x80, 0xE5, 0x83]
        elif can_rate == CANRate.CAN_500KBPS:
            data = [0x00, 0xD1, 0x81]
        elif can_rate == CANRate.CAN_1000KBPS:
            data = [0x00, 0xC0, 0x80]
    elif can_clock == CANClock.CAN_16MHZ:
        assert can_rate != CANRate.CAN_31K25BPS
        if can_rate == CANRate.CAN_5KBPS:
            data = [0x3F, 0xFF, 0x87]
        elif can_rate == CANRate.CAN_10KBPS:
            data = [0x67, 0xF6, 0x84]
        elif can_rate == CANRate.CAN_20KBPS:
            data = [0x53, 0xF6, 0x84]
        elif can_rate == CANRate.CAN_33K3BPS:
            data = [0x4E, 0xE5, 0x83]
        elif can_rate == CANRate.CAN_40KBPS:
            data = [0x49, 0xF6, 0x84]
        elif can_rate == CANRate.CAN_50KBPS:
            data = [0x47, 0xF6, 0x84]
        elif can_rate == CANRate.CAN_80KBPS:
            data = [0x44, 0xF6, 0x84]
        elif can_rate == CANRate.CAN_100KBPS:
            data = [0x44, 0xE5, 0x83]
        elif can_rate == CANRate.CAN_125KBPS:
            data = [0x43, 0xE5, 0x83]
        elif can_rate == CANRate.CAN_200KBPS:
            data = [0x41, 0xF6, 0x84]
        elif can_rate == CANRate.CAN_250KBPS:
            data = [0x41, 0xE5, 0x83]
        elif can_rate == CANRate.CAN_500KBPS:
            data = [0x40, 0xE5, 0x83]
        elif can_rate == CANRate.CAN_1000KBPS:
            data = [0x00, 0xCA, 0x81]


def init():
    set_mode(MCPMode.LOOPBACK)
    set_rate(CANClock.CAN_16MHZ, CANRate.CAN_500KBPS)

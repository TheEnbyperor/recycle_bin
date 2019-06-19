import can
import enum
import time
import struct
import queue
import threading


@enum.unique
class MessageTypes(enum.Enum):
    DEVICE_DETECT_REQUEST = 0
    DEVICE_DETECT_RESPONSE = 1
    PING = 2
    PONG = 3
    SET_LEDS = 4


class CanDevice:
    def __init__(self, bus_id, bus, controller):
        self._id = bus_id
        self._bus = bus
        self._controller = controller

    def __repr__(self):
        return f"<CanDevice(0x{self._id:x})>"

    def ping(self):
        self._bus.send(can.Message(arbitration_id=0, data=struct.pack("!BH", MessageTypes.PING.value, self._id)), 5)
        last_message = time.time()
        while True:
            resp = self._controller.recv()
            if resp is None:
                break
            if len(resp.data) >= 1:
                if resp.data[0] == MessageTypes.PONG:
                    if resp.arbitration_id == self._id:
                        return True
            self._controller.return_message(resp)
            if time.time() - last_message > 5:
                break
        self._controller.end_return()
        return False

    def set_led(self, red, green, blue, white):
        self._bus.send(
            can.Message(arbitration_id=0,
                        data=struct.pack("!BHBBBB", MessageTypes.SET_LEDS.value, self._id, (red & 0xff), (green & 0xff),
                                         (blue & 0xff), (white & 0xff))), 5)


class CanController:
    def __init__(self):
        self._bus = can.ThreadSafeBus(bustype='socketcan', channel='vcan0', bitrate=500000)
        self._recv_queue = queue.Queue()
        self._recv_return_queue = {}

    def recv(self):
        if not self._recv_queue.empty():
            return self._recv_queue.get()
        resp = self._bus.recv(1)
        return resp

    def return_message(self, msg):
        t_id = threading.get_ident()
        if self._recv_return_queue.get(t_id) is None:
            self._recv_return_queue[t_id] = []
        self._recv_return_queue[t_id].append(msg)

    def end_return(self):
        t_id = threading.get_ident()
        for msg in self._recv_return_queue[t_id]:
            self._recv_queue.put(msg)

    def device(self, id):
        return CanDevice(id & 0x7ff, self._bus, self)

    def find_devices(self):
        devices = []
        self._bus.send(can.Message(arbitration_id=0, data=[MessageTypes.DEVICE_DETECT_REQUEST.value],
                                   extended_id=False), 5)
        last_message = time.time()
        while True:
            resp = self.recv()
            if resp is None:
                break
            if len(resp.data) >= 1:
                if resp.data[0] == MessageTypes.DEVICE_DETECT_RESPONSE.value:
                    device = CanDevice(resp.arbitration_id, self._bus, self)
                    devices.append(device)
                    last_message = time.time()
                    continue
            self.return_message(resp)
            if time.time() - last_message > 5:
                break
        self.end_return()
        return devices

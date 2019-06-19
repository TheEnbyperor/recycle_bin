import can
import random
import struct
import can_bus
import time


class Listener(can.Listener):
    def __init__(self, bus_id, bus):
        self._id = bus_id
        self._bus = bus

    def on_message_received(self, msg):
        if len(msg.data) >= 1:
            if msg.data[0] == can_bus.MessageTypes.DEVICE_DETECT_REQUEST.value:
                self._bus.send(can.Message(arbitration_id=self._id,
                                           data=[can_bus.MessageTypes.DEVICE_DETECT_RESPONSE.value],
                                           extended_id=False), 5)
            elif msg.data[0] == can_bus.MessageTypes.SET_LEDS.value:
                dest_id = struct.unpack("!H", msg.data[1:3])[0]
                if dest_id == self._id:
                    red, green, blue, white = struct.unpack("!BBBB", msg.data[3:8])
                    print(f"SET_LEDS R{red} G{green} B{blue} W{white}")


bus = can.interface.Bus(bustype='socketcan', channel='vcan0', bitrate=500000)
notifier = can.Notifier(bus, [])

bus_id = random.randint(1, 2**11-1)
print(f"Starting with bus id 0x{bus_id:x}")
listener = Listener(bus_id, bus)
notifier.add_listener(listener)

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    notifier.stop()

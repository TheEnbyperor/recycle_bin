import enum
import cv2
import tornado.web


class SocketHandler(tornado.websocket.WebSocketHandler):
    class State(enum.Enum):
        NONE = enum.auto
        BARCODE = enum.auto

    class MsgType(enum.Enum):
        COMMAND = 0
        BARCODE_DATA = 1

    class CmdType(enum.Enum):
        START_BARCODE = 0
        STOP_BARCODE = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        server_loop = tornado.ioloop.IOLoop.current()
        self.barcode_thread = threading.Thread(target=self.barcode_thread_f, args=(server_loop,))
        self.barcode_thread.start()

    def check_origin(self, origin):
        return True

    def on_close(self):
        self.barcode_running = False
        if self.queues in queues:
            queues.remove(self.queues)

    async def on_message(self, message):
        try:
            msg_data = json.loads(message)
        except json.decoder.JSONDecodeError:
            self.close()
            return
        if not all(k in msg_data.keys() for k in ("type", "data")):
            self.close()
            return
        await self.handle_message(msg_data["type"], msg_data["data"])

    async def handle_message(self, msg_type, data):
        if msg_type == self.MSG_TYPE_COMMAND:
            if not all(k in data.keys() for k in ("cmd", "data")):
                self.close()
                return
            await self.handle_command(data["cmd"], data["data"])
        else:
            self.close()

    async def handle_command(self, cmd, data):
        if cmd == self.CMD_TYPE_START_BARCODE:
            self.barcode_running = True
            queues.add(self.queues)
        elif cmd == self.CMD_TYPE_STOP_BARCODE:
            self.barcode_running = False
            queues.remove(self.queues)
        else:
            self.close()

    def write_message_safe(self, *args, **kwargs):
        try:
            self.write_message(*args, **kwargs)
        except tornado.websocket.WebSocketClosedError:
            pass

    def barcode_thread_f(self, server_loop):
        while True:
            if thread_exit:
                break
            if self.barcode_running:
                data = self.queues.cam.get()
                b64_data = base64.b64encode(data).decode()
                server_loop.add_callback(self.write_message_safe, {
                    "type": self.MSG_TYPE_BARCODE_DATA,
                    "data": b64_data
                })





def get_cam():
    cap = cv2.VideoCapture(0)
    cap.set(3, 800)
    cap.set(4, 600)
    cap.set(5, 10)
    return cap


def make_app():
    return tornado.web.Application([
        (r'/ws', SocketHandler),
    ])


if __name__ == "__main__":
    cam = get_cam()
    app = make_app()

import tornado.websocket
import tornado.ioloop
import threading
import json
import queue
import base64
import proto
import scan


class SocketHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._thread_exit = None
        self._barcode_running = None
        self._img_queue = None
        self._scanner = None
        self._barcode_thread = None

    def initialize(self, scanner: scan.BarcodeScanner, exit_event: threading.Event):
        server_loop = tornado.ioloop.IOLoop.current()
        self._thread_exit = exit_event
        self._barcode_running = False
        self._scanner = scanner
        self._barcode_thread = threading.Thread(target=self.barcode_thread_f, args=(server_loop,), daemon=True)
        self._barcode_thread.start()
        self._img_queue = queue.Queue()

    def check_origin(self, origin):
        return True

    def on_close(self):
        self._barcode_running = False
        self._scanner.remove_img_queue(self._img_queue)

    async def on_message(self, message: str):
        try:
            msg_data = json.loads(message)
        except json.decoder.JSONDecodeError:
            self.close()
            return
        if not all(k in msg_data.keys() for k in ("type", "data")):
            self.close()
            return
        await self.handle_message(msg_data["type"], msg_data["data"])

    async def handle_message(self, msg_type: int, data):
        if msg_type == proto.MsgType.COMMAND:
            if not all(k in data.keys() for k in ("cmd", "data")):
                self.close()
                return
            await self.handle_command(data["cmd"], data["data"])
        else:
            self.close()

    async def handle_command(self, cmd: int, data):
        if cmd == proto.CmdType.START_BARCODE:
            self._barcode_running = True
            self._scanner.remove_img_queue(self._img_queue)
        elif cmd == proto.CmdType.STOP_BARCODE:
            self._barcode_running = False
            self._scanner.remove_img_queue(self._img_queue)
        else:
            self.close()

    def write_message_safe(self, *args, **kwargs):
        try:
            self.write_message(*args, **kwargs)
        except tornado.websocket.WebSocketClosedError:
            pass

    def barcode_thread_f(self, server_loop):
        while not self._thread_exit.is_set():
            if self._barcode_running:
                data = self._img_queue.get()
                b64_data = base64.b64encode(data).decode()
                server_loop.add_callback(self.write_message_safe, {
                    "type": proto.MsgType.BARCODE_DATA,
                    "data": b64_data
                })


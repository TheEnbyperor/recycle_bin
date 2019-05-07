import tornado.websocket
import tornado.ioloop
import threading
import json
import queue
import base64
import logging
import proto
import scan


class SocketHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._logger = logging.getLogger(__name__)

    def initialize(self, scanner: scan.BarcodeScanner, exit_event: threading.Event):
        print(exit_event)
        server_loop = tornado.ioloop.IOLoop.current()
        self._thread_exit = exit_event
        self._barcode_running = False
        self._scanner = scanner
        self._barcode_thread = threading.Thread(target=self.barcode_thread_f, args=(server_loop,), daemon=True)
        self._barcode_thread.start()
        self._img_queue = queue.LifoQueue(maxsize=10)
        self._code_queue = queue.Queue(maxsize=3)

    def check_origin(self, origin):
        return True

    def open(self):
        self._logger.info("Client connected to websocket")

    def on_close(self):
        self._logger.info("Closing connection")
        self._barcode_running = False
        self._scanner.remove_img_queue(self._img_queue)
        self._scanner.remove_code_queue(self._code_queue)
        self._code_queue.join()
        self._img_queue.join()
        self._logger.info("Connection closed")

    async def on_message(self, message: str):
        try:
            msg_data = json.loads(message)
        except json.decoder.JSONDecodeError:
            self._logger.warn("Invalid JSON syntax received from client, closing socket")
            self.close()
            return
        if not all(k in msg_data.keys() for k in ("type", "data")):
            self._logger.warn("Invalid data structure received from client, closing socket")
            self.close()
            return
        await self.handle_message(msg_data["type"], msg_data["data"])

    async def handle_message(self, msg_type: int, data):
        if msg_type == proto.MsgType.COMMAND:
            if not all(k in data.keys() for k in ("cmd", "data")):
                self._logger.warn("Invalid data structure received from client, closing socket")
                self.close()
                return
            await self.handle_command(data["cmd"], data["data"])
        else:
            self._logger.warn("Unrecognised message type received, closing socket")
            self.close()

    async def handle_command(self, cmd: int, data):
        if cmd == proto.CmdType.START_BARCODE:
            self._barcode_running = True
            self._scanner.add_img_queue(self._img_queue)
            self._scanner.add_code_queue(self._code_queue)
        elif cmd == proto.CmdType.STOP_BARCODE:
            self._barcode_running = False
            self._scanner.remove_img_queue(self._img_queue)
            self._scanner.remove_code_queue(self._code_queue)
        else:
            self._logger.warn("Unrecognised command received, closing socket")
            self.close()

    def write_message_safe(self, *args, **kwargs):
        try:
            self.write_message(*args, **kwargs)
        except tornado.websocket.WebSocketClosedError:
            pass

    def barcode_thread_f(self, server_loop):
        while not self._thread_exit.is_set():
            if self._barcode_running:
                try:
                    data = self._img_queue.get_nowait()
                    b64_data = base64.b64encode(data).decode()
                    server_loop.add_callback(self.write_message_safe, {
                        "type": proto.MsgType.BARCODE_IMG,
                        "data": b64_data
                    })
                    self._img_queue.task_done()
                except queue.Empty:
                    pass
                try:
                    data = self._code_queue.get_nowait()
                    server_loop.add_callback(self.write_message_safe, {
                        "type": proto.MsgType.BARCODE_DATA,
                        "data": data
                    })
                    self._code_queue.task_done()
                except queue.Empty:
                    pass


import tornado.websocket
import tornado.ioloop
import threading
import json
import queue
import base64
import logging
import time
import proto
import scan
import config
import lights
import gql_client


class SocketHandler(tornado.websocket.WebSocketHandler):
    _config: config.Config
    _logger: logging.Logger
    _thread_exit: threading.Event
    _thread_exit_self: threading.Event
    _scanner: scan.BarcodeScanner
    _barcode_running: bool
    _barcode_thread: threading.Thread
    _barcode_code_thread: threading.Thread
    _code_fetch_thread: threading.Thread
    _img_queue: queue.LifoQueue
    _code_queue: queue.Queue
    _code_fetch_queue: queue.LifoQueue
    _gql_client: gql_client.GQLClient
    _lights: lights.LightingController

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def initialize(self, scanner: scan.BarcodeScanner, exit_event: threading.Event, config: config.Config,
                   lighting_controller: lights.LightingController):
        self._logger = logging.getLogger(__name__)
        server_loop = tornado.ioloop.IOLoop.current()
        self._config = config
        self._lights = lighting_controller
        self._thread_exit = exit_event
        self._barcode_running = False
        self._thread_exit_self = threading.Event()
        self._scanner = scanner
        self._barcode_thread = threading.Thread(target=self.barcode_thread_f, args=(server_loop,), daemon=True)
        self._barcode_code_thread =\
            threading.Thread(target=self.barcode_code_thread_f, args=(server_loop,), daemon=True)
        self._code_fetch_thread =\
            threading.Thread(target=self.code_fetch_thread_f, args=(server_loop,), daemon=True)
        self._img_queue = queue.LifoQueue(maxsize=10)
        self._code_queue = queue.Queue(maxsize=3)
        self._code_fetch_queue = queue.LifoQueue(maxsize=3)
        self._barcode_thread.start()
        self._barcode_code_thread.start()
        self._code_fetch_thread.start()
        self._gql_client = gql_client.GQLClient("http://localhost:8000/graphql/")

    def check_origin(self, origin):
        return True

    def open(self):
        self._logger.info("Client connected to websocket")

    def on_close(self):
        self._logger.info("Closing connection")
        self._barcode_running = False
        self._thread_exit_self.set()
        self._scanner.remove_img_queue(self._img_queue)
        self._scanner.remove_code_queue(self._code_queue)
        self._code_queue.join()
        self._code_fetch_queue.join()
        self._img_queue.join()
        self._logger.info("Connection closed")

    async def on_message(self, message: str):
        try:
            msg_data = json.loads(message)
        except json.decoder.JSONDecodeError:
            self._logger.warning("Invalid JSON syntax received from client, closing socket")
            self.close()
            return
        if not all(k in msg_data.keys() for k in ("type", "data")):
            self._logger.warning("Invalid data structure received from client, closing socket")
            self.close()
            return
        await self.handle_message(msg_data["type"], msg_data["data"])

    async def handle_message(self, msg_type: int, data):
        if msg_type == proto.MsgType.COMMAND.value:
            if not all(k in data.keys() for k in ("cmd", "data")):
                self._logger.warning("Invalid data structure received from client, closing socket")
                self.close()
                return
            await self.handle_command(data["cmd"], data["data"])
        else:
            self._logger.warning("Unrecognised message type received, closing socket")
            self.close()

    async def handle_command(self, cmd: int, data):
        if cmd == proto.CmdType.START_BARCODE.value:
            self._logger.info("Start barcode decoding")
            self._barcode_running = True
            self._scanner.add_img_queue(self._img_queue)
            self._scanner.add_code_queue(self._code_queue)
        elif cmd == proto.CmdType.STOP_BARCODE.value:
            self._logger.info("Stopping barcode decoding")
            self._barcode_running = False
            self._scanner.remove_img_queue(self._img_queue)
            self._scanner.remove_code_queue(self._code_queue)
        elif cmd == proto.CmdType.COMP_ON.value:
            self.handle_set_light(str(data), True)
        elif cmd == proto.CmdType.COMP_OFF.value:
            self.handle_set_light(str(data), False)
        elif cmd == proto.CmdType.COMP_RESET.value:
            self._logger.info("Resetting compartment indicators")
            self._lights.reset()
        else:
            self._logger.warning("Unrecognised command received, closing socket")
            self.close()

    def handle_set_light(self, data: str, state: bool):
        self._logger.info(f"Setting compartment {data} {'On' if state else 'Off'}")
        comp = self._lights.get_compartment(data)
        if comp is None:
            return
        comp.set_state(255 if state else 0)

    def write_message_safe(self, *args, **kwargs):
        try:
            self.write_message(*args, **kwargs)
        except tornado.websocket.WebSocketClosedError:
            pass

    def barcode_thread_f(self, server_loop):
        self._logger.info("Barcode image to client thread started")
        while not (self._thread_exit.is_set() or self._thread_exit_self.is_set()):
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
            else:
                time.sleep(0.1)
        self._logger.info("Barcode image to client thread exiting")

    def barcode_code_thread_f(self, server_loop):
        self._logger.info("Barcode data to client thread started")
        while not (self._thread_exit.is_set() or self._thread_exit_self.is_set()):
            if self._barcode_running:
                try:
                    data = self._code_queue.get_nowait()
                    server_loop.add_callback(self.write_message_safe, {
                        "type": proto.MsgType.BARCODE_DATA,
                        "data": data
                    })
                    try:
                        self._code_fetch_queue.put_nowait(data)
                    except queue.Full:
                        pass
                    self._code_queue.task_done()
                except queue.Empty:
                    pass
            else:
                time.sleep(0.1)
        self._logger.info("Barcode data to client thread exiting")

    def code_fetch_thread_f(self, server_loop):
        self._logger.info("Product lookup thread started")
        while not (self._thread_exit.is_set() or self._thread_exit_self.is_set()):
            try:
                data = self._code_fetch_queue.get_nowait()

                try:
                    data = self._gql_client.query("""
                    query($barcode: String!, $authority: ID!) {
                        product(barcode: $barcode) {
                            id
                            name
                            brand {
                                name
                            }
                            productpartSet {
                                edges {
                                    cursor
                                    node {
                                        id
                                        name
                                        material {
                                            id
                                            name
                                            bin(authority: $authority) {
                                              id
                                              name
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    """, {
                        "barcode": data,
                        "authority": self._config.local_authority
                    })
                    product = data["data"].get("product")
                    if product is None:
                        server_loop.add_callback(self.write_message_safe, {
                            "type": proto.MsgType.LOOKUP_ERROR,
                            "data": "Product not recognised"
                        })
                    else:
                        print(product)
                        server_loop.add_callback(self.write_message_safe, {
                            "type": proto.MsgType.LOOKUP_SUCCESS,
                            "data": product
                        })
                except gql_client.GQLError as e:
                    self._logger.error(f"Error encountered when looking up barcode is database: {str(e)}")
                    server_loop.add_callback(self.write_message_safe, {
                        "type": proto.MsgType.LOOKUP_ERROR,
                        "data": "Unable to contact server. Please try again..."
                    })

                self._code_fetch_queue.task_done()
            except queue.Empty:
                pass
        self._logger.info("Product lookup thread exiting")


import tornado.web
import tornado.ioloop
import tornado.gen
import tornado.iostream
import tornado.concurrent
import tornado.websocket
import threading
import cv2
import json
import base64
import time
import zbar
import numpy as np
from queue import Queue

cam_queues = set()
scanner = zbar.Scanner()
thread_exit = False


class SocketHandler(tornado.websocket.WebSocketHandler):
    MSG_TYPE_COMMAND = 0
    MSG_TYPE_BARCODE_DATA = 1

    CMD_TYPE_START_BARCODE = 0
    CMD_TYPE_STOP_BARCODE = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.barcode_running = False
        self.cam_queue = Queue()

        server_loop = tornado.ioloop.IOLoop.current()
        self.barcode_thread = threading.Thread(target=self.barcode_thread_f, args=(server_loop,))
        self.barcode_thread.start()

    def check_origin(self, origin):
        return True

    def on_close(self):
        self.barcode_running = False
        cam_queues.remove(self.cam_queue)

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
            cam_queues.add(self.cam_queue)
        elif cmd == self.CMD_TYPE_STOP_BARCODE:
            self.barcode_running = False
            cam_queues.remove(self.cam_queue)
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
                data = self.cam_queue.get()
                b64_data = base64.b64encode(data).decode()
                server_loop.add_callback(self.write_message_safe, {
                    "type": self.MSG_TYPE_BARCODE_DATA,
                    "data": {
                        "img": b64_data,
                        "codes": []
                    }
                })


def rotatePoint(pt, mat):
    newX = pt[0] * mat[0][0] + pt[1] * mat[0][1] + mat[0][2]
    newY = pt[0] * mat[1][0] + pt[1] * mat[1][1] + mat[1][2]
    return newX, newY


def fill_cam_queue(cam):
    while True:
        if thread_exit:
            break
        ret, frame = cam.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gradX = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=-1)
        gradY = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=0, dy=1, ksize=-1)
        gradient = cv2.subtract(gradX, gradY)
        gradient = cv2.convertScaleAbs(gradient)
        blurred = cv2.blur(gradient, (9, 9))
        (_, thresh) = cv2.threshold(blurred, 225, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 7))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        closed = cv2.erode(closed, None, iterations=4)
        closed = cv2.dilate(closed, None, iterations=4)
        cnts = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[1]
        c = sorted(cnts, key=cv2.contourArea, reverse=True)
        if len(c) > 0:
            c = c[0]
            rect = cv2.minAreaRect(c)
            box = np.int0(cv2.BoxPoints(rect))
            cv2.drawContours(frame, [box], -1, (0, 255, 0), 3)

            rotMatrix = cv2.getRotationMatrix2D(rect[0], rect[2], 1.0)
            rotRect = tuple([rotatePoint(i, rotMatrix) for i in cv2.BoxPoints(rect)])
            rotBox = numpy.int0(rotRect)

        data = cv2.imencode('.jpg', frame)[1].tostring()
        for q in cam_queues:
            q.put(data)
        time.sleep(0.1)


def make_app():
    return tornado.web.Application([
        (r'/ws', SocketHandler),
        ],)


if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    cap.set(3, 800)
    cap.set(4, 600)
    cap.set(5, 10)
    t = threading.Thread(target=fill_cam_queue, args=(cap,))
    t.start()
    # bind server on 8080 port
    app = make_app()
    app.listen(9090)
    try:
        tornado.ioloop.IOLoop.current().start()
    finally:
        thread_exit = True

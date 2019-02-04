import tornado.web
import tornado.ioloop
import tornado.gen
import tornado.iostream
import tornado.concurrent
import tornado.websocket
import threading
import cv2
import imutils
import json
import base64
import zbar
import math
import numpy as np
import collections
from queue import Queue

queues = set()
scanner = zbar.Scanner()
thread_exit = False
scan_queue = Queue()

QueueDict = collections.namedtuple('QueueDict', ['cam', 'codes'])


class SocketHandler(tornado.websocket.WebSocketHandler):
    MSG_TYPE_COMMAND = 0
    MSG_TYPE_BARCODE_DATA = 1

    CMD_TYPE_START_BARCODE = 0
    CMD_TYPE_STOP_BARCODE = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.barcode_running = False
        self.queues = QueueDict(Queue(), Queue())

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


def rotatePoint(pt, mat):
    newX = pt[0] * mat[0][0] + pt[1] * mat[0][1] + mat[0][2]
    newY = pt[0] * mat[1][0] + pt[1] * mat[1][1] + mat[1][2]
    return newX, newY


def newBouncingBox(size, deg):
    width = size[0]
    height = size[1]

    rad = math.radians(deg)
    sin = abs(math.sin(rad))
    cos = abs(math.cos(rad))

    newWidth = int(width * cos + height * sin) + 1
    newHeight = int(width * sin + height * cos) + 1

    return newWidth, newHeight


def scan_thread():
    while True:
        if thread_exit:
            break
        if not scan_queue.empty():
            frame = scan_queue.get()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            results = scanner.scan(gray)
            results = sorted(results, key=lambda r: r.quality, reverse=True)
            for result in results:
                try:
                    data = result.data.decode()
                except UnicodeDecodeError:
                    continue
                for q in queues:
                    q.codes.put(data)


def rankContours(frame, c):
    ddepth = cv2.cv.CV_32F if imutils.is_cv2() else cv2.CV_32F
    rect = cv2.minAreaRect(c)
    rect = ((rect[0][0], rect[0][1]), (rect[1][0] + 30, rect[1][1] + 30), rect[2])
    if rect[1][0] < rect[1][1]:
        rect = (rect[0], (rect[1][1], rect[1][0]), rect[2] + 90)

    rotMatrix = cv2.getRotationMatrix2D(rect[0], rect[2], 1.0)
    rotWidth, rotHeight = newBouncingBox((frame.shape[1], frame.shape[0]), rect[2])
    rotImage = cv2.warpAffine(frame, rotMatrix, (rotWidth, rotHeight), flags=cv2.INTER_LINEAR)

    boxWidth, boxHeight = np.int0(rect[1])
    boxOrigX, boxOrigY = np.int0((rect[0][0] - rect[1][0] / 2.0, rect[0][1] - rect[1][1] / 2.0))
    rotImage = rotImage[boxOrigY:boxOrigY + boxHeight, boxOrigX:boxOrigX + boxWidth]

    if rotImage.size != 0:
        gradX = cv2.Sobel(rotImage, ddepth=ddepth, dx=1, dy=0, ksize=-1)
        gradY = cv2.Sobel(rotImage, ddepth=ddepth, dx=0, dy=1, ksize=-1)
        gradient = cv2.subtract(gradX, gradY)
        gradient = cv2.convertScaleAbs(gradient)
        blurred = cv2.blur(gradient, (9, 9))
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 7))
        closed = cv2.morphologyEx(blurred, cv2.MORPH_CLOSE, kernel)
        closed = cv2.erode(closed, None, iterations=4)
        closed = cv2.dilate(closed, None, iterations=4)

        return rotImage, rect, np.mean(closed)
    else:
        return rotImage, rect, 0


def fill_cam_queue(cam):
    while True:
        if thread_exit:
            break
        ret, frame = cam.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        (_, thresh) = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        cs = sorted(cnts, key=cv2.contourArea, reverse=True)
        cs = map(lambda c: rankContours(gray, c), cs[0:10])
        cs = sorted(cs, key=lambda c: c[2], reverse=True)
        for i in range(min(3, len(cs))):
            c = cs[i]
            rotImage = c[0]
            rect = c[1]

            box = cv2.cv.boxPoints(rect) if imutils.is_cv2() else cv2.boxPoints(rect)
            box = np.int0(box)
            cv2.drawContours(frame, [box], 0, (0, 0, 255), 2)

            if rotImage.size != 0:
                scan_queue.put(rotImage)

        data = cv2.imencode('.jpg', frame)[1].tostring()
        for q in queues:
            q.cam.put(data)


def make_app():
    return tornado.web.Application([
        (r'/ws', SocketHandler),
    ])


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

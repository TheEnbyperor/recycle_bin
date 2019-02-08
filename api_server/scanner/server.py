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
thread_exit = False
scan_queue = Queue()

QueueDict = collections.namedtuple('QueueDict', ['cam', 'codes'])


def make_app():
    return tornado.web.Application([
        (r'/ws', SocketHandler),
    ])



if __name__ == "__main__":
    t = threading.Thread(target=fill_cam_queue, args=(cap,))
    t.start()
    # bind server on 8080 port
    app = make_app()
    app.listen(9090)
    try:
        tornado.ioloop.IOLoop.current().start()
    finally:
        thread_exit = True

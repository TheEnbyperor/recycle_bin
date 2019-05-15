import cv2
import copy
import time
import math
import queue
import zbar
import threading
import logging


class BarcodeScanner:
    def __init__(self, cam, exit_event: threading.Event):
        self._cam = cam
        self._thread_exit = exit_event
        self._scan_queue = queue.LifoQueue(maxsize=2)
        self._code_queues = set()
        self._img_queues = set()
        self._scanner = zbar.Scanner()
        self._detect_t = threading.Thread(target=self.fill_cam_queue, daemon=True)
        self._scan_t = threading.Thread(target=self.scan_tf, daemon=True)

    def add_code_queue(self, q):
        self._code_queues.add(q)

    def add_img_queue(self, q):
        self._img_queues.add(q)

    def remove_code_queue(self, q):
        if q in self._code_queues:
            self._code_queues.remove(q)

    def remove_img_queue(self, q):
        if q in self._img_queues:
            self._img_queues.remove(q)

    def start(self):
        logging.info("Barcode scanning thread starting")
        self._detect_t.start()
        self._scan_t.start()

    @staticmethod
    def _rotatePoint(pt, mat):
        newX = pt[0] * mat[0][0] + pt[1] * mat[0][1] + mat[0][2]
        newY = pt[0] * mat[1][0] + pt[1] * mat[1][1] + mat[1][2]
        return newX, newY

    @staticmethod
    def _newBouncingBox(size, deg):
        width = size[0]
        height = size[1]

        rad = math.radians(deg)
        sin = abs(math.sin(rad))
        cos = abs(math.cos(rad))

        newWidth = int(width * cos + height * sin) + 1
        newHeight = int(width * sin + height * cos) + 1

        return newWidth, newHeight

    def scan_tf(self):
        while not self._thread_exit.is_set():
            try:
                frame = self._scan_queue.get_nowait()
            except queue.Empty:
                time.sleep(0.1)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.medianBlur(gray, 5)
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 1.5)
            results = self._scanner.scan(thresh)
            results = sorted(results, key=lambda r: r.quality, reverse=True)
            for result in results:
                try:
                    data = result.data.decode()
                except UnicodeDecodeError:
                    logging.warning(f"Unable to debug barcode with raw data {result.data!r}")
                    continue
                logging.info(f"Scanned barcode with data {data!r}")
                for q in copy.copy(self._code_queues):
                    try:
                        q.put_nowait(data)
                    except queue.Full:
                        pass
                break
        logging.info("Barcode decoding thread exiting")

    def fill_cam_queue(self):
        i = 0

        while not self._thread_exit.is_set():
            ret, frame = self._cam.read()
            if not ret:
                break

            if (i % 5) == 0:
                try:
                    self._scan_queue.put_nowait(frame)
                except queue.Full:
                    self._scan_queue.get()
                    self._scan_queue.put(frame)
            i += 1

            data = cv2.imencode('.jpg', frame)[1].tostring()
            for q in copy.copy(self._img_queues):
                try:
                    q.put_nowait(data)
                except queue.Full:
                    pass
        logging.info("Barcode scanning thread exiting")

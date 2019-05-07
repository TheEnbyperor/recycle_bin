import cv2
import math
import queue
import collections
import zbar
import imutils
import threading
import logging
import numpy as np


class BarcodeScanner:
    def __init__(self, cam, exit_event: threading.Event):
        self._cam = cam
        self._thread_exit = exit_event
        self._scan_queue = queue.LifoQueue(maxsize=10)
        self._code_queues = set()
        self._img_queues = set()
        self._scanner = zbar.Scanner()
        self._detect_t = threading.Thread(target=self.fill_cam_queue, daemon=True)
        self._scan_t = threading.Thread(target=self.scan_thread, daemon=True)
        self._logger = logging.getLogger(__name__)

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
        self._logger.info("Barcode scanning thread starting")
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

    def scan_thread(self):
        while not self._thread_exit.is_set():
            if not self._scan_queue.empty():
                frame = self._scan_queue.get()
                results = self._scanner.scan(frame)
                results = sorted(results, key=lambda r: r.quality, reverse=True)
                for result in results:
                    try:
                        data = result.data.decode()
                    except UnicodeDecodeError:
                        self._logger.warning(f"Unable to debug barcode with raw data {result.data!r}")
                        continue
                    self._logger.info(f"Scanned barcode with data {data!r}")
                    for q in self._code_queues:
                        try:
                            q.put_nowait(data)
                        except queue.Full:
                            pass

    def _rankContours(self, frame, c):
        ddepth = cv2.cv.CV_32F if imutils.is_cv2() else cv2.CV_32F
        rect = cv2.minAreaRect(c)
        rect = ((rect[0][0], rect[0][1]), (rect[1][0] + 30, rect[1][1] + 30), rect[2])
        if rect[1][0] < rect[1][1]:
            rect = (rect[0], (rect[1][1], rect[1][0]), rect[2] + 90)

        rotMatrix = cv2.getRotationMatrix2D(rect[0], rect[2], 1.0)
        rotWidth, rotHeight = self._newBouncingBox((frame.shape[1], frame.shape[0]), rect[2])
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

    def fill_cam_queue(self):
        i = 0
        cur_contours = []
        find_barcode_queue = collections.deque(maxlen=3)
        contour_queue = collections.deque(maxlen=3)

        def find_barcode_f():
            while not self._thread_exit.is_set():
                try:
                    frame = find_barcode_queue.pop()
                except IndexError:
                    continue

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                (_, thresh) = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
                cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cnts = imutils.grab_contours(cnts)
                cs = sorted(cnts, key=cv2.contourArea, reverse=True)
                cs = map(lambda c: self._rankContours(gray, c), cs[0:10])
                cs = sorted(cs, key=lambda c: c[2], reverse=True)
                contours = []
                for i in range(min(3, len(cs))):
                    c = cs[i]
                    rotImage = c[0]
                    rect = c[1]

                    box = cv2.cv.boxPoints(rect) if imutils.is_cv2() else cv2.boxPoints(rect)
                    box = np.int0(box)
                    contours.append(box)

                    if rotImage.size != 0:
                        self._logger.debug("Detected possible barcode")
                        try:
                            self._scan_queue.put_nowait(rotImage)
                        except queue.Full:
                            pass
                contour_queue.append(contours)

        find_barcode_t = threading.Thread(target=find_barcode_f, daemon=True)
        find_barcode_t.start()

        while not self._thread_exit.is_set():
            ret, frame = self._cam.read()
            if not ret:
                break

            if (i % 5) == 0:
                find_barcode_queue.append(frame)
            i += 1

            try:
                cur_contours = contour_queue.popleft()
            except IndexError:
                pass

            for box in cur_contours:
                cv2.drawContours(frame, [box], 0, (0, 0, 255), 2)

            data = cv2.imencode('.jpg', frame)[1].tostring()
            for q in self._img_queues:
                try:
                    q.put_nowait(data)
                except queue.Full:
                    pass
        self._logger.info("Barcode scanning thread exiting")

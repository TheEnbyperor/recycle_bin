import cv2
import math
import queue
import zbar
import imutils
import threading
import numpy as np


class BarcodeScanner:
    def __init__(self, cam):
        self._cam = cam
        self._thread_exit = False
        self._scan_queue = queue.Queue()
        self._code_queues = set()
        self._img_queues = set()
        self._scanner = zbar.Scanner()
        self._detect_t = threading.Thread(target=self.fill_cam_queue)

    def add_cam_queue(self, q):
        self._code_queues.add(q)

    def add_img_queue(self, q):
        self._code_queues.add(q)

    def remove_cam_queue(self, q):
        self._code_queues.remove(q)

    def remove_img_queue(self, q):
        self._code_queues.remove(q)

    def start(self):
        self._detect_t.start()

    def stop(self):
        self._thread_exit = True

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
        while True:
            if self._thread_exit:
                break
            if not self._scan_queue.empty():
                frame = self._scan_queue.get()
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                results = self._scanner.scan(gray)
                results = sorted(results, key=lambda r: r.quality, reverse=True)
                for result in results:
                    try:
                        data = result.data.decode()
                    except UnicodeDecodeError:
                        continue
                    for q in self._code_queues:
                        q.put(data)

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
        while True:
            if self._thread_exit:
                break
            ret, frame = self._cam.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            (_, thresh) = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)
            cs = sorted(cnts, key=cv2.contourArea, reverse=True)
            cs = map(lambda c: self._rankContours(gray, c), cs[0:10])
            cs = sorted(cs, key=lambda c: c[2], reverse=True)
            for i in range(min(3, len(cs))):
                c = cs[i]
                rotImage = c[0]
                rect = c[1]

                box = cv2.cv.boxPoints(rect) if imutils.is_cv2() else cv2.boxPoints(rect)
                box = np.int0(box)
                cv2.drawContours(frame, [box], 0, (0, 0, 255), 2)

                if rotImage.size != 0:
                    self._scan_queue.put(rotImage)

            data = cv2.imencode('.jpg', frame)[1].tostring()
            for q in self._img_queues:
                q.put(data)

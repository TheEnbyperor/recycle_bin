import cv2
import tornado.web
import threading
import signal
import scan
import ws_handler


def get_cam():
    cap = cv2.VideoCapture(0)
    cap.set(3, 800)
    cap.set(4, 600)
    cap.set(5, 10)
    return cap


def make_app(scanner, thread_exit):
    return tornado.web.Application([
        (r'/ws', ws_handler.SocketHandler, {
            "scanner": scanner,
            "exit_event": thread_exit
        }),
    ])


class ServiceExit(Exception):
    pass


def service_signal(signum, _):
    print('Caught signal %d' % signum)
    raise ServiceExit


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, service_signal)
    signal.signal(signal.SIGINT, service_signal)
    print("Starting...")

    cam = get_cam()
    thread_exit = threading.Event()
    scanner = scan.BarcodeScanner(cam, thread_exit)
    app = make_app(scanner, thread_exit)
    app.listen(9090)

    try:
        print("Running")
        tornado.ioloop.IOLoop.current().start()
    except ServiceExit:
        thread_exit.set()

        for t in threading.enumerate():
            if t is not threading.current_thread():
                t.join()

    print("Exiting")


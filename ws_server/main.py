import cv2
import tornado.web
import threading
import signal
import logging
import scan
import ws_handler
import gql_client
import config
import lights
import argparse


def get_cam(cam_id):
    cap = cv2.VideoCapture(cam_id)
    cap.set(3, 800)
    cap.set(4, 600)
    cap.set(5, 10)
    return cap


def make_app(scanner, thread_exit, config, lighting_controller):
    return tornado.web.Application([
        (r'/ws', ws_handler.SocketHandler, {
            "scanner": scanner,
            "exit_event": thread_exit,
            "config": config,
            "lighting_controller": lighting_controller,
        }),
    ])


class ServiceExit(Exception):
    pass


def service_signal(signum, _):
    logger.info('Caught signal %d' % signum)
    raise ServiceExit


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='WebSocket server for recycle bin')
    parser.add_argument('--cam', metavar='N', type=int, default=0,
                        help='Numerical ID of the camera to use as in /dev/video*')
    parser.add_argument('--debug', action='store_true', help='Print debug messages')
    parser.add_argument('--server', default="http://localhost:8000/graphl", help='GraphQL endpoint to query against')
    parser.add_argument('--config', default="config.db", help='Location of configuration database')
    args = parser.parse_args()

    logging.basicConfig(level=(logging.DEBUG if args.debug else logging.INFO))
    logger = logging.getLogger(__name__)
    signal.signal(signal.SIGTERM, service_signal)
    signal.signal(signal.SIGINT, service_signal)
    logger.info("Starting...")

    config = config.Config(args.config)
    cam = get_cam(args.cam)
    thread_exit = threading.Event()
    scanner = scan.BarcodeScanner(cam, thread_exit)
    gql_client = gql_client.GQLClient(args.server)
    lighting_controller = lights.LightingController(config)
    app = make_app(scanner, thread_exit, config, lighting_controller)
    app.listen(9090, "127.0.0.1")
    app.listen(9090, "::1")

    try:
        scanner.start()
        logger.info("Running")
        tornado.ioloop.IOLoop.current().start()
    except ServiceExit:
        thread_exit.set()

        for t in threading.enumerate():
            if t is not threading.current_thread():
                t.join()

    logger.info("Exiting")
    del config


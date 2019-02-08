import threading
import queue
import scan
import gql_client


class SearchHandler:
    BARCODE_QUERY = """
        BarcodeQuery($code: String!) {
          query {
            product(barcode: $code) {
              id
              name
              brand {
                id
                name
              }
            }
          }
        }
    """

    def __init__(self, scanner: scan.BarcodeScanner, gql_client: gql_client.GQLClient, exit_event: threading.Event):
        self._scanner = scanner
        self._gql_client = gql_client
        self._thread_exit = exit_event
        self._barcode_queue = queue.Queue()
        self._barcode_t = threading.Thread(target=self.search_from_barcode_t, daemon=True)

    def start(self):
        self._barcode_t.start()
        self._scanner.add_code_queue(self._barcode_queue)

    def search_from_barcode_t(self):
        while not self._thread_exit.set():
            code = self._barcode_queue.get()

            try:
                data = self._gql_client.query(self.BARCODE_QUERY, {"code": code})
            except gql_client.GQLError:
                pass

        self._scanner.remove_code_queue(self._barcode_queue)

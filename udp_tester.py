import SocketServer
import logging
import signal
import threading
import select
logger = logging.getLogger(__name__)


class SocketListener(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request[0]
        maxdata = 20
        if len(data) > maxdata:
            print("Received {} bytes: {}...".format(len(bytes(data)), " ".join(map(lambda x: x[2:], map(hex, list(bytearray(bytes(data[:maxdata]))))))))
        else:
            print("Received {} bytes: {}".format(len(bytes(data)), " ".join(map(lambda x: x[2:], map(hex, list(bytearray(bytes(data))))))))


class Collector(object):
    def __init__(self):
        self.listen_address = ('', 8787)
        self.transmit_buffer = []
        self.transmit_buffer_size = 0
        self.transmit_buffer_threshold = 500  # push the transmit buffer to the database server if it reaches this many entries.
        self.time_between_imports = 1  # seconds. Period for translating lines from SOCKET to TRANSMIT buffers
        self.time_between_transmits = 10  # seconds. Period for transmitting to the database server.
        self.listener = None
        self.listener_thread = None
        self.shutdown_event = threading.Event()
        self.importer = None

    def run(self, host=None, port=None):
        # set up the importer
        if port is not None:
            try:
                self.listen_address = (self.listen_address[0], int(port))
            except (ValueError, TypeError) as e:
                logger.critical('Collector: Invalid port: {}'.format(e))
                return
        if host is not None:
            self.listen_address = (host, self.listen_address[1])

        self.listener = SocketServer.UDPServer(self.listen_address, SocketListener)

        # Start the daemon listening on the port in an infinite loop that exits when the program is killed
        logger.info("Live Collector listening on {0}:{1}.".format(*self.listen_address))
        print("Listening on {0}:{1}".format(*self.listen_address))
        try:
            self.listener.serve_forever()
        except:
            logger.exception("Live_collector server has encountered a critical error.")

        logger.info("Live_collector server shut down successfully.")


if __name__ == "__main__":
    c = Collector()
    c.run(host='', port='8787')

import SocketServer
import logging
import signal
import threading
import time
# import web
from sam import constants
import sam.importers.import_base as base_importer
import requests
import cPickle
import select
logger = logging.getLogger(__name__)

"""
Live Collector
-----------

* runs client-side.
* listens on a socket (usually localhost:514) for messages from a gateway or router
* translates those messages into a standard SAM format
* periodically opens an SSL connection to live_server to send accumulated messages

* two threads: one to read the socket, one to translate and transmit
"""


class SocketBuffer(object):
    def __init__(self):
        self.buffer = []
        self.buffer_lock = threading.Lock()

    def store_data(self, packet):
        # acquire lock
        with self.buffer_lock:
            # append packet
            self.buffer.append(packet)
            # release lock

    def __len__(self):
        return len(self.buffer)

    def pop_all(self):
        with self.buffer_lock:
            packets = self.buffer
            self.buffer = []
        return packets


# used to send data between threads.
SOCKET_BUFFER = SocketBuffer()

class SocketListener(SocketServer.BaseRequestHandler):
    def handle(self):
        global SOCKET_BUFFER
        data = self.request[0]
        SOCKET_BUFFER.store_data(data)


class FileListener(threading.Thread):
    def set_file(self, f):
        self.file = f

    def run(self):
        global SOCKET_BUFFER
        self.alive = True
        while self.alive:
            # block waiting for input from the stream, but unblock every 0.5 seconds.
            # This works on linux but doesn't work on windows.
            # see the [note] in https://docs.python.org/2/library/select.html#select.select
            if self.file in select.select([self.file], [], [], 0.5)[0]:
                line = self.file.readline()
                if line == '':
                    self.alive = False
                else:
                    line = line.rstrip()
                    SOCKET_BUFFER.store_data(line)

    def shutdown(self):
        self.alive = False


class Collector(object):
    def __init__(self):
        self.listen_address = (constants.collector['listen_host'], int(constants.collector['listen_port']))
        self.target_address = constants.collector['target_address']
        self.access_key = constants.collector['upload_key']
        self.default_format = constants.collector['format']
        self.transmit_buffer = []
        self.transmit_buffer_size = 0
        self.transmit_buffer_threshold = 500  # push the transmit buffer to the database server if it reaches this many entries.
        self.time_between_imports = 1  # float, seconds. Period for translating lines from SOCKET to TRANSMIT buffers
        self.time_between_transmits = 10  # float, seconds. Period for transmitting to the database server.
        self.listener = None
        self.listener_thread = None
        self.shutdown_event = threading.Event()
        self.importer = None

    def get_importer(self, format):
        if format is None:
            format = self.default_format
        try:
            importer = base_importer.get_importer(format, 0, 0)
        except:
            importer = None
        return importer

    def form_connection(self, sleep=1.0, max_tries=10):
        attempts = 1
        connected = self.test_connection()
        while not connected and attempts < max_tries:
            time.sleep(sleep)
            connected = self.test_connection()
            attempts += 1
        return connected

    def run(self, port=None, format=None, access_key=None):
        # set up the importer
        self.importer = self.get_importer(format)
        if not self.importer:
            logger.critical("Collector: Failed to load importer; aborting")
            return

        if port is not None:
            try:
                self.listen_address = (self.listen_address[0], int(port))
            except (ValueError, TypeError) as e:
                logger.critical('Collector: Invalid port: {}'.format(e))
                return
        if access_key is not None:
            self.access_key = access_key

        # test the connection
        if not self.form_connection():
            logger.critical('Collector: Failed to connect to aggregator; aborting')
            return

            # register signals for safe shut down
        def sig_handler(num, frame):
            logger.debug('\nInterrupt received.')
            self.shutdown()

        signal.signal(signal.SIGINT, sig_handler)
        self.listener = SocketServer.UDPServer(self.listen_address, SocketListener)

        # Start the daemon listening on the port in an infinite loop that exits when the program is killed
        self.listener_thread = threading.Thread(target=self.listener.serve_forever)
        self.listener_thread.daemon = True
        self.listener_thread.start()
        logger.info("Live Collector listening on {0}:{1}.".format(*self.listen_address))

        try:
            self.thread_batch_processor()
        except:
            logger.exception("Live_collector server has encountered a critical error.")
            self.shutdown()

        logger.info("Live_collector server shut down successfully.")

    def run_streamreader(self, stream, format=None, access_key=None):
        # set up the importer
        self.importer = self.get_importer(format)
        if not self.importer:
            logger.critical("Collector: Failed to load importer; aborting")
            return

        if access_key is not None:
            self.access_key = access_key

        # test the connection
        if not self.form_connection():
            logger.critical('Collector: Failed to connect to aggregator; aborting')
            return

            # register signals for safe shut down
        def sig_handler(num, frame):
            logger.debug('\nInterrupt received.')
            self.shutdown()

        signal.signal(signal.SIGINT, sig_handler)
        self.listener = FileListener()
        self.listener.set_file(stream)

        # Start the daemon listening on the port in an infinite loop that exits when the program is killed
        self.listener_thread = self.listener
        self.listener_thread.daemon = True
        self.listener_thread.start()
        logger.info('Collector: listening to {}.'.format(stream.name if hasattr(stream, 'name') else 'stream'))

        try:
            self.thread_batch_processor()
        except:
            logger.exception("Collector: server has encountered a critical error.")
            self.shutdown()

        logger.info("Collector: server shut down successfully.")

    def thread_batch_processor(self):
        global SOCKET_BUFFER
        # loop:
        #    wait for event, with timeout
        #    check bufferSize
        #       conditionally swap buffers and do processing.

        last_processing = time.time()  # time.time() is in floating point seconds
        alive = True
        while alive:
            triggered = self.shutdown_event.wait(self.time_between_imports)
            if triggered:
                alive = False

            deltatime = time.time() - last_processing
            # Buffer full. Processing.
            if self.transmit_buffer_size > self.transmit_buffer_threshold:
                logger.debug("COLLECTOR: process server running batch (due to buffer cap reached)")
                self.transmit_lines()
                last_processing = time.time()
            # Time's up. Processing.
            elif deltatime > self.time_between_transmits and self.transmit_buffer_size > 0:
                logger.debug("COLLECTOR: process server running batch (due to time)")
                self.transmit_lines()
                last_processing = time.time()
            # Stuff is in there, but the buffer's not full and time isn't up. Not processing.
            elif self.transmit_buffer_size > 0:
                logger.debug("COLLECTOR: waiting for time limit or a full buffer. "
                      "Time at {0:.1f}, Size at {1}".format(deltatime, self.transmit_buffer_size))
            # buffer is empty. Waiting...
            else:
                # Don't let time accumulate while the buffer is empty
                last_processing = time.time()

            # import lines in memory buffer:
            if len(SOCKET_BUFFER) > 0:
                self.import_packets()

        logger.info("COLLECTOR: process server shutting down")

    def import_packets(self):
        global SOCKET_BUFFER
        # clear socket buffer
        packets = SOCKET_BUFFER.pop_all()

        # translate lines
        translations = self.importer.import_packets(packets)

        # insert translations into TRANSMIT_BUFFER
        headers = base_importer.BaseImporter.keys
        for line in translations:
            list_line = [line[header] for header in headers]
            self.transmit_buffer.append(list_line)

        # update TRANSMIT_BUFFER size
        self.transmit_buffer_size = len(self.transmit_buffer)

    def transmit_lines(self):
        access_key = self.access_key
        version = "1.0"
        headers = base_importer.BaseImporter.keys
        lines = self.transmit_buffer
        self.transmit_buffer = []
        self.transmit_buffer_size = 0
        package = {
            'access_key': access_key,
            'version': version,
            'headers': headers,
            'lines': lines
        }

        logger.info("COLLECTOR: Sending package...")
        try:
            response = requests.request('POST', self.target_address, data=cPickle.dumps(package))
            reply = response.content
            logger.debug("COLLECTOR: Received reply: {0}".format(reply))
        except Exception as e:
            reply = 'error'
            logger.error("COLLECTOR: Error sending package: {0}".format(e))
            # keep the unsent lines around
            self.transmit_buffer.extend(lines)
            self.transmit_buffer_size = len(self.transmit_buffer)
        return reply

    def test_connection(self):
        package = {
            'access_key': self.access_key,
            'version': '1.0',
            'headers': base_importer.BaseImporter.keys,
            'msg': 'handshake',
            'lines': []
        }
        try:
            response = requests.request('POST', self.target_address, data=cPickle.dumps(package))
            reply = response.content
        except Exception as e:
            logger.error("Collector: Testing connection...Failed")
            return False
        if reply == 'handshake':
            logger.info("Collector: Testing connection...Succeeded")
            return True
        else:
            reply.replace('\r', '').replace('\n', '')
            if len(reply) > 50:
                logger.error("Error: {}...".format(reply[:50]))
            else:
                logger.error("Error: {}".format(reply))
            return False

    def shutdown(self):
        if self.listener is not None:
            logger.info("COLLECTOR: Shutting down handler.")
            self.listener.shutdown()
            if self.listener_thread:
                self.listener_thread.join()
            logger.info("COLLECTOR: Handler stopped.")
        logger.info("COLLECTOR: Shutting down batch processor.")
        self.shutdown_event.set()


if __name__ == "__main__":
    c = Collector()
    c.run()

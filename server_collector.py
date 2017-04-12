import SocketServer
import threading
import signal
import time
import traceback
import importlib
import importers.import_base as base_importer
import constants
import requests
import cPickle

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

    def store_data(self, lines):
        # acquire lock
        with self.buffer_lock:
            # append line
            self.buffer.append(lines)
            # release lock

    def __len__(self):
        return len(self.buffer)

    def pop_all(self):
        with self.buffer_lock:
            lines = self.buffer
            self.buffer = []
        return lines

# used to send data between threads.
SOCKET_BUFFER = SocketBuffer()


class CollectorListener(SocketServer.BaseRequestHandler):
    def handle(self):
        global SOCKET_BUFFER
        data = self.request[0].strip()
        SOCKET_BUFFER.store_data(data)


class Collector(object):
    def __init__(self):
        self.listen_address = (constants.collector['listen_host'], int(constants.collector['listen_port']))
        self.target_address = 'http://{}:{}'.format(constants.collector['target_host'], constants.collector['target_port'])
        self.access_key = constants.collector['upload_key']
        self.default_format = constants.collector['format']
        self.transmit_buffer = []
        self.transmit_buffer_size = 0
        self.transmit_buffer_threshold = 500  # push the transmit buffer to the database server if it reaches this many entries.
        self.time_between_imports = 1  # seconds. Period for translating lines from SOCKET to TRANSMIT buffers
        self.time_between_transmits = 10  # seconds. Period for transmitting to the database server.
        self.listener = None
        self.listener_thread = None
        self.shutdown_event = threading.Event()
        self.importer = None

    def get_importer(self, importer_name):
        if importer_name.startswith("import_"):
            importer_name = importer_name[7:]
        i = importer_name.rfind(".py")
        if i != -1:
            importer_name = importer_name[:i]
        else:
            importer_name = self.default_format

        # attempt to import the module
        fullname = "importers.import_{0}".format(importer_name)
        try:
            module = importlib.import_module(fullname)
            instance = module._class()
        except ImportError:
            print("Cannot find importer {0}".format(importer_name))
            instance = None
        except AttributeError:
            traceback.print_exc()
            print("Cannot instantiate importer. Is _class defined?")
            instance = None
        return instance

    def run(self, port=None, format=None, access_key=None):
        # set up the importer
        if port is not None:
            try:
                self.listen_address = (self.listen_address[0], int(port))
            except (ValueError, TypeError) as e:
                print('Collector: Invalid port: {}'.format(e))
                return
        if format is None:
            format = self.default_format
        self.importer = self.get_importer(format)
        if not self.importer:
            print("Collector: Failed to load importer; aborting")
            return
        if access_key is not None:
            self.access_key = access_key

        # test the connection
        if self.test_connection() is False:
            return

            # register signals for safe shut down
        def sig_handler(num, frame):
            print('\nInterrupt received.')
            self.shutdown()

        signal.signal(signal.SIGINT, sig_handler)
        self.listener = SocketServer.UDPServer(self.listen_address, CollectorListener)

        # Start the daemon listening on the port in an infinite loop that exits when the program is killed
        self.listener_thread = threading.Thread(target=self.listener.serve_forever)
        self.listener_thread.start()
        print("Live Collector listening on {0}:{1}.".format(*self.listen_address))

        try:
            self.thread_batch_processor()
        except:
            print("Live_collector server has encountered a critical error.")
            traceback.print_exc()
            print("==>--<" * 10)
            self.shutdown()

        print("Live_collector server shut down successfully.")

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
            if self.transmit_buffer_size > self.transmit_buffer_threshold:
                print("CHRON: process server running batch (due to buffer cap reached)")
                self.transmit_lines()
                last_processing = time.time()
            elif deltatime > self.time_between_transmits and self.transmit_buffer_size > 0:
                print("CHRON: process server running batch (due to time)")
                self.transmit_lines()
                last_processing = time.time()
            elif self.transmit_buffer_size > 0:
                print("CHRON: waiting for time limit or a full buffer. "
                      "Time at {0:.1f}, Size at {1}".format(deltatime, self.transmit_buffer_size))
            else:
                # Don't let time accumulate while the buffer is empty
                last_processing = time.time()

            # import lines in memory buffer:
            if len(SOCKET_BUFFER) > 0:
                self.import_lines()

        print("CHRON: process server shutting down")

    def import_lines(self):
        global SOCKET_BUFFER
        # clear socket buffer
        lines = SOCKET_BUFFER.pop_all()

        # translate lines
        translated = []
        for line in lines:
            translated_line = {}
            success = self.importer.translate(line, 1, translated_line)
            if success == 0:
                translated.append(translated_line)

        # insert translations into TRANSMIT_BUFFER
        headers = base_importer.BaseImporter.keys
        for line in translated:
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

        print("Sending package...")
        try:
            response = requests.request('POST', self.target_address, data=cPickle.dumps(package))
            reply = response.content
            print("Received reply: {0}".format(reply))
        except Exception as e:
            print("Error sending package: {0}".format(e))
            # keep the unsent lines around
            self.transmit_buffer.extend(lines)
            self.transmit_buffer_size == len(self.transmit_buffer)

    def test_connection(self):
        print "Testing connection...",

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
            print("Failed.")
            print(e)
            return False
        if reply == 'handshake':
            print("Succeeded.")
            return True
        else:
            print("Bad reply.")
            print('  "{}"'.format(reply))
            return False

    def shutdown(self):
        print("Shutting down handler.")
        self.listener.shutdown()
        if self.listener_thread:
            self.listener_thread.join()
            print("Handler stopped.")
        print("Shutting down batch processor.")
        self.shutdown_event.set()


def localmode():
    # global LISTEN_ADDRESS
    # global SERVER
    # global ACCESS_KEY
    # global FORMAT
    # constants.enable_local_mode()
    # LISTEN_ADDRESS = (constants.collector['hostname'], int(constants.collector['port']))
    # SERVER = constants.collector['server']
    # FORMAT = constants.collector['format']
    # import models.livekeys
    # import common
    # m_livekeys = models.livekeys.LiveKeys(common.db_quiet, constants.demo['id'])
    # keys = m_livekeys.read()
    # ACCESS_KEY = keys[0]['access_key']
    pass


if __name__ == "__main__":
    c = Collector()
    c.run()
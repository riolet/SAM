import SocketServer
import threading
import signal
import time
import traceback
import importers.import_base as base_importer
import live_protocol
import socket
import ssl
import sys
import importlib

"""
Live Collector
-----------

* runs client-side.
* listens on a socket (usually localhost:514) for messages from a gateway or router
* translates those messages into a standard SAM format
* periodically opens an SSL connection to live_server to send accumulated messages

"""


LISTEN_ADDRESS = ('localhost', 514)
SERVER_ADDRESS = ('localhost', 8081)
ACCESS_KEY = 'lLbEAWT6fpbXIogTRTh_qKyW'
CERTIFICATE_FILE = "cert.pem"

SOCKET_BUFFER = []
SOCKET_BUFFER_LOCK = threading.Lock()
TRANSMIT_BUFFER = []
TRANSMIT_BUFFER_SIZE = 0
TRANSMIT_BUFFER_THRESHOLD = 500  # push the transmit buffer to the database server if it reaches this many entries.
TIME_BETWEEN_IMPORTING = 1  # seconds. Period for translating lines from SOCKET to TRANSMIT buffers
TIME_BETWEEN_TRANSMISSION = 10  # seconds. Period for transmitting to the database server.

COLLECTOR = None  # collector server object
COLLECTOR_THREAD = None  # collector server thread
SHUTDOWN_EVENT = threading.Event()  # shuts down the processing loop when .set()
IMPORTER = None


def get_importer(argv):
    global IMPORTER
    if len(argv) != 2:
        print("Please specify the format when running the collector. \nFor example:")
        print("\t{0} nfdump".format(argv[0]))

    # strip the extras of the name
    importer_name = argv[1]
    if importer_name.startswith("import_"):
        importer_name = importer_name[7:]
    i = importer_name.rfind(".py")
    if i != -1:
        importer_name = importer_name[:i]

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


def thread_batch_processor():
    global TRANSMIT_BUFFER_SIZE
    global TRANSMIT_BUFFER_THRESHOLD
    global TIME_BETWEEN_IMPORTING
    global TIME_BETWEEN_TRANSMISSION
    global SOCKET_BUFFER
    global SHUTDOWN_EVENT
    # loop:
    #    wait for event, with timeout
    #    check bufferSize
    #       conditionally swap buffers and do processing.

    last_processing = time.time()  # time.time() is in floating point seconds
    alive = True
    while alive:
        triggered = SHUTDOWN_EVENT.wait(TIME_BETWEEN_IMPORTING)
        if triggered:
            alive = False

        deltatime = time.time() - last_processing
        if TRANSMIT_BUFFER_SIZE > TRANSMIT_BUFFER_THRESHOLD:
            print("CHRON: process server running batch (due to buffer cap reached)")
            transmit_lines()
            last_processing = time.time()
        elif deltatime > TIME_BETWEEN_TRANSMISSION and TRANSMIT_BUFFER_SIZE > 0:
            print("CHRON: process server running batch (due to time)")
            transmit_lines()
            last_processing = time.time()
        elif TRANSMIT_BUFFER_SIZE > 0:
            print("CHRON: waiting for time limit or a full buffer. "
                  "Time at {0:.1f}, Size at {1}".format(deltatime, TRANSMIT_BUFFER_SIZE))
        else:
            # Don't let time accumulate while the buffer is empty
            last_processing = time.time()

        # import lines in memory buffer:
        if len(SOCKET_BUFFER) > 0:
            import_lines()

    print("CHRON: process server shutting down")


def import_lines():
    global SOCKET_BUFFER
    global SOCKET_BUFFER_LOCK
    global TRANSMIT_BUFFER
    global TRANSMIT_BUFFER_SIZE
    # clear socket buffer
    lines = []
    with SOCKET_BUFFER_LOCK:
        lines = SOCKET_BUFFER
        SOCKET_BUFFER = []
    
    # translate lines
    translated = []
    for line in lines:
        translated_line = {}
        success = IMPORTER.translate(line, 1, translated_line)
        if success == 0:
            translated.append(translated_line)

    # insert translations into TRANSMIT_BUFFER
    headers = base_importer.BaseImporter.keys
    for line in translated:
        list_line = [line[header] for header in headers]
        TRANSMIT_BUFFER.append(list_line)

    # update TRANSMIT_BUFFER size
    TRANSMIT_BUFFER_SIZE = len(TRANSMIT_BUFFER)


def transmit_lines():
    global TRANSMIT_BUFFER
    global TRANSMIT_BUFFER_SIZE
    global CERTIFICATE_FILE
    global SERVER_ADDRESS
    global ACCESS_KEY
    address = ("localhost", 8081)
    access_key = ACCESS_KEY
    version = "1.0"
    headers = base_importer.BaseImporter.keys
    lines = TRANSMIT_BUFFER
    TRANSMIT_BUFFER = []
    TRANSMIT_BUFFER_SIZE = 0
    package = {
        'access_key': access_key,
        'version': version,
        'headers': headers,
        'lines': lines
    }

    # Send data on the socket!
    plain_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ssl_sock = ssl.wrap_socket(plain_sock,
                               ca_certs="cert.pem",
                               cert_reqs=ssl.CERT_REQUIRED,
                               ssl_version=ssl.PROTOCOL_TLSv1_2)
    translator = live_protocol.LiveProtocol(ssl_sock)

    try:
        print("SOCKET: Opening...")
        ssl_sock.connect(SERVER_ADDRESS)

        print("SOCKET: Sending {0} lines.".format(len(package['lines'])))
        translator.send(package)

        response = translator.receive()
        print("SOCKET: Receiving: {0} chars. {1}...".format(len(response), repr(response[:50])))
        ssl_sock.close()
    except socket.error as e:
        print("SOCKET: Could not connect to socket {0}:{1}".format(*address))
        print("SOCKET: Error {0}: {1}".format(e.errno, e.strerror))


def test_connection():
    print "Testing connection...",
    try:
        plain_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssl_sock = ssl.wrap_socket(plain_sock,
                                   ca_certs="cert.pem",
                                   cert_reqs=ssl.CERT_REQUIRED,
                                   ssl_version=ssl.PROTOCOL_TLSv1_2)
        translator = live_protocol.LiveProtocol(ssl_sock)

        translator.send("hello")
        response = translator.receive()
    except:
        print("Failed.")
        return False
    print("Succeeded.")
    return True

def store_data(lines):
    global SOCKET_BUFFER
    global SOCKET_BUFFER_LOCK

    # acquire lock
    with SOCKET_BUFFER_LOCK:
        # append line
        SOCKET_BUFFER.append(lines)
    # release lock


# Request handler used to listen on the port
# Uses synchronous message processing as threading was causing database issues
class UDPRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        store_data(data)


def signal_handler(signal_number, stack_frame):
    print("\nInterrupt received.")
    shutdown()


def shutdown():
    global COLLECTOR
    global COLLECTOR_THREAD
    global SHUTDOWN_EVENT

    print("Shutting down handler.")
    COLLECTOR.shutdown()
    if COLLECTOR_THREAD:
        COLLECTOR_THREAD.join()
        print("Handler stopped.")
    print("Shutting down batch processor.")
    SHUTDOWN_EVENT.set()


if __name__ == "__main__":
    # set up the importer
    IMPORTER = get_importer(sys.argv)
    if not IMPORTER:
        print("Aborting.")
        sys.exit(1)

    # test the connection


    # register signals for safe shut down
    signal.signal(signal.SIGINT, signal_handler)
    COLLECTOR = SocketServer.UDPServer(LISTEN_ADDRESS, UDPRequestHandler)

    # Start the daemon listening on the port in an infinite loop that exits when the program is killed
    COLLECTOR_THREAD = threading.Thread(target=COLLECTOR.serve_forever)
    COLLECTOR_THREAD.start()

    print("Live Collector listening on {0}:{1}.".format(*LISTEN_ADDRESS))


    try:
        thread_batch_processor()
    except:
        traceback.print_exc()
        print("==>--<" * 10)
        shutdown()

    print("Server shut down successfully.")

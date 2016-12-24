import SocketServer
import threading
import signal
import time
import traceback
import import_paloalto
import import_base
import live_protocol
import socket
import ssl

COLLECTOR_ADDRESS = ('localhost', 514)
SERVER_ADDRESS = ('localhost', 8081)
CERTIFICATE_FILE = "cert.pem"

SOCKET_BUFFER = []
SOCKET_BUFFER_LOCK = threading.Lock()
TRANSMIT_BUFFER = []
TRANSMIT_BUFFER_SIZE = 0
TRANSMIT_BUFFER_THRESHOLD = 200 # push the transmit buffer to the database server if it reaches this many entries.
TIME_BETWEEN_IMPORTING = 1 # seconds. Period for translating lines from SOCKET to TRANSMIT
TIME_BETWEEN_TRANSMISSION = 10 # seconds. Period for transmitting to the database server.

COLLECTOR = None  # collector server object
COLLECTOR_THREAD = None # collector server thread
SHUTDOWN_EVENT = threading.Event() # shuts down the processing loop when .set()


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
            print("CHRON: waiting for time limit or a full buffer.  Time at {0:.1f}, Size at {1}".format(deltatime, TRANSMIT_BUFFER_SIZE))
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
    importer = import_paloalto.PaloAltoImporter()
    translated = []
    for line in lines:
        translated_line = {}
        success = importer.translate(line, 1, translated_line)
        if success == 0:
            translated.append(translated_line)

    # insert translations into TRANSMIT_BUFFER
    headers = import_base.BaseImporter.keys
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
    address = ("localhost", 8081)
    password = "not-so-secret-passcode"
    version = "1.0"
    headers = import_base.BaseImporter.keys
    lines = TRANSMIT_BUFFER
    TRANSMIT_BUFFER = []
    TRANSMIT_BUFFER_SIZE = 0
    package = {
        'password': password,
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
    # Port and host to listen from

    # register signals for safe shut down
    signal.signal(signal.SIGINT, signal_handler)
    COLLECTOR = SocketServer.UDPServer(COLLECTOR_ADDRESS, UDPRequestHandler)

    # Start the daemon listening on the port in an infinite loop that exits when the program is killed
    COLLECTOR_THREAD = threading.Thread(target=COLLECTOR.serve_forever)
    COLLECTOR_THREAD.start()

    print("Live Collector listening on {0}:{1}.".format(*COLLECTOR_ADDRESS))

    try:
        thread_batch_processor()
    except:
        traceback.print_exc()
        print("==>--<" * 10)
        shutdown()

    print("Server shut down successfully.")

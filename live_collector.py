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

socket_buffer_mutex = threading.Lock()
socket_buffer = []

transmit_buffer = []
transmit_buffer_size = 0
handler_server = None
handler_thread = None
shutdown_processor = threading.Event()


def thread_batch_processor():
    # loop:
    #    wait for event, with timeout
    #    check bufferSize
    #       conditionally swap buffers and do processing.
    global syslog_size
    seconds_per_scan = 1
    max_time_between_processing = 20

    last_processing = time.time()  # time.time() is in floating point seconds
    alive = True
    while alive:
        triggered = shutdown_processor.wait(seconds_per_scan)
        if triggered:
            alive = False

        deltatime = time.time() - last_processing
        if transmit_buffer_size > 100:
            print("CHRON: process server running batch (due to buffer cap reached)")
            transmit_lines()
            last_processing = time.time()
        elif deltatime > max_time_between_processing and transmit_buffer_size > 0:
            print("CHRON: process server running batch (due to time)")
            transmit_lines()
            last_processing = time.time()
        elif transmit_buffer_size > 0:
            print("CHRON: waiting for time limit or a full buffer.  Time at {0:.1f}, Size at {1}".format(deltatime, transmit_buffer_size))
        else:
            # Don't let time accumulate while the buffer is empty
            last_processing = time.time()

        # import lines in memory buffer:
        if len(socket_buffer) > 0:
            import_lines()

    print("CHRON: process server shutting down")


def import_lines():
    global socket_buffer
    global socket_buffer_mutex
    global transmit_buffer
    global transmit_buffer_size
    # clear socket buffer
    lines = []
    with socket_buffer_mutex:
        lines = socket_buffer
        socket_buffer = []
    
    # translate lines
    importer = import_paloalto.PaloAltoImporter()
    translated = []
    for line in lines:
        translated_line = {}
        success = importer.translate(line, 1, translated_line)
        if success == 0:
            translated.append(translated_line)

    # insert translations into transmit_buffer
    headers = import_base.BaseImporter.keys
    for line in translated:
        list_line = [line[header] for header in headers]
        transmit_buffer.append(list_line)

    # update transmit_buffer size
    transmit_buffer_size = len(transmit_buffer)

def transmit_lines():
    global transmit_buffer
    global transmit_buffer_size
    address = ("localhost", 8081)
    password = "not-so-secret-passcode"
    version = "1.0"
    headers = import_base.BaseImporter.keys
    lines = transmit_buffer
    transmit_buffer = []
    transmit_buffer_size = 0
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
        ssl_sock.connect(address)

        print("SOCKET: Sending {0} lines.".format(len(package['lines'])))
        translator.send(package)

        response = translator.receive()
        print("SOCKET: Receiving: {0} chars. {1}...".format(len(response), repr(response[:50])))
        ssl_sock.close()
    except socket.error as e:
        print("SOCKET: Could not connect to socket {0}:{1}".format(*address))
        print("SOCKET: Error {0}: {1}".format(e.errno, e.strerror))


def store_data(lines):
    global socket_buffer
    global socket_buffer_mutex

    # acquire lock
    with socket_buffer_mutex:
        # append line
        socket_buffer.append(lines)
    # release lock


# Request handler used to listen on the port
# Uses synchronous message processing as threading was causing database issues
class UDPRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        global buffer_size
        global buffer_id

        data = self.request[0].strip()
        store_data(data)


def signal_handler(signal_number, stack_frame):
    print("\nInterrupt received.")
    shutdown()


def shutdown():
    print("Shutting down handler.")
    handler_server.shutdown()
    if handler_thread:
        handler_thread.join()
        print("Handler stopped.")
    print("Shutting down batch processor.")
    shutdown_processor.set()


if __name__ == "__main__":
    # Port and host to listen from
    HOST, PORT = "localhost", 514

    # register signals for safe shut down
    signal.signal(signal.SIGINT, signal_handler)
    handler_server = SocketServer.UDPServer((HOST, PORT), UDPRequestHandler)
    ip, port = handler_server.server_address

    # Start the daemon listening on the port in an infinite loop that exits when the program is killed
    handler_thread = threading.Thread(target=handler_server.serve_forever)
    handler_thread.start()

    print("Live Collector listening on {0}:{1}.".format(HOST, PORT))

    try:
        thread_batch_processor()
    except:
        traceback.print_exc()
        print("==>--<" * 10)
        shutdown()

    print("Server shut down successfully.")

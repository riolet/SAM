import SocketServer
import threading
import traceback
import signal
import ssl
import time
import live_protocol
import dbaccess
import preprocess
import importers.import_base


# Self-signed certificate generation for testing:
# openssl req -new -x509 -days 365 -nodes -out cert.pem -keyout cert.pem

CERTIFICATE_FILE = "cert.pem"
HOST = "localhost"
PORT = 8081
SERVER = None
SERVER_THREAD = None
PASSCODE = b'not-so-secret-passcode'
MEMORY_BUFFER = []
MEMORY_BUFFER_LOCK = threading.Lock()
SYSLOG_SIZE = 0
SYSLOG_PROCESSING_QUOTE = 1000 # when the syslog has this many entries, process it.
TIME_BETWEEN_IMPORTING = 1 # seconds. Check for and import lines into the syslog with this period.
TIME_BETWEEN_PROCESSING = 20 # seconds. Process a partially-filled syslog with this period.
SHUTDOWN_EVENT = threading.Event()


class SSL_TCPServer(SocketServer.TCPServer):
    def __init__(self,
                 server_address,
                 RequestHandlerClass,
                 certfile,
                 keyfile=None,
                 ssl_version=ssl.PROTOCOL_TLSv1_2,
                 bind_and_activate=True):
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass, bind_and_activate)
        self.certfile = certfile
        self.keyfile = keyfile
        self.ssl_version = ssl_version

    def get_request(self):
        newsocket, fromaddr = self.socket.accept()
        if self.keyfile:
            connstream = ssl.wrap_socket(newsocket,
                                         server_side=True,
                                         certfile=self.certfile,
                                         keyfile=self.keyfile,
                                         ssl_version=self.ssl_version)
        else:
            connstream = ssl.wrap_socket(newsocket,
                                     server_side=True,
                                     certfile=self.certfile,
                                     ssl_version=self.ssl_version)
        return connstream, fromaddr


class SSL_ThreadingTCPServer(SocketServer.ThreadingMixIn, SSL_TCPServer): pass


class testHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        print("SERVER: Handling input!")
        translator = live_protocol.LiveProtocol(self.connection)
        self.data = None
        try:
            self.data = translator.receive()
        except:
            traceback.print_exc()
            translator.send("Error processing request")

        if self.data:
            with MEMORY_BUFFER_LOCK:
                MEMORY_BUFFER.append(self.data)

        translator.send("Received {0}".format(repr(self.data)[:50]))


def signal_handler(signal_number, stack_frame):
    print("\nInterrupt received.")
    shutdown()


def shutdown():
    global SERVER
    global SERVER_THREAD

    print("Shutting down server.")
    SERVER.shutdown()
    if SERVER_THREAD:
        SERVER_THREAD.join()
        print("Handler stopped.")
    SHUTDOWN_EVENT.set()


def import_messages(messages):
    global SYSLOG_SIZE
    settings = dbaccess.get_settings()
    importer = importers.import_base.BaseImporter()
    importer.datasource = settings['live_dest']
    if importer.datasource is None:
        print("IMPORTER: No destination specified for live data")
        return

    for msg in messages:
        # TODO: check password
        # TODO: check message version

        lines = msg['lines']
        headers = msg['headers']
        # lines is a list of rows, where each row is a list of values
        # headers is a list of column names
        # rows is a list of dictionaries where each dictionary is the headers applied to that row of data
        rows = [{headers[i]: v for i, v in enumerate(row)} for row in lines]
        print("IMPORTER: importing {0} lines to the Syslog. Syslog is now {1}".format(len(lines), SYSLOG_SIZE + len(lines)))
        importer.insert_data(rows, len(lines))
        SYSLOG_SIZE += len(lines)


def preprocess_lines():
    global SYSLOG_SIZE
    print("PREPROCESSOR: preprocessing the syslog. ({0} lines)".format(SYSLOG_SIZE))
    settings = dbaccess.get_settings()
    if settings['live_dest'] is None:
        print("PREPROCESSOR: No live data source specified. Check settings.")
    else:
        preprocess.preprocess_log(ds=settings['live_dest'])
    SYSLOG_SIZE = 0


def thread_batch_processor():
    # loop:
    #    wait for event, with timeout
    #    check bufferSize
    #       conditionally swap buffers and do processing.
    global SYSLOG_SIZE
    global SHUTDOWN_EVENT
    global MEMORY_BUFFER
    global TIME_BETWEEN_IMPORTING
    global TIME_BETWEEN_PROCESSING

    last_processing = time.time()  # time.time() is in floating point seconds
    alive = True
    while alive:
        triggered = SHUTDOWN_EVENT.wait(TIME_BETWEEN_IMPORTING)
        if triggered:
            alive = False

        deltatime = time.time() - last_processing
        if SYSLOG_SIZE > 1000:
            print("CHRON: process server running batch (due to buffer cap reached)")
            preprocess_lines()
            last_processing = time.time()
        elif deltatime > TIME_BETWEEN_PROCESSING and SYSLOG_SIZE > 0:
            print("CHRON: process server running batch (due to time)")
            preprocess_lines()
            last_processing = time.time()
        elif SYSLOG_SIZE > 0:
            print("CHRON: waiting for time limit or a full buffer.  Time at {0:.1f}, Size at {1}".format(deltatime, SYSLOG_SIZE))
        else:
            # don't let time accumulate while the buffer is empty.
            last_processing = time.time()

        # import lines in memory buffer:
        if len(MEMORY_BUFFER) > 0:
            with MEMORY_BUFFER_LOCK:
                messages = MEMORY_BUFFER
                MEMORY_BUFFER = []
            import_messages(messages)

    print("CHRON: process server shutting down")


def main():
    global SERVER
    global SERVER_THREAD
    global HOST
    global PORT
    global CERTIFICATE_FILE

    # register signals for safe shut down
    signal.signal(signal.SIGINT, signal_handler)

    # Start the daemon listening on the port in an infinite loop that exits when the program is killed
    SSL_TCPServer.allow_reuse_address = True
    SERVER = SSL_ThreadingTCPServer((HOST, PORT), testHandler, CERTIFICATE_FILE)
    SERVER_THREAD = threading.Thread(target=SERVER.serve_forever)
    SERVER_THREAD.start()

    print("Live Server listening on {0}:{1}.".format(HOST, PORT))

    try:
        thread_batch_processor()
    except:
        traceback.print_exc()
        print("==>--<" * 10)
        shutdown()

    print("Server shut down successfully.")


if __name__ == "__main__":
    main()

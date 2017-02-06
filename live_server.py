import SocketServer
import threading
import traceback
import signal
import ssl
import time
import live_protocol
import preprocess
import common
import importers.import_base

"""
Live Server
-----------

* runs server-side.
* listens on an SSL-secured socket for messages from live_collector
* imports log entries from live_client into database
* validates messages against keys before importing

"""

# create MemoryBuffer class to allow storing, counting, and removing lines
# unique storage comparments, unique per subscription/datasource
# Must support inter-thread locking based on subscription/datasource.
# dribble-written by server thread.
# read/erased by processor/importer thread.

# create processor/importer/something class
# runs a thread. checks mem buffer for any subscription/datasource combinations that are ripe
# lock, copy/move, erase, unlock memory buffer
# if a memory buffer is empty, lock it, remove it entirely, unlock it
# run importer and preprocessor on lines into appropriate subscription/datasource


# Self-signed certificate generation for testing:
# openssl req -new -x509 -days 365 -nodes -out cert.pem -keyout cert.pem

CERTIFICATE_FILE = "cert.pem"
HOST = "localhost"
PORT = 8081
SERVER = None
SERVER_THREAD = None
IMPORTER = None
IMPORTER_THREAD = None
# MEMORY_BUFFER = []
# MEMORY_BUFFER_LOCK = threading.Lock()
# SYSLOG_SIZE = 0
# SYSLOG_PROCESSING_QUOTE = 1000  # when the syslog has this many entries, process it.
# TIME_BETWEEN_IMPORTING = 1  # seconds. Check for and import lines into the syslog with this period.
# TIME_BETWEEN_PROCESSING = 20  # seconds. Process a partially-filled syslog with this period.
# SHUTDOWN_EVENT = threading.Event()


class Buffer:
    EMPTY = 0
    PARTIAL = 1
    FULL = 2

    EXPIRED = 4
    NOT_EXPIRED = 0

    TIMEOUT = 8

    SIZE_QUOTA = 1000  # log lines.  When the syslog has this many entries, process it.
    TIME_QUOTA = 20  # seconds. Process a partially-filled syslog with this period.


    def __init__(self, sub, ds):
        self.sub = sub
        self.ds = ds
        self.lines = []
        self.last_pop_time = time.time()
        self.expiring = self.NOT_EXPIRED
        self.lock = threading.Lock()

    def visit(self):
        code = (len(self.lines) + self.SIZE_QUOTA - 1) // self.SIZE_QUOTA
        code = code ^ ((2 ^ code) & -(2 < code))
        # code is now 0, 1, or 2 if the number of lines is 0, 1..SIZE_QUOTE, or >SIZE_QUOTA

        code |= self.expiring
        # sets the 3rd bit (EXPIRED) if the buffer is old.

        code |= int(time.time() > self.last_pop_time + self.TIME_QUOTA) << 3
        # sets the 4th bit (TIMEOUT) if the time quota is up

        return code

    def pop_all(self):
        lines = self.lines
        self.lines = []
        self.last_pop_time = time.time()
        return lines

    def add(self, lines):
        self.lines.extend(lines)
        self.expiring = self.EXPIRED * int(len(lines) != 0)

    def __str__(self):
        return "{0}-{1}-{2}".format(self.sub, self.ds, len(self.lines))

    def __repr__(self):
        return str(self)


class MemoryBuffers:
    def __init__(self):
        # each buffer needs a sub, ds, list-of-lines, and last_empty_time
        self.buffers = {}
        """:type : {int: {int: Buffer}}"""

    def create(self, sub, ds):
        sub_buffers = self.buffers.get(sub, {})
        sub_buffers[ds] = Buffer(sub, ds)
        self.buffers[sub] = sub_buffers

    def add(self, sub, ds, lines):
        # type: (int, int, [str]) -> None
        buffer = self.buffers.get(sub, {}).get(ds)
        if not buffer:
            self.create(sub, ds)
            buffer = self.buffers.get(sub, {}).get(ds)
        with buffer.lock:
            buffer.add(lines)

    def remove(self, sub, ds):
        # type: (int, int) -> None
        sub_buffer = self.buffers.get(sub)
        if sub_buffer:
            if ds in sub_buffer:
                del sub_buffer[ds]
            if not sub_buffer:
                del self.buffers[sub]

    def get_all(self):
        # type: () -> [Buffer]
        buffers = [v for sub in self.buffers.keys() for v in self.buffers[sub].values()]
        return buffers

    def yank(self, sub, ds):
        buffer = self.buffers.get(sub, {})[ds]
        with buffer.lock:
            lines = buffer.pop_all()
        return lines


class DatabaseInserter(threading.Thread):
    CYCLE_SLEEP = 1  # sleep period between buffer-checking cycles

    def __init__(self, buffers):
        threading.Thread.__init__(self)
        # type: (MemoryBuffers) -> None
        self.buffers = buffers
        self.alive = True
        self.e_shutdown = threading.Event()

    def run(self):
        while self.alive:

            # sleep, but watch for shutdown requests
            triggered = self.e_shutdown.wait(self.CYCLE_SLEEP)
            if triggered:
                self.alive = False

            buffers = self.buffers.get_all()
            for buffer in buffers:
                state = buffer.visit()

                # import any lines into Syslog
                if state & (Buffer.FULL | Buffer.PARTIAL):
                    self.buffer_to_syslog(buffer)

                if state & Buffer.FULL:
                    # process the buffer
                    self.syslog_to_tables(buffer)
                elif state & Buffer.TIMEOUT:
                    # process the buffer
                    self.syslog_to_tables(buffer)
                elif state & Buffer.EXPIRED:
                    # remove the buffer from the buffer list
                    self.buffers.remove(buffer.sub, buffer.ds)

    def shutdown(self):
        self.e_shutdown.set()

    def run_importer(self, sub, ds, messages):
        importer = importers.import_base.BaseImporter()
        importer.set_subscription(sub)
        importer.set_datasource(ds)

        for msg in messages:
            lines = msg['lines']
            headers = msg['headers']
            # lines is a list of rows, where each row is a list of values
            # headers is a list of column names
            # rows is a list of dictionaries where each dictionary is the headers applied to that row of data
            rows = [{headers[i]: v for i, v in enumerate(row)} for row in lines]
            importer.insert_data(rows, len(lines))

    def run_preprocessor(self, sub, ds):
        print("PREPROCESSOR: running syslog to tables for {0}: {1}".format(sub, ds))
        processor = preprocess.Preprocessor(common.db_quiet, sub, ds)
        rows = processor.count_syslog()
        if rows > 0:
            print("Processing {0} rows".format(rows))
            processor.run_all()
        else:
            print("Not processing. {0} rows".format(rows))

    def buffer_to_syslog(self, buffer):
        sub = buffer.sub
        ds = buffer.ds
        lines = self.buffers.yank(sub, ds)
        self.run_importer(sub, ds, lines)

    def syslog_to_tables(self, buffer):
        sub = buffer.sub
        ds = buffer.ds
        self.run_preprocessor(sub, ds)


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


class ConnectionHandler(SocketServer.StreamRequestHandler):
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
            print("CHRON: waiting for time limit or a full buffer.  Time at {0:.1f}, Size at {1}".format(deltatime,
                                                                                                         SYSLOG_SIZE))
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
    SERVER = SSL_ThreadingTCPServer((HOST, PORT), ConnectionHandler, CERTIFICATE_FILE)
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

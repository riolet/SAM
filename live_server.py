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
import models.livekeys

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
BUFFERS = None
# MEMORY_BUFFER = []
# MEMORY_BUFFER_LOCK = threading.Lock()
# SYSLOG_SIZE = 0
# SYSLOG_PROCESSING_QUOTE = 1000  # when the syslog has this many entries, process it.
# TIME_BETWEEN_IMPORTING = 1  # seconds. Check for and import lines into the syslog with this period.
# TIME_BETWEEN_PROCESSING = 20  # seconds. Process a partially-filled syslog with this period.
# SHUTDOWN_EVENT = threading.Event()


class Buffer:

    def __init__(self, sub, ds):
        self.sub = sub
        self.ds = ds
        self.messages = []
        self.last_pop_time = time.time()
        self.expiring = False
        self.lock = threading.Lock()

    def pop_all(self):
        messages = self.messages
        self.messages = []
        self.last_pop_time = time.time()
        return messages

    def add(self, message):
        self.messages.append(message)
        self.expiring = len(self.messages) > 0

    def __str__(self):
        return "{0}-{1}-{2}".format(self.sub, self.ds, len(self.messages))

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

    def add(self, sub, ds, message):
        # type: (int, int, [str]) -> None
        buffer = self.buffers.get(sub, {}).get(ds)
        if not buffer:
            self.create(sub, ds)
            buffer = self.buffers.get(sub, {}).get(ds)
        with buffer.lock:
            buffer.add(message)

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
    SIZE_QUOTA = 1000  # log lines.  When the syslog has this many entries, process it.
    TIME_QUOTA = 20  # seconds. Process a partially-filled syslog with this period.
    CYCLE_SLEEP = 1  # seconds. sleep period between buffer-checking cycles

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
                # import any lines into Syslog
                self.buffer_to_syslog(buffer)

                processor = preprocess.Preprocessor(common.db_quiet, buffer.sub, buffer.ds)
                rows = processor.count_syslog()

                if rows >= self.SIZE_QUOTA:
                    # process the buffer
                    self.syslog_to_tables(buffer)
                elif time.time() > buffer.last_pop_time + self.TIME_QUOTA:
                    if rows > 0:
                        # process the buffer
                        self.syslog_to_tables(buffer)
                    else:
                        if buffer.expiring:
                            # remove the buffer from the buffer list
                            self.buffers.remove(buffer.sub, buffer.ds)
                        else:
                            # flag the buffer as inactive for future removal
                            buffer.flag_expired()
                else:
                    # rows are under quota, and time is not up. Move on
                    pass

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
            translator.send("Failed: Error processing request.")
            return

        if self.data:
            success = self.socket_to_buffer(self.data)
        else:
            translator.send("Failed: No data.")
            return

        if success:
            translator.send("Success")
        else:
            translator.send("Failed: Error processing data.")

    def socket_to_buffer(self, data):
        global BUFFERS
        # read code
        code = data.pop('code', None)
        if not code:
            print("No access code. Denied")
            return False

        # translate/validate code in database
        key_model = models.livekeys.LiveKeys()
        access = key_model.validate(code)
        if not access:
            print("Access code not valid. Denied")
            return False
        sub = access['subscription']
        ds = access['datasource']

        # read lines/etc
        # insert lines into buffer
        BUFFERS.add(sub, ds, data)


def signal_handler(signal_number, stack_frame):
    print("\nInterrupt received.")
    shutdown()


def shutdown():
    global SERVER
    global IMPORTER
    global SERVER_THREAD

    print("Shutting down server.")
    SERVER.shutdown()
    if SERVER_THREAD:
        SERVER_THREAD.join()
        print("Handler stopped.")
    IMPORTER.shutdown()


def main():
    global CERTIFICATE_FILE
    global HOST
    global PORT
    global SERVER
    global SERVER_THREAD
    global IMPORTER
    global IMPORTER_THREAD
    global BUFFERS

    # register signals for safe shut down
    signal.signal(signal.SIGINT, signal_handler)

    # Create the buffers object
    BUFFERS = MemoryBuffers()

    # Start the daemon listening on the port in an infinite loop that exits when the program is killed
    SSL_TCPServer.allow_reuse_address = True
    SERVER = SSL_ThreadingTCPServer((HOST, PORT), ConnectionHandler, CERTIFICATE_FILE)
    SERVER_THREAD = threading.Thread(target=SERVER.serve_forever)
    SERVER_THREAD.start()

    # set up the importer
    IMPORTER = DatabaseInserter(BUFFERS)
    IMPORTER_THREAD = threading.currentThread()

    print("Live Server listening on {0}:{1}.".format(HOST, PORT))

    try:
        IMPORTER.run()
    except:
        traceback.print_exc()
        print("==>--<" * 10)
        shutdown()

    print("Server shut down successfully.")


if __name__ == "__main__":
    main()

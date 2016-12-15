import SocketServer
import threading
import signal
import time
import import_paloalto
import preprocess
import dbaccess

buffer_mutex = threading.Lock()
mem_buffer = []

syslog_size = 0
handler_server = None
handler_thread = None
shutdown_processor = threading.Event()
processor_thread = None
counter = 0


def thread_batch_processor():
    # loop:
    #    wait for event, with timeout
    #    check bufferSize
    #       conditionally swap buffers and do processing.
    global syslog_size
    global importer
    seconds_per_scan = 1
    max_time_between_processing = 20

    last_processing = time.time()  # time.time() is in floating point seconds
    alive = True
    while alive:
        triggered = shutdown_processor.wait(seconds_per_scan)
        if triggered:
            alive = False

        deltatime = time.time() - last_processing
        if syslog_size > 1000:
            print("CHRON: process server running batch (due to buffer cap reached)")
            preprocess_lines()
            last_processing = time.time()
        elif deltatime > max_time_between_processing and syslog_size > 0:
            print("CHRON: process server running batch (due to time)")
            preprocess_lines()
            last_processing = time.time()
        else:
            print("CHRON: waiting for time limit or a full buffer.  Time at {0:.1f}, Size at {1}".format(deltatime, syslog_size))

        # import lines in memory buffer:
        if len(mem_buffer) > 0:
            import_lines()

    print("CHRON: process server shutting down")


def store_lines(lines):
    global mem_buffer
    global buffer_mutex

    # acquire lock
    with buffer_mutex:
        # append line
        mem_buffer.extend(lines)
    # release lock


def import_lines():
    global mem_buffer
    global syslog_size
    global buffer_mutex

    with buffer_mutex:
        lines = mem_buffer
        mem_buffer = []

    settings = dbaccess.get_settings_cached()
    importer = import_paloalto.PaloAltoImporter()
    importer.datasource = settings['live_dest']
    print("IMPORTER: importing {0} lines to the Syslog. Syslog is now {1} lines".format(len(lines), len(lines) + syslog_size))
    importer.import_string("\n".join(lines))
    syslog_size += len(lines)


def preprocess_lines():
    global syslog_size
    print("PREPROCESSOR: preprocessing the syslog. ({0} lines)".format(syslog_size))
    settings = dbaccess.get_settings_cached()
    preprocess.preprocess_log(ds=settings['live_dest'])
    syslog_size = 0


# Request handler used to listen on the port
# Uses synchronous message processing as threading was causing database issues
class UDPRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        global buffer_size
        global buffer_id

        data = self.request[0].strip()
        lines = data.splitlines()
        store_lines(lines)


def signal_handler(signal_number, stack_frame):
    print("\nInterrupt received.")
    print("Shutting down handler.")
    handler_server.shutdown()
    if handler_thread:
        handler_thread.join()
        print("Handler stopped.")
    print("Shutting down batch processor.")
    shutdown_processor.set()
    if processor_thread:
        processor_thread.join()
        print("Processor stopped.")


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

    print("Live Update server listening on {0}:{1}.".format(HOST, PORT))

    thread_batch_processor()

    print("Server shut down successfully.")

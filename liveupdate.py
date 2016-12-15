import SocketServer
import threading
import signal
import time
import import_paloalto
import preprocess
import dbaccess

buffer_mutex = threading.Lock()
buffer_id = "A"
buffer_size = 0
handler_server = None
handler_thread = None
shutdown_processor = threading.Event()
processor_thread = None


def thread_batch_processor():
    # loop:
    #    wait for event, with timeout
    #    check bufferSize
    #       conditionally swap buffers and do processing.
    global buffer_size
    seconds_per_scan = 1
    max_time_between_processing = 20

    last_processing = time.time()  # time.time() is in floating point seconds
    alive = True
    while alive:
        triggered = shutdown_processor.wait(seconds_per_scan)
        if triggered:
            alive = False

        deltatime = time.time() - last_processing
        if buffer_size > 1000:
            print("CHRON: process server running batch (due to buffer cap reached)")
            preprocess_buffer()
            last_processing = time.time()
        elif deltatime > max_time_between_processing and buffer_size > 0:
            print("CHRON: process server running batch (due to time)")
            preprocess_buffer()
            last_processing = time.time()
        else:
            print("CHRON: waiting for time limit or a full buffer")

    print("CHRON: process server shutting down")


def preprocess_buffer():
    global buffer_id
    global buffer_size
    old_buffer_id = buffer_id
    process_old_buffer = False
    settings = dbaccess.get_settings_cached()

    buffer_mutex.acquire()
    print("PROCESS: buffer {0} size is {1}".format(buffer_id, buffer_size))
    try:
        if buffer_id == "A":
            buffer_id = "B"
        else:
            buffer_id = "A"
        buffer_size = dbaccess.get_syslog_size(settings['live_dest'], buffer_id)
        process_old_buffer = True
    except:
        print("PROCESS: hit an exception.")
    finally:
        buffer_mutex.release()

    if process_old_buffer:
        print("PROCESS: Actually running preprocess on buffer {0} of ds_{1}"
              .format(old_buffer_id, settings['live_dest']))
        preprocess.preprocess_log(suffix=old_buffer_id, ds=settings['live_dest'])


# Request handler used to listen on the port
# Uses synchronous message processing as threading was causing database issues
class UDPRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        global buffer_size
        global buffer_id
        data = self.request[0].strip()

        lines = data.splitlines()
        # palo Alto log translation
        importer = import_paloalto.PaloAltoImporter()
        settings = dbaccess.get_settings_cached()
        importer.datasource = settings['live_dest']
        importer.buffer = buffer_id
        if importer.datasource is None:
            # live updates are configured to be discarded
            return

        translated_lines = []
        for line in lines:
            result = {}
            r = importer.translate(line, 1, result)
            if r == 0:
                translated_lines.append(result)

        # this inserts into Syslog
        importer.insert_data(translated_lines, len(translated_lines))

        # update buffer stats
        buffer_mutex.acquire()
        try:
            buffer_size += len(translated_lines)
        finally:
            buffer_mutex.release()


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

    # choose which buffer to start with:
    size_a = dbaccess.get_syslog_size(dbaccess.get_settings_cached()['live_dest'], "A")
    size_b = dbaccess.get_syslog_size(dbaccess.get_settings_cached()['live_dest'], "B")
    if size_a > 0:
        buffer_id = "A"
        buffer_size = size_a
    elif size_b > 0:
        buffer_id = "B"
        buffer_size = size_b

    # Start the daemon listening on the port in an infinite loop that exits when the program is killed
    handler_thread = threading.Thread(target=handler_server.serve_forever)
    handler_thread.start()

    print("Live Update server listening on {0}:{1}.".format(HOST, PORT))

    thread_batch_processor()

    print("Server shut down successfully.")

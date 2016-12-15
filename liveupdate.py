import SocketServer
import socket
import sys
import os
import threading
import signal
import time
import import_paloalto
import preprocess
import dbaccess


bufferMutex = threading.Lock()
buffer = "A"
bufferSize = 0
handlerServer = None
handler_thread = None
shutdown_processor = threading.Event()
processor_thread = None

def thread_batch_processor():
    # loop:
    #    wait for event, with timeout
    #    check bufferSize
    #       conditionally swap buffers and do processing.
    global bufferSize
    seconds_per_scan = 1
    max_time_between_processing = 5

    last_processing = time.time()  # time.time() is in floating point seconds
    alive = True
    while alive:
        triggered = shutdown_processor.wait(seconds_per_scan)
        if triggered:
            alive = False

        deltatime = time.time() - last_processing
        if bufferSize > 1000:
            print("CHRON: process server running batch (due to buffer cap reached)")
            preprocess_buffer()
        elif (deltatime > max_time_between_processing and bufferSize > 0):
            print("CHRON: process server running batch (due to time)")
            preprocess_buffer()
        else:
            print("CHRON: waiting for time limit or a full buffer")

    print("CHRON: process server shutting down")


def preprocess_buffer():
    global buffer
    global bufferSize
    oldBuffer = buffer
    processOldBuffer = False
    settings = dbaccess.get_settings_cached()

    bufferMutex.acquire()
    print("PROCESS: buffer {0} size is {1}".format(buffer, bufferSize))
    try:
        if buffer == "A":
            buffer = "B"
        else:
            buffer = "A"
        bufferSize = dbaccess.get_syslog_size(settings['live_dest'], buffer)
        processOldBuffer = True
    except:
        print("PROCESS: hit an exception.")
    finally:
        bufferMutex.release()

    if processOldBuffer:
        print("PROCESS: Actually running preprocess on buffer {0} of ds_{1}".format(oldBuffer, settings['live_dest']))
        preprocess.preprocess_log(suffix=oldBuffer, ds=settings['live_dest'])


#Request handler used to listen on the port
#Uses synchronous message processing as threading was causing database issues
class UDPRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        global bufferSize
        global buffer
        data = self.request[0].strip()
        ### get port number
        port = self.client_address[1]
        ### get the communicate socket
        socket = self.request[1]
        ### get client host ip address
        client_address = (self.client_address[0])

        ### assemble a response message to client
        response = "%s"%(data)
        socket.sendto(data.upper(), self.client_address)

        lines = data.splitlines()
        # palo Alto log translation
        importer = import_paloalto.PaloAltoImporter()
        settings = dbaccess.get_settings_cached()
        importer.datasource = settings['live_dest']
        importer.buffer = buffer
        if importer.datasource == None:
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

        #update buffer stats
        bufferMutex.acquire()
        try:
            bufferSize += len(translated_lines)
        finally:
            bufferMutex.release()


def signal_handler(signal, frame):
    print("\nCtrl-C received.")
    print("Shutting down handler.")
    handlerServer.shutdown()
    if handler_thread:
        handler_thread.join()
        print("Handler stopped.")
    print("Shutting down batch processor.")
    shutdown_processor.set()
    if processor_thread:
        processor_thread.join()
        print("Processor stopped.")

if __name__ == "__main__":
    #Port and host to listen from
    HOST, PORT = "localhost", 514

    # register signals for safe shut down
    signal.signal(signal.SIGINT, signal_handler)
    handlerServer = SocketServer.UDPServer((HOST, PORT), UDPRequestHandler)
    ip, port = handlerServer.server_address

    # choose which buffer to start with:
    size_a = dbaccess.get_syslog_size(dbaccess.get_settings_cached()['live_dest'], "A")
    size_b = dbaccess.get_syslog_size(dbaccess.get_settings_cached()['live_dest'], "B")
    if size_a > 0:
        buffer = "A"
        bufferSize = size_a
    elif size_b > 0:
        buffer = "B"
        bufferSize = size_b

    # Start the daemon listening on the port in an infinite loop that exits when the program is killed
    handler_thread = threading.Thread(target=handlerServer.serve_forever)
    handler_thread.start()

    print("Live Update server listening on {0}:{1}.".format(HOST, PORT))

    thread_batch_processor()

    print("Server shut down successfully.")

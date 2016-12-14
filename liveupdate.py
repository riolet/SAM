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
buffer = 'A'
bufferSize = 0

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
        oldBuffer = buffer
        processOldBuffer = False

        bufferMutex.acquire()
        try:
            bufferSize += len(translated_lines)
            if bufferSize > 1000:
                bufferSize = 0
                if buffer == "A":
                    buffer = "B"
                else:
                    buffer = "A"
                processOldBuffer = True
        finally:
            bufferMutex.release()

        if processOldBuffer:
            preprocess.preprocess_log(oldBuffer)

def signal_handler(signal, frame):
    sys.exit(0)

if __name__ == "__main__":
    #Port and host to listen from
    HOST, PORT = "localhost", 514

    signal.signal(signal.SIGINT, signal_handler)
    server = SocketServer.UDPServer((HOST, PORT), UDPRequestHandler)
    ip, port = server.server_address

    #Keeps the daemon listening on the port in an infinite loop that exits when the program is killed
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()
    while (True):
        time.sleep(24*60*60);

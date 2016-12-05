import SocketServer
import socket
import sys
import os
import threading
import signal
import time
import import_paloalto
import preprocess

#Request handler used to listen on the port
#Uses synchronous message processing as threading was causing database issues
class UDPRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
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
        translated_lines = []
        for line in lines:
            result = {}
            r = importer.translate(line, 1, result)
            if r == 0:
                translated_lines.append(result)

                """ this code is not fully developed (supposed to process data after 1000 imports)
        while (counter < 1000):
            counter = counter + 1
            lines = data.splitlines()
            # palo Alto log translation
            importer = import_paloalto.PaloAltoImporter()
            translated_lines = []
            for line in lines:
                result = {}
                r = importer.translate(line, 1, result)
                if r == 0:
                    translated_lines.append(result)
"""

        # this inserts into Syslog
        importer.insert_data(translated_lines, len(translated_lines))
        # Invoke the preprocessing to import data from Syslog into Noes and Links tables
        preprocess.preprocess_log()

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

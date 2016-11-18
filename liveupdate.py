import SocketServer
import socket
import sys
import os
import threading
import signal
import time

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

        #creates a file based off of the data passed through
        textFile = open("syslog_file.txt", "wr")
        textFile.write(data)
        textFile.close()
        os.system("python2 import_paloalto.py syslog_file.txt")
        os.system("python2 preprocess.py")

def signal_handler(signal, frame):
    sys.exit(0)

if __name__ == "__main__":
    HOST, PORT = "localhost", 514

    signal.signal(signal.SIGINT, signal_handler)
    server = SocketServer.UDPServer((HOST, PORT), UDPRequestHandler)
    ip, port = server.server_address

    #server.serve_forever()
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()
    while (True):
        time.sleep(24*60*60);
    #server.shutdown()

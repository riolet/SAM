import SocketServer
import threading
import signal
import traceback

buffer_mutex = threading.Lock()
mem_buffer = []

syslog_size = 0
handler_server = None
handler_thread = None
shutdown_processor = threading.Event()


class TCPRequestHandler_stream(SocketServer.StreamRequestHandler):
    def handle(self):
        # self.rfile is a file-like object created by the handler;
        # we can now use e.g. readline() instead of raw recv() calls
        self.data = self.rfile.readline().strip()
        print("{} wrote:".format(self.client_address[0]))
        print(self.data)
        # Likewise, self.wfile is a file-like object used to write back
        # to the client
        self.wfile.write("Thanks for {0}".format(self.data.upper()))


class TCPRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        # self.rfile is a file-like object created by the handler;
        # we can now use e.g. readline() instead of raw recv() calls
        print("SERVER: Handling input!")
        #self.data = self.request.recv(10).strip()
        self.data = receive_message(self.request)
        for line in self.data.splitlines():
            print("\t: {0}".format(line))
        # Likewise, self.wfile is a file-like object used to write back
        # to the client
        send_message(self.request, self.data.upper())
        #self.request.sendall(self.data.upper())


def signal_handler(signal_number, stack_frame):
    print("\nInterrupt received.")
    shutdown()


def shutdown():
    print("Shutting down handler.")
    handler_server.shutdown()
    if handler_thread:
        handler_thread.join()
        print("Handler stopped.")
    print("Shutting down server.")
    shutdown_processor.set()


def send_message(sock, msg):
    l = len(msg)
    m = "{0:05d}{1}".format(l, msg)
    sock.sendall(m)


def receive_message(sock):
    chars = ""
    while len(chars) < 5:
        chars += sock.recv(1)
    length = int(chars[:5])

    message = chars[5:]
    while len(message) < length:
        message += sock.recv(10)
    return message


if __name__ == "__main__":
    # Port and host to listen from
    HOST, PORT = "localhost", 8081

    # register signals for safe shut down
    signal.signal(signal.SIGINT, signal_handler)
    handler_server = SocketServer.TCPServer((HOST, PORT), TCPRequestHandler)
    ip, port = handler_server.server_address

    # Start the daemon listening on the port in an infinite loop that exits when the program is killed
    handler_thread = threading.Thread(target=handler_server.serve_forever)
    handler_thread.start()

    print("Live Update server listening on {0}:{1}.".format(HOST, PORT))

    try:
        alive = True
        while alive:
            if shutdown_processor.wait(5):
                print("Server stopping.")
                alive = False
    except:
        traceback.print_exc()
        print("==>--<" * 10)
        shutdown()

    print("Server shut down successfully.")

import SocketServer
import threading
import traceback
import signal
import ssl
import time
import live_protocol


# Certificate Generation:
# openssl req -new -x509 -days 365 -nodes -out cert.pem -keyout cert.pem
CERTIFICATE_FILE = "cert.pem"
HOST = "localhost"
PORT = 8081
SERVER = None
SERVER_THREAD = None
ALIVE = True
PASSCODE = b'not-so-secret-passcode'


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
        translator = live_protocol.LiveProtocol(self.connection, password=PASSCODE)
        self.data = None
        try:
            transmission = translator.receive()
            self.data = translator.decode(transmission)
        except live_protocol.PasswordError as e:
            print(e.message)
            translator.send("Password Error")
        except:
            traceback.print_exc()
            translator.send("Error processing request")

        if self.data:
            for line in self.data.splitlines():
                print("\t: {0}".format(line))
            translator.send(self.data.upper())


def signal_handler(signal_number, stack_frame):
    print("\nInterrupt received.")
    shutdown()


def shutdown():
    global SERVER
    global SERVER_THREAD
    global ALIVE

    print("Shutting down server.")
    SERVER.shutdown()
    if SERVER_THREAD:
        SERVER_THREAD.join()
        print("Handler stopped.")
    ALIVE=False

def main():
    global SERVER
    global SERVER_THREAD
    global ALIVE
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

    print("Live Update server listening on {0}:{1}.".format(HOST, PORT))

    try:
        while ALIVE:
            time.sleep(1)
    except:
        traceback.print_exc()
        print("==>--<" * 10)
        shutdown()

    print("Server shut down successfully.")


if __name__ == "__main__":
    main()

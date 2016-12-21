import SocketServer
import threading
import traceback
import ssl

# Certificate Generation:
# openssl req -new -x509 -days 365 -nodes -out cert.pem -keyout cert.pem
CERTIFICATE_FILE = "cert.pem"
HOST = "localhost"
PORT = 8081


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


class MySSL_TCPServer(SocketServer.TCPServer):
    def __init__(self,
                 server_address,
                 RequestHandlerClass,
                 certfile,
                 ssl_version=ssl.PROTOCOL_TLSv1_2,
                 bind_and_activate=True):
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass, bind_and_activate)
        self.certfile = certfile
        self.ssl_version = ssl_version

    def get_request(self):
        newsocket, fromaddr = self.socket.accept()
        connstream = ssl.wrap_socket(newsocket,
                                 server_side=True,
                                 certfile = self.certfile,
                                 ssl_version = self.ssl_version)
        return connstream, fromaddr


class MySSL_ThreadingTCPServer(SocketServer.ThreadingMixIn, MySSL_TCPServer): pass


class testHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        print("SERVER: Handling input!")
        self.data = receive_message(self.connection)
        for line in self.data.splitlines():
            print("\t: {0}".format(line))
        # Likewise, self.wfile is a file-like object used to write back
        # to the client
        send_message(self.connection, self.data.upper())



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

    MySSL_TCPServer.allow_reuse_address=True
    my_server = MySSL_ThreadingTCPServer((HOST, PORT), testHandler, CERTIFICATE_FILE)

    print("Live Update server listening on {0}:{1}.".format(HOST, PORT))

    try:
        my_server.serve_forever()
    except KeyboardInterrupt:
        print("\nInterrupt encountered. Shutting down.")
        my_server.shutdown()
        my_server.socket.close()
        my_server.server_close()
    except:
        traceback.print_exc()
        print("==>--<" * 10)
    finally:
        if my_server:
            my_server.server_close()
    print("Server shut down successfully.")

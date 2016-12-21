from SocketServer import TCPServer, ThreadingMixIn, StreamRequestHandler
import ssl

class MySSL_TCPServer(TCPServer):
    def __init__(self,
                 server_address,
                 RequestHandlerClass,
                 certfile,
                 ssl_version=ssl.PROTOCOL_TLSv1_2,
                 bind_and_activate=True):
        TCPServer.__init__(self, server_address, RequestHandlerClass, bind_and_activate)
        self.certfile = certfile
        self.ssl_version = ssl_version

    def get_request(self):
        newsocket, fromaddr = self.socket.accept()
        connstream = ssl.wrap_socket(newsocket,
                                 server_side=True,
                                 certfile = self.certfile,
                                 ssl_version = self.ssl_version)
        return connstream, fromaddr

class MySSL_ThreadingTCPServer(ThreadingMixIn, MySSL_TCPServer): pass

class testHandler(StreamRequestHandler):
    def handle(self):
        data = self.connection.recv(4096)
        self.wfile.write(data)
#test code
MySSL_ThreadingTCPServer(('127.0.0.1',5151),testHandler,"cert.pem").serve_forever()
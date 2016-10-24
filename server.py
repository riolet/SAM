import SocketServer
import socket
import sys
import os
import threading
import signal
sys.path.append(os.path.dirname(__file__))
import web

class ThreadedUDPRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        ### get port number
        port = self.client_address[1]
        ### get the communicate socket
        socket = self.request[1]
        ### get client host ip address
        client_address = (self.client_address[0])
        ### proof of multithread
        cur_thread = threading.current_thread()
        print "thread %s" %cur_thread.name
        print "received call from client address :%s" %client_address
        print "received data from port [%s]: %s" %(port,data)

        ### assemble a response message to client
        response = "%s %s"%(cur_thread.name, data)
        socket.sendto(data.upper(), self.client_address)

class ThreadedUDPServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    pass

def signal_handler(signal, frame):
    sys.exit(0)

# web.config.debug = False

# Manage routing from here. Regex matches URL and chooses class by name
urls = (
    # '/', 'pages.overview.Overview',  # matched groups (in parens) are sent as arguments
    '/', 'pages.map.Map',  # Omit the overview page and go straight to map (no content in overview anyway)
    '/overview', 'pages.overview.Overview',
    '/map', 'pages.map.Map',
    '/stats', 'pages.stats.Stats',
    '/nodes', 'pages.nodes.Nodes',
    '/links', 'pages.links.Links',
    '/details', 'pages.details.Details',
    '/details/(.+)', 'pages.details.Details',
    '/portinfo', 'pages.portinfo.Portinfo',
    '/nodeinfo', 'pages.nodeinfo.Nodeinfo',
    '/metadata', 'pages.metadata.Metadata',
    '/table', 'pages.table.Table',
)

# For development testing, uncomment these 3 lines
if __name__ == "__main__":
    HOST, PORT = "localhost", 514

    signal.signal(signal.SIGINT, signal_handler)
    server = ThreadedUDPServer((HOST, PORT), ThreadedUDPRequestHandler)
    ip, port = server.server_address

    #server.serve_forever()
    # Start a thread with the server --
    # that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()

    app = web.application(urls, globals())
    app.run()
    
    server.shutdown()

# For apache2 mod_wsgi deployment, uncomment these two lines
# app = web.application(urls, globals(), autoreload=False)
# application = app.wsgifunc()

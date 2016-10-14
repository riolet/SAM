import socket
import time
import threading
import sys
import signal

data = "{\"message\":\"1,2016/06/21 18:06:27,0009C100218,TRAFFIC,end,1,2016/06/21 18:06:27,189.49.111.232,21.66.242.207,0.0.0.0,0.0.0.0,Allow export to Syslog,,,netbios-ns,vsys1,TAP-T0000R021,TAP-T0000R021,ethernet1/3,ethernet1/3,Copy Traffic Logs to Syslog,2016/06/21 18:06:27,34485576,1,137,137,0,0,0x19,udp,allow,220,220,0,3,2016/06/21 18:05:51,33,any,0,945712,0x0,189.0.0.0-189.255.255.255,US,0,3,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy\",\"@version\":\"1\",\"@timestamp\":\"2016-06-22T01:06:27.000Z\",\"host\":\"79.35.77.216\",\"priority\":14,\"timestamp\":\"Jun 21 18:06:27\",\"logsource\":\"Palo-Alto-Networks\",\"severity\":6,\"facility\":1,\"facility_label\":\"user-level\",\"severity_label\":\"Informational\"}"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

if (len(sys.argv) < 2):
    numThreads = 3
else:
    numThreads = int(sys.argv[1])


def sendData():
    while(True):
        sock.sendall(data + "\n")
        time.sleep(1)

def signal_handler(signal, frame):
    sys.exit(0)

try:
    # Connect to server and send data
    sock.connect(("localhost", 514))
    signal.signal(signal.SIGINT, signal_handler)

    for i in range(numThreads):
        thr = threading.Thread(target=sendData)
        thr.daemon = True
        thr.start()

    while(True):
        time.sleep(60*60*24)

finally:
    sock.close()


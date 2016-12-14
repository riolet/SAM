import socket
import time
import threading
import sys
import signal


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#define number of threads to use for stress testing
if len(sys.argv) < 2:
    numThreads = 1
else:
    numThreads = int(sys.argv[1])

#Plays back the data based on the relative differences between the timestamps
def playback_data(path, speed):
    # speed relative to realtime
    delay_multiplier = 1.0 / speed
    # open file for playback
    with open(path, 'rb') as syslog:
        line = syslog.readline()
        line_time_string = line[25:33]
        last_time = line_time = time.strptime(line_time_string, "%H:%M:%S")
        yield line
        for line in syslog:
            # sleep for the duration of the pause between log lines, to "playback" in real time
            line_time_string = line[25:33]
            line_time = time.strptime(line_time_string, "%H:%M:%S")
            if line_time != last_time:
                delay = (time.mktime(line_time) - time.mktime(last_time)) * delay_multiplier
                #time.sleep(delay) # this lines causes are error to occur at the 45 min mark when running SAM
                time.sleep(0.5) # this line does not cause error but we should be using delay instead of 0.5 
                last_time = line_time
            yield line
    return


def send_data():
    player = playback_data("../data/syslog_garbled", 1.0)
    for message in player:
        sock.sendall(message)
        # time.sleep(7)


def signal_handler(sig, frame):
    sys.exit(0)

try:
    # Connect to server and send data
    sock.connect(("localhost", 514))
    signal.signal(signal.SIGINT, signal_handler)

    for i in range(numThreads):
        thr = threading.Thread(target=send_data)
        thr.daemon = True
        thr.start()

    while True:
        time.sleep(60*60*24)

finally:
    sock.close()


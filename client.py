import socket
import time
import threading
import sys
import signal

#dataArr = [
 #   "{\"message\":\"1,2016/06/21 18:06:27,0009C100218,TRAFFIC,end,1,2016/06/21 18:06:27,21.66.94.6,79.35.64.113,0.0.0.0,0.0.0.0,Allow export to Syslog,,,snmp-base,vsys1,TAP-T0000R022,TAP-T0000R022,ethernet1/4,ethernet1/4,Copy Traffic Logs to Syslog,2016/06/21 18:06:27,34190678,1,161,59491,0,0,0x100050,udp,allow,183,183,0,1,2016/06/21 18:05:54,30,any,0,945786,0x0,US,79.179.0.0-79.119.255.255,0,1,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy\",\"@version\":\"1\",\"@timestamp\":\"2016-06-22T01:06:27.000Z\",\"host\":\"79.35.77.216\",\"priority\":14,\"timestamp\":\"Jun 21 18:06:27\",\"logsource\":\"Palo-Alto-Networks\",\"severity\":6,\"facility\":1,\"facility_label\":\"user-level\",\"severity_label\":\"Informational\"}\n{\"message\":\"1,2016/06/21 18:06:27,0009C100218,TRAFFIC,end,1,2016/06/21 18:06:27,21.66.218.234,21.66.10.55,0.0.0.0,0.0.0.0,Allow export to Syslog,,,incomplete,vsys1,TAP-T0000R022,TAP-T0000R022,ethernet1/4,ethernet1/4,Copy Traffic Logs to Syslog,2016/06/21 18:06:27,33918797,1,39655,26307,0,0,0x19,tcp,allow,2879,2879,0,9,2016/06/21 17:06:24,3600,any,0,945787,0x0,US,US,0,9,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy\",\"@version\":\"1\",\"@timestamp\":\"2016-06-22T01:06:27.000Z\",\"host\":\"79.35.77.216\",\"priority\":14,\"timestamp\":\"Jun 21 18:06:27\",\"logsource\":\"Palo-Alto-Networks\",\"severity\":6,\"facility\":1,\"facility_label\":\"user-level\",\"severity_label\":\"Informational\"}",
  #  "{\"message\":\"1,2016/06/21 18:06:27,0009C100218,TRAFFIC,end,1,2016/06/21 18:06:27,21.66.40.63,79.35.146.97,0.0.0.0,0.0.0.0,Allow export to Syslog,,,incomplete,vsys1,TAP-T0000R021,TAP-T0000R021,ethernet1/3,ethernet1/3,Copy Traffic Logs to Syslog,2016/06/21 18:06:27,360655,1,34133,9003,0,0,0x19,tcp,allow,1892,1892,0,11,2016/06/21 17:06:24,3600,any,0,945783,0x0,US,79.179.0.0-79.119.255.255,0,11,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy\",\"@version\":\"1\",\"@timestamp\":\"2016-06-22T01:06:27.000Z\",\"host\":\"79.35.77.216\",\"priority\":14,\"timestamp\":\"Jun 21 18:06:27\",\"logsource\":\"Palo-Alto-Networks\",\"severity\":6,\"facility\":1,\"facility_label\":\"user-level\",\"severity_label\":\"Informational\"}\n{\"message\":\"1,2016/06/21 18:06:27,0009C100218,TRAFFIC,end,1,2016/06/21 18:06:27,21.66.40.32,79.229.19.249,0.0.0.0,0.0.0.0,Allow export to Syslog,,,ping,vsys1,TAP-T0000R022,TAP-T0000R022,ethernet1/4,ethernet1/4,Copy Traffic Logs to Syslog,2016/06/21 18:06:27,245351,1,0,0,0,0,0x100019,icmp,allow,74,74,0,1,2016/06/21 18:06:15,0,any,0,945784,0x0,US,79.179.0.0-79.119.255.255,0,1,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy\",\"@version\":\"1\",\"@timestamp\":\"2016-06-22T01:06:27.000Z\",\"host\":\"79.35.77.216\",\"priority\":14,\"timestamp\":\"Jun 21 18:06:27\",\"logsource\":\"Palo-Alto-Networks\",\"severity\":6,\"facility\":1,\"facility_label\":\"user-level\",\"severity_label\":\"Informational\"}",
  #  "{\"message\":\"1,2016/06/21 18:06:27,0009C100218,TRAFFIC,end,1,2016/06/21 18:06:27,79.229.180.169,21.66.81.57,0.0.0.0,0.0.0.0,Allow export to Syslog,,,netbios-ns,vsys1,TAP-T0000R021,TAP-T0000R021,ethernet1/3,ethernet1/3,Copy Traffic Logs to Syslog,2016/06/21 18:06:27,80266,1,137,137,0,0,0x19,udp,allow,253,253,0,1,2016/06/21 18:05:54,30,any,0,945781,0x0,79.179.0.0-79.119.255.255,US,0,1,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy\",\"@version\":\"1\",\"@timestamp\":\"2016-06-22T01:06:27.000Z\",\"host\":\"79.35.77.216\",\"priority\":14,\"timestamp\":\"Jun 21 18:06:27\",\"logsource\":\"Palo-Alto-Networks\",\"severity\":6,\"facility\":1,\"facility_label\":\"user-level\",\"severity_label\":\"Informational\"}\n{\"message\":\"1,2016/06/21 18:06:27,0009C100218,TRAFFIC,end,1,2016/06/21 18:06:27,189.146.31.133,21.66.192.80,0.0.0.0,0.0.0.0,Allow export to Syslog,,,incomplete,vsys1,TAP-T0000R021,TAP-T0000R021,ethernet1/3,ethernet1/3,Copy Traffic Logs to Syslog,2016/06/21 18:06:27,265978,1,64533,443,0,0,0x19,tcp,allow,20009,20009,0,30,2016/06/21 17:06:24,3600,any,0,945782,0x0,189.0.0.0-189.255.255.255,US,0,30,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy\",\"@version\":\"1\",\"@timestamp\":\"2016-06-22T01:06:27.000Z\",\"host\":\"79.35.77.216\",\"priority\":14,\"timestamp\":\"Jun 21 18:06:27\",\"logsource\":\"Palo-Alto-Networks\",\"severity\":6,\"facility\":1,\"facility_label\":\"user-level\",\"severity_label\":\"Informational\"}"] 


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
                time.sleep(delay)
                last_time = line_time
            yield line
    return


def send_data():
    player = playback_data("./data/syslog_garbled", 1.0)
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


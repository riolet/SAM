import sys
from import_base import BaseImporter
from datetime import datetime
import time


class TCPDumpImporter(BaseImporter):
    def translate(self, line, line_num, dictionary):
        """
        Converts a given syslog line into a dictionary of (ip, port, ip, port)
        Args:
            line: The syslog line to parse
            line_num: The line number, for error printouts
            dictionary: The dictionary to write key/values pairs into

        Returns:
            0 on success and non-zero on error.
        """

        # from running sudo tcpdump -i eno1 -f --immediate-mode -l -n -Q inout -tt
        # 1491525947.515414 STP 802.1d, Config, Flags [none], bridge-id 8000.f8:32:e4:af:0a:a8.8001, length 43
        # 1491525947.915376 ARP, Request who-has 192.168.10.106 tell 192.168.10.254, length 46
        # 1491525948.268015 IP 192.168.10.113.33060 > 172.217.3.196.443: Flags [P.], seq 256:730, ack 116, win 3818, options [nop,nop,TS val 71847613 ecr 4161606244], length 474
        # 1491525737.317942 IP 192.168.10.254.55943 > 239.255.255.250.1900: UDP, length 449
        a = line.split()
        try:
            timestamp = datetime.fromtimestamp(float(a[0]))
        except:
            timestamp = datetime.fromtimestamp(time.time())

        try:
            src_ip_port = a[2].split(".")
            src_port = src_ip_port.pop()
            dst_ip_port = a[4].split(".")
            dst_port = dst_ip_port.pop()

            protocol = 'TCP'
            if a[5].startswith('UDP'):
                protocol = 'UDP'

            if a[-2] == 'length':
                try:
                    nBytes = int(a[-1])
                except:
                    nBytes = 1
            else:
                nBytes = 1

            dictionary['src'] = self.ip_to_int(*src_ip_port)
            dictionary['srcport'] = int(src_port)
            dictionary['dst'] = self.ip_to_int(*dst_ip_port)
            dictionary['dstport'] = int(dst_port.strip(":"))
            dictionary['timestamp'] = timestamp
            dictionary['protocol'] = protocol
            dictionary['duration'] = '1'
            dictionary['bytes_received'] = '0'
            dictionary['bytes_sent'] = nBytes
            dictionary['packets_received'] = '0'
            dictionary['packets_sent'] = '1'
        except:
            return 1
        return 0


_class = TCPDumpImporter

# If running as a script, begin by executing main.
if __name__ == "__main__":
    importer = _class()
    importer.main(sys.argv)

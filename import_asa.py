import sys
import re
import common
from import_base import BaseImporter
import time


# This implementation is incomplete:
# TODO: validate implementation with test data
# TODO: verify protocol is TCP
# TODO: parse timestamp into dictionary['Timestamp']

class ASAImporter(BaseImporter):
    def translate(self, line, line_num, dictionary):
        """
        Converts a given syslog line into a dictionary of (ip, port, ip, port)
        Args:
            line: The syslog line to parse
            line_num: The line number, for error printouts
            dictionary: The dictionary to write key/values pairs into

        Returns:
            0 on success and non-zero on error.
            1 => The protocol wasn't TCP and was ignored.
            2 => error in parsing the line. It was too short for some reason
        """
        # regexp to extract from ASA syslog
        regexp = r"^.* Built (?P<asa_in_out>in|out)bound (?P<asa_protocol>.*) connection (?P<asa_conn_id>\d+) for (?P<asa_src_zone>.*):(?P<asa_src_ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/(?P<asa_src_port>\d+) \(.*/\d+\) to (?P<asa_dst_zone>.*):(?P<asa_dst_ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/(?P<asa_dst_port>\d+) .*"
        m = re.match(regexp, line)

        if m:
            # srcIP, srcPort, dstIP, dstPort
            # The order of the source and destination depends on the direction, i.e., inbound or outbound
            if m.group('asa_in_out') == 'in':
                dictionary['SourceIP'] = common.IPtoInt(*(m.group('asa_src_ip').split(".")))
                dictionary['SourcePort'] = m.group('asa_src_port')
                dictionary['DestinationIP'] = common.IPtoInt(*(m.group('asa_dst_ip').split(".")))
                dictionary['DestinationPort'] = m.group('asa_dst_port')
            else:
                dictionary['DestinationIP'] = common.IPtoInt(*(m.group('asa_src_ip').split(".")))
                dictionary['DestinationPort'] = m.group('asa_src_port')
                dictionary['SourceIP'] = common.IPtoInt(*(m.group('asa_dst_ip').split(".")))
                dictionary['SourcePort'] = m.group('asa_dst_port')

            # ASA logs don't always have a timestamp. If your logs do, you may want to edit the line below to parse it.

            dictionary['Timestamp'] = time.strftime(self.mysql_time_format, time.localtime())
            return 0
        else:
            print("error parsing line {0}: {1}".format(line_num, line))
            return 2


# If running as a script, begin by executing main.
if __name__ == "__main__":
    importer = ASAImporter()
    importer.main(sys.argv)

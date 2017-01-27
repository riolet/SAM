import re
import sys

import dateutil.parser

import common
from import_base import BaseImporter
import datetime


# This implementation is incomplete:
# TODO: validate implementation with test data
# TODO: verify protocol is TCP
# TODO: parse timestamp into dictionary['Timestamp']


class AWSImporter(BaseImporter):
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
        # if line_num == 0:
        #     return 0

        a = line.split()

        dt = dateutil.parser.parse(a[0])
        src_ip_port = a[2].split(".")
        src_port = src_ip_port.pop()
        dst_ip_port = a[4].split(".")
        dst_port = dst_ip_port.pop()

        dictionary['Timestamp'] = dt.strftime(self.mysql_time_format)

        dictionary['SourceIP'] = common.IPtoInt(*src_ip_port)
        dictionary['SourcePort'] = int(src_port)

        dictionary['DestinationIP'] = common.IPtoInt(*dst_ip_port)
        dictionary['DestinationPort'] = int(dst_port.strip(":"))

        return 0


# If running as a script, begin by executing main.
if __name__ == "__main__":
    importer = AWSImporter()
    importer.main(sys.argv)

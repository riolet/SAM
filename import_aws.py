import sys
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
        awsLog = line.split(" ")

        dictionary['SourceIP'] = common.IPtoInt(*(awsLog[3].split(".")))
        dictionary['SourcePort'] = awsLog[5]
        dictionary['DestinationIP'] = common.IPtoInt(*(awsLog[4].split(".")))
        dictionary['DestinationPort'] = awsLog[6]
        dictionary['Timestamp'] = datetime.datetime.fromtimestamp((int(awsLog[10]))).strftime(self.mysql_time_format)
        return 0


# If running as a script, begin by executing main.
if __name__ == "__main__":
    importer = AWSImporter()
    importer.main(sys.argv)
import sys
from sam.importers.import_base import BaseImporter
import datetime


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

        dictionary['src'] = self.ip_to_int(*(awsLog[3].split(".")))
        dictionary['srcport'] = awsLog[5]
        dictionary['dst'] = self.ip_to_int(*(awsLog[4].split(".")))
        dictionary['dstport'] = awsLog[6]
        dictionary['timestamp'] = datetime.datetime.fromtimestamp((int(awsLog[10]))).strftime(self.mysql_time_format)

        # TODO: the following is placeholder.
        #       Needed: test data or spec to read
        dictionary['protocol'] = 'TCP'.upper()
        dictionary['duration'] = '1'
        dictionary['bytes_received'] = '1'
        dictionary['bytes_sent'] = '1'
        dictionary['packets_received'] = '1'
        dictionary['packets_sent'] = '1'
        return 0


_class = AWSImporter

# If running as a script, begin by executing main.
if __name__ == "__main__":
    sys.stderr.write("Warning: This importer is incomplete and uses empty data for some fields.")
    importer = _class()
    importer.main(sys.argv)

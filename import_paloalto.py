import json
import sys
import common
from import_base import BaseImporter
from datetime import datetime


class PaloAltoImporter(BaseImporter):
    def translate(self, line, line_num, dictionary):
        """
        Converts a given syslog line into a dictionary of (ip, port, ip, port, timestamp)
        Args:
            line: The syslog line to parse
            line_num: The line number, for error printouts
            dictionary: The dictionary to write key/values pairs into

        Returns:
            0 on success and non-zero on error.
            1 => ignoring a message that isn't network "TRAFFIC"
            2 => error in parsing the line. It was too short for some reason
            3 => The protocol wasn't TCP and was ignored.
        """
        data = json.loads(line)['message']
        # TODO: this assumes the data will not have any commas embedded in strings
        split_data = data.split(',')

        if split_data[3] != "TRAFFIC":
            print("Line {0}: Ignoring non-TRAFFIC entry (was {1})".format(line_num, split_data[3]))
            return 1
        if len(split_data) < 29:
            print("error parsing line {0}: {1}".format(line_num, line))
            return 2
        # 29 is protocol: tcp, udp, ...
        # TODO: don't ignore everything but TCP
        if split_data[29] != 'tcp':
            # printing this is very noisy and slow
            # print("Line {0}: Ignoring non-TCP entry (was {1})".format(lineNum, split_data[29]))
            return 3

        # srcIP, srcPort, dstIP, dstPort
        dictionary['SourceIP'] = common.IPtoInt(*(split_data[7].split(".")))
        dictionary['SourcePort'] = split_data[24]
        dictionary['DestinationIP'] = common.IPtoInt(*(split_data[8].split(".")))
        dictionary['DestinationPort'] = split_data[25]
        dictionary['Timestamp'] = datetime.strptime(split_data[1], "%Y/%m/%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
        return 0


# If running as a script, begin by executing main.
if __name__ == "__main__":
    importer = PaloAltoImporter()
    importer.main(sys.argv)

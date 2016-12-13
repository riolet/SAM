import sys
import os
import subprocess
import shlex
import common
from import_base import BaseImporter
from datetime import datetime


class NFDumpImporter(BaseImporter):
    def __init__(self):
        BaseImporter.__init__(self)
        self.instructions = """
This program imports a nfdump into the MySQL database.  The file must be binary data from nfcapd.
It extracts IP addresses and ports and discards other data. Only TCP traffic data is imported.

Usage:
    python {0} <input-file>
""".format(sys.argv[0])

    def import_file(self, path_in):
        # Assume a binary file as input
        args = shlex.split('nfdump -r {0} -o "fmt:%pr,%sa,%sp,%da,%dp,%byt,%bps,%ts"'.format(path_in))
        proc = subprocess.Popen(args, bufsize=-1, stdout=subprocess.PIPE)


        line_num = -1
        lines_inserted = 0
        counter = 0
        # prepare buffer
        row = {"SourceIP": "", "SourcePort": "", "DestinationIP": "", "DestinationPort": "", "Timestamp": ""}
        rows = [row.copy() for i in range(1000)]

        # skip the titles line at the start of the file
        proc.stdout.readline()

        while True:
            line_num += 1
            line = proc.stdout.readline()
            if line == '':
                break

            if self.translate(line, line_num, rows[counter]) != 0:
                continue

            counter += 1

            if counter == 1000:
                self.insert_data(rows, counter)
                lines_inserted += counter
                counter = 0
        if counter != 0:
            self.insert_data(rows, counter)
            lines_inserted += counter

        # pass through anything else and close the process
        proc.poll()
        while proc.returncode is None:
            proc.stdout.readline()
            proc.poll()
        proc.wait()

        print("Done. {0} lines processed, {1} rows inserted".format(line_num, lines_inserted))

    def import_string(self, s):
        """
        Takes a string containing one or more lines and attempts to import it into the database staging table.
        Args:
            s: One or more syslog lines

        Returns:
            None
        """
        args = shlex.split('nfdump -o "fmt:%pr,%sa,%sp,%da,%dp,%byt,%bps,%ts"')
        proc = subprocess.Popen(args, bufsize=-1, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout, stderr = proc.communicate(s)
        all_lines = stdout.splitlines()

        line_num = -1
        lines_inserted = 0
        counter = 0
        row = {"SourceIP": "", "SourcePort": "", "DestinationIP": "", "DestinationPort": "", "Timestamp": ""}
        rows = [row.copy() for i in range(1000)]
        for line in all_lines:
            line_num += 1

            if self.translate(line, line_num, rows[counter]) != 0:
                continue

            counter += 1

            # Perform the actual insertion in batches of 1000
            if counter == 1000:
                self.insert_data(rows, counter)
                lines_inserted += counter
                counter = 0
        if counter != 0:
            self.insert_data(rows, counter)
            lines_inserted += counter
        print("Done. {0} lines processed, {1} rows inserted".format(line_num, lines_inserted))

    def translate(self, line, linenum, dictionary):
        # remove trailing newline
        line = line.rstrip("\n")
        split_data = line.split(",")
        if len(split_data) != 8:
            return 1
        split_data = [i.strip(' ') for i in split_data]

        if split_data[0] != 'UDP':
            # printing this is very noisy and slow
            # print("Line {0}: Ignoring non-TCP entry (was {1})".format(lineNum, split_data[29]))
            return 2

        # srcIP, srcPort, dstIP, dstPort
        dictionary['SourceIP'] = common.IPtoInt(*(split_data[1].split(".")))
        dictionary['SourcePort'] = split_data[2]
        dictionary['DestinationIP'] = common.IPtoInt(*(split_data[3].split(".")))
        dictionary['DestinationPort'] = split_data[4]
        dictionary['Timestamp'] = split_data[7]
        return 0


# If running as a script, begin by executing main.
if __name__ == "__main__":
    importer = NFDumpImporter()
    importer.main(sys.argv)

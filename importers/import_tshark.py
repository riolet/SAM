import sys
import subprocess
import shlex
import common
from import_base import BaseImporter
import dateutil.parser


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
        args = shlex.split('tshark -r {0} -E separator=@ -e frame.number -e frame.time -e ip.src -e tcp.srcport '
                           '-e udp.srcport -e ip.dst -e tcp.dstport -e udp.dstport -e frame.len -T fields'.format(path_in))
        proc = subprocess.Popen(args, bufsize=-1, stdout=subprocess.PIPE)

        print 'tshark -r {0} -E separator=@ -e frame.number -e frame.time -e ip.src -e tcp.srcport -e udp.srcport -e ip.dst -e tcp.dstport -e udp.dstport -e frame.len -T fields'.format(path_in)
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
            #print line
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

    def translate(self, line, linenum, dictionary):
        # remove trailing newline
        line = line.rstrip("\n")
        split_data = line.split("@")
        if len(split_data) != 9:
            return 1
        split_data = [i.strip(' ') for i in split_data]
        #print split_data
        # srcIP, srcPort, dstIP, dstPort

        try:
            dictionary['SourceIP'] = common.IPtoInt(*(split_data[2].split(".")))
            dictionary['SourcePort'] = int(split_data[3] if len(split_data[3]) > 0 else split_data[4])
            dictionary['DestinationIP'] = common.IPtoInt(*(split_data[5].split(".")))
            dictionary['DestinationPort'] = int(split_data[6] if len(split_data[6]) > 0 else split_data[7])
            dictionary['Timestamp'] = dateutil.parser.parse(split_data[1]).strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print line, e.message
            return 1
        return 0


# If running as a script, begin by executing main.
if __name__ == "__main__":
    importer = NFDumpImporter()
    importer.main(sys.argv)

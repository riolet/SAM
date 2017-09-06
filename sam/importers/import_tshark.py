import sys
import subprocess
import shlex
import datetime
import time
from sam.importers.import_base import BaseImporter
try:
    import dateutil.parser
    DATEUTIL = True
except ImportError as e:
    DATEUTIL = False
    sys.stderr.write("Please install the dateutil package to use this importer.\n\t`pip install py-dateutil`\n")
    sys.stderr.write(e.message + '\n')


class TSharkImporter(BaseImporter):
    FIELDS = [
        'frame.number',
        'frame.time',
        'ip.src',
        'tcp.srcport',
        'udp.srcport',
        'ip.dst',
        'tcp.dstport',
        'udp.dstport',
        '_ws.col.Protocol' # for protocol
    ]
    # TODO: add tcp.analysis.bytes_in_flight, udp.length
    SRC = 2
    SRCPORT = 3  # or 4
    DST = 5
    DSTPORT = 6  # or 7
    TIMESTAMP = 1
    PROTOCOL = 8

    def __init__(self):
        BaseImporter.__init__(self)
        self.instructions = """
This program imports tshark data into the MySQL database.  The file must be a pcap file from TShark or Wireshark
Optionally, include the name of the datasource to import in to. Default uses currently selected data source.

Usage:
    python {0} <input-file> <data source>
""".format(sys.argv[0])

    def import_file(self, path_in):
        # Assume a binary file as input
        command = 'tshark -r {path} -E separator=@ {fields} -T fields'.format(
            path=path_in,
            fields='-e ' + ' -e '.join(TSharkImporter.FIELDS))

        # print 'tshark -r {0} -E separator=@ -e frame.number -e frame.time -e ip.src -e tcp.srcport -e udp.srcport -e ip.dst -e tcp.dstport -e udp.dstport -e frame.len -T fields'.format(path_in)
        args = shlex.split(command)
        proc = subprocess.Popen(args, bufsize=-1, stdout=subprocess.PIPE)

        line_num = -1
        lines_inserted = 0
        counter = 0
        # prepare buffer
        rows = [dict.fromkeys(self.keys, '') for _ in range(1000)]

        # TODO: read everything, and combine the conversation streams (aggregate/group by ip:port->ip:port)
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

    def import_string(self, s):
        raise NotImplementedError("String interpretation has not been implemented for TShark. File: {0}".format(__file__))

    def translate(self, line, linenum, dictionary):
        # remove trailing newline
        line = line.rstrip("\n")
        split_data = line.split("@")
        if len(split_data) < 5:
            return 1
        split_data = [i.strip(' ') for i in split_data]
        # srcIP, srcPort, dstIP, dstPort

        try:
            srcIP = split_data[TSharkImporter.SRC].split(",")[0].split(".")
            srcPort = split_data[TSharkImporter.SRCPORT] or split_data[TSharkImporter.SRCPORT + 1]
            dstIP = split_data[TSharkImporter.DST].split(",")[0].split(".")
            dstPort = split_data[TSharkImporter.DSTPORT] or split_data[TSharkImporter.DSTPORT + 1]
            if split_data[TSharkImporter.PROTOCOL] in ('UDP', 'DNS'):
                protocol = 'UDP'
            elif split_data[TSharkImporter.PROTOCOL] == 'ICMP':
                protocol = 'ICMP'
            else:
                protocol = 'TCP'
            if DATEUTIL:
                timestamp = dateutil.parser.parse(split_data[TSharkImporter.TIMESTAMP])
            else:
                ds = split_data[TSharkImporter.TIMESTAMP]
                timestamp = datetime.datetime.strptime(ds[:ds.rfind(".")], "%b %d, %Y %H:%M:%S")
        except Exception as e:
            print line, e.message
            return 2

        try:
            dictionary['src'] = self.ip_to_int(*srcIP)
            dictionary['srcport'] = int(srcPort)
            dictionary['dst'] = self.ip_to_int(*dstIP)
            dictionary['dstport'] = int(dstPort)
            dictionary['timestamp'] = timestamp
            dictionary['protocol'] = protocol

            # TODO: the following is placeholder.
            #       Needed: test data or spec to read
            dictionary['duration'] = 1
            dictionary['bytes_received'] = 0
            dictionary['bytes_sent'] = 100
            dictionary['packets_received'] = 0
            dictionary['packets_sent'] = 1
        except:
            print("srcIP: {}".format(srcIP))
            print("srcport: {}".format(srcPort))
            print("dstIP: {}".format(dstIP))
            print("dstport: {}".format(dstPort))
            return 3

        if dictionary['srcport'] < dictionary['dstport']:
            BaseImporter.reverse_connection(dictionary)
        return 0


class_ = TSharkImporter

# If running as a script, begin by executing main.
if __name__ == "__main__":
    sys.stderr.write("Warning: This importer is incomplete and uses empty data for some fields.")
    importer = class_()
    importer.main(sys.argv)

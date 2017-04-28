import sys
import subprocess
import shlex
from sam.importers.import_base import BaseImporter


def safe_translate(value):
    try:
        return int(float(value))
    except ValueError:
        prefix = value[-1]
        try:
            value = float(value[:-2])
        except ValueError:
            raise ValueError("Untranslatable number: {0}".format(value))
        if prefix == 'M':
            return int(value * 1e6)
        elif prefix == 'G':
            return int(value * 1e9)
        elif prefix == 'T':
            return int(value * 1e12)
        raise ValueError("Unknown prefix: {0} {1}".format(value, prefix))


class NFDumpImporter(BaseImporter):
    FORMAT = "fmt:%pr,%sa,%sp,%da,%dp,%ts,%ibyt,%obyt,%ipkt,%opkt,%td"
    PROTOCOL = 0
    SRC = 1
    SRCPORT = 2
    DST = 3
    DSTPORT = 4
    TIMESTAMP = 5
    B_RECEIVED = 6
    B_SENT = 7
    P_RECEIVED = 8
    P_SENT = 9
    DURATION = 10


    def __init__(self):
        BaseImporter.__init__(self)
        self.instructions = """
This program imports a nfdump into the MySQL database.  The file must be binary data from nfcapd.
Optionally, include the name of the datasource to import in to. Default uses currently selected data source.

Usage:
    python {0} <input-file> <data source>
""".format(sys.argv[0])

    def import_file(self, path_in):
        # Assume a binary file as input
        args = shlex.split('nfdump -r {0} -o {1}'.format(path_in, NFDumpImporter.FORMAT))
        try:
            proc = subprocess.Popen(args, bufsize=-1, stdout=subprocess.PIPE)
        except OSError as e:
            sys.stderr.write("To use this importer, please install nfdump.\n\t`apt-get install nfdump`\n")
            raise e

        line_num = -1
        lines_inserted = 0
        counter = 0
        # prepare buffer
        rows = [dict.fromkeys(self.keys, '') for _ in range(1000)]

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
        args = shlex.split('nfdump -o {0}'.format(NFDumpImporter.FORMAT))
        proc = subprocess.Popen(args, bufsize=-1, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout, stderr = proc.communicate(s)
        all_lines = stdout.splitlines()

        line_num = -1
        lines_inserted = 0
        counter = 0
        rows = [dict.fromkeys(self.keys, '') for i in range(1000)]
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
        if len(split_data) != 11:
            return 1
        split_data = [i.strip(' ') for i in split_data]

        #if split_data[0] != 'TCP':
        #    # printing this is very noisy and slow
        #    # print("Line {0}: Ignoring non-TCP entry (was {1})".format(lineNum, split_data[29]))
        #    return 2

        #self.keys = [
        #        "src",
        #        "srcport",
        #        "dst",
        #        "dstport",
        #        "timestamp",
        #        "protocol",
        #        "bytes_sent",
        #        "bytes_received",
        #        "packets_sent",
        #        "packets_received",
        #        "duration",
        #    ]
        dictionary['src'] = self.ip_to_int(*(split_data[NFDumpImporter.SRC].split(".")))
        dictionary['srcport'] = split_data[NFDumpImporter.SRCPORT]
        dictionary['dst'] = self.ip_to_int(*(split_data[NFDumpImporter.DST].split(".")))
        dictionary['dstport'] = split_data[NFDumpImporter.DSTPORT]
        dictionary['timestamp'] = split_data[NFDumpImporter.TIMESTAMP]
        dictionary['protocol'] = split_data[NFDumpImporter.PROTOCOL].upper()
        dictionary['bytes_sent'] = safe_translate(split_data[NFDumpImporter.B_SENT])
        dictionary['bytes_received'] = safe_translate(split_data[NFDumpImporter.B_RECEIVED])
        dictionary['packets_sent'] = safe_translate(split_data[NFDumpImporter.P_SENT])
        dictionary['packets_received'] = safe_translate(split_data[NFDumpImporter.P_RECEIVED])
        dictionary['duration'] = safe_translate(split_data[NFDumpImporter.DURATION])
        return 0


class_ = NFDumpImporter

# If running as a script, begin by executing main.
if __name__ == "__main__":
    importer = _class()
    importer.main(sys.argv)

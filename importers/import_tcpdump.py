import sys
from import_base import BaseImporter
try:
    import dateutil.parser
except ImportError as e:
    sys.stderr.write("Please install the dateutil package to use this importer.\n\t`pip install py-dateutil`\n")
    sys.stderr.write(e.message + '\n')
    sys.exit(-1)


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
        try:
            a = line.split()

            dt = dateutil.parser.parse(a[0])
            src_ip_port = a[2].split(".")
            src_port = src_ip_port.pop()
            dst_ip_port = a[4].split(".")
            dst_port = dst_ip_port.pop()

            dictionary['src'] = self.ip_to_int(*src_ip_port)
            dictionary['srcport'] = int(src_port)
            dictionary['dst'] = self.ip_to_int(*dst_ip_port)
            dictionary['dstport'] = int(dst_port.strip(":"))
            dictionary['timestamp'] = dt.strftime(self.mysql_time_format)

            # TODO: the following is placeholder.
            #       Needed: test data or spec to read
            dictionary['protocol'] = 'TCP'.upper()
            dictionary['duration'] = '1'
            dictionary['bytes_received'] = '1'
            dictionary['bytes_sent'] = '1'
            dictionary['packets_received'] = '1'
            dictionary['packets_sent'] = '1'
        except TypeError as ex:
            print "Ignoring line because of error TypeError: " + ex.message
            return 1
        except UnicodeDecodeError as ex:
            print "Ignoring line because of error UnicodeDecodeError: " + ex.message
            return 1
        return 0


_class = TCPDumpImporter

# If running as a script, begin by executing main.
if __name__ == "__main__":
    sys.stderr.write("Warning: This importer is incomplete and uses empty data for some fields.")
    importer = _class()
    importer.main(sys.argv)

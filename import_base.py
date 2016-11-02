import sys
import os
import common
import dbaccess


class BaseImporter:
    def __init__(self):
        self.instructions = """
This program imports a syslog dump into the database.
It extracts IP addresses and ports and discards other data. Only TCP traffic data is used.

Usage:
    python {0} <input-file>
""".format(sys.argv[0])

    mysql_time_format = '%Y-%m-%d %H:%M:%S'

    def main(self, argv):
        if len(argv) != 2:
            print(self.instructions)
            return

        if self.validate_file(argv[1]):
            self.import_file(argv[1])
        else:
            print(self.instructions)
            return

    def validate_file(self, path):
        """
        Check whether a given path is a file.
        Args:
            path: The path to verify is a file

        Returns:
            True or False
        """
        if os.path.isfile(path):
            return True
        else:
            print("File not found:", path)
            return False

    def translate(self, line, line_num, dictionary):
        """
        Converts a given syslog line into a dictionary of (ip, port, ip, port, timestamp)
        Args:
            line: The syslog line to parse
            line_num: The line number, for error printouts
            dictionary: The dictionary to write key/values pairs into

        Returns:
            0 on success and non-zero on error.
        """
        return 1

    def import_file(self, path_in):
        """
        Takes a file path and attempts to import it into the database. Specifically into the samapper.Syslog table
        Args:
            path_in: The path to a log file to read/import

        Returns:
            None
        """
        with open(path_in) as fin:
            line_num = -1
            lines_inserted = 0
            counter = 0
            row = {"SourceIP": "", "SourcePort": "", "DestinationIP": "", "DestinationPort": "", "Timestamp": ""}
            rows = [row.copy() for i in range(1000)]
            for line in fin:
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

    def insert_data(self, rows, count):
        """
        Attempt to insert the first 'count' items in 'rows' into the database table `samapper`.`Syslog`.
        Exits script on critical failure.
        Args:
            rows: The iterable containing dictionaries to insert
                (dictionaries must all have the same keys, matching column names)
            count: The number of items from rows to insert

        Returns:
            None
        """
        try:
            truncated_rows = rows[:count]
            # >>> values = [{"name": "foo", "email": "foo@example.com"}, {"name": "bar", "email": "bar@example.com"}]
            # >>> db.multiple_insert('person', values=values, _test=True)
            common.db.multiple_insert('Syslog', values=truncated_rows)
        except Exception as e:
            # see http://dev.mysql.com/doc/refman/5.7/en/error-messages-server.html for codes
            if e[0] == 1049:  # Unknown database 'samapper'
                dbaccess.create_database()
                self.insert_data(rows, count)
            elif e[0] == 1045:  # Access Denied for '%s'@'%s' (using password: (YES|NO))
                print(e[1])
                print("Check your username / password? (dbconfig_local.py)")
                sys.exit(1)
            else:
                print("Critical failure.")
                print(e.message)
                sys.exit(2)

import sys
import os
import common
import dbaccess


class BaseImporter:
    mysql_time_format = '%Y-%m-%d %H:%M:%S'

    def __init__(self):
        self.keys = [
                "src",
                "srcport",
                "dst",
                "dstport",
                "timestamp",
                "protocol",
                "bytes_sent",
                "bytes_received",
                "packets_sent",
                "packets_received",
                "duration",
            ]
        self.instructions = """
This program imports a syslog dump into the database.
It extracts IP addresses and ports and discards other data. Only TCP traffic data is used.
Optionally, include the name of the datasource to import in to. Default uses currently selected data source.

Usage:
    python {0} <input-file>
    python {0} <input-file> <data source>

""".format(sys.argv[0])
        self.datasource = 0
        self.buffer = 'A' # 'A' or 'B'

    def main(self, argv):
        if not (1 < len(argv) < 4):
            print(self.instructions)
            return

        self.datasource = self.determine_datasource(argv)

        if self.validate_file(argv[1]) and self.datasource > 0:
            self.import_file(argv[1])
        else:
            print(self.instructions)
            return

    def determine_datasource(self, argv):
        settings = dbaccess.get_settings(all=True)
        default_ds = settings['datasource']['id']
        custom_ds = 0
        if len(argv) >= 3:
            requested_ds = argv[2]
            for ds in settings['datasources']:
                if ds['name'] == requested_ds:
                    custom_ds = ds['id']
                    break

        if custom_ds > 0:
            return custom_ds
        else:
            return default_ds

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

    def import_string(self, s):
        """
        Takes a string containing one or more lines and attempts to import it into the database staging table.
        Args:
            s: One or more syslog lines

        Returns:
            None
        """
        all_lines = s.splitlines()
        line_num = 0
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

    def import_file(self, path_in):
        """
        Takes a file path and attempts to import it into the database staging table.
        Args:
            path_in: The path to a log file to read/import

        Returns:
            None
        """
        with open(path_in) as fin:
            line_num = 0
            lines_inserted = 0
            counter = 0
            rows = [dict.fromkeys(self.keys, '') for i in range(1000)]
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
        table_name = "ds_{ds}_Syslog{buffer}".format(ds=self.datasource, buffer=self.buffer)
        try:
            truncated_rows = rows[:count]
            if count > 0 and len(rows[0].keys()) != len(self.keys):
                print("Database key length doesn't match. Check that your importer's translate function "
                      "fills all the dictionary keys in import_base.keys exactly.")
                print("Expected keys: {0}".format(repr(self.keys)))
                print("Received keys: {0}".format(repr(rows[0].keys())))
                sys.exit(3)
            # >>> values = [{"name": "foo", "email": "foo@example.com"}, {"name": "bar", "email": "bar@example.com"}]
            # >>> db.multiple_insert('person', values=values, _test=True)
            common.db_quiet.multiple_insert(table_name, values=truncated_rows)
        except Exception as e:
            print("Error inserting into database:")
            import integrity
            if integrity.check_and_fix_db_access() == 0:
                print("Resuming...")
                self.insert_data(rows, count)
            else:
                print("Critical failure. Aborting.")
                sys.exit(2)

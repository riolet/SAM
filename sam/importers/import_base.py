import sys
import os
import numbers
import sam.constants
import traceback
import importlib
common = None
Datasources = None


class BaseImporter:
    mysql_time_format = '%Y-%m-%d %H:%M:%S'
    keys = [
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

    def __init__(self):
        self.instructions = """
This program imports a syslog dump into the database.
It extracts IP addresses and ports and discards other data. Only TCP traffic data is used.
Optionally, include the name of the datasource to import in to. Default uses currently selected data source.

Usage:
    python {0} <input-file> <data-source>

""".format(sys.argv[0])
        self.dsModel = None
        self.subscription = None
        self.ds_name = None  # datasource name
        self.ds_id = None  # datasource id
        self.failed_attempts = 0

    @staticmethod
    def ip_to_int(a, b, c, d):
        """
        Converts a number from a sequence of dotted decimals into a single unsigned int.
        Args:
        :param a: IP address segment 1 ###.0.0.0
        :type a: str or unicode
        :param b: IP address segment 2 0.###.0.0
        :type b: str or unicode
        :param c: IP address segment 3 0.0.###.0
        :type c: str or unicode
        :param d: IP address segment 4 0.0.0.###
        :type d: str or unicode

        :return: The IP address as a simple 32-bit unsigned integer
        :rtype: int
        """
        return (int(a) << 24) + (int(b) << 16) + (int(c) << 8) + int(d)

    def main(self, argv):
        if not (1 < len(argv) < 4):
            print(self.instructions)
            return

        try:
            self.determine_datasource(argv)
        except ValueError:
            print(self.instructions)
            return

        self.set_subscription(1)

        if self.validate_file(argv[1]):
            self.import_file(argv[1])
        else:
            print(self.instructions)
            return

    def determine_datasource(self, argv):
        if len(argv) >= 3 and len(argv[2]) >= 1:
            requested_ds = argv[2]
        else:
            raise ValueError("Cannot determine datasource. Argv is {0}".format(repr(argv)))

        try:
            requested_ds = int(requested_ds)
            self.set_datasource_id(requested_ds)
        except:
            self.set_datasource_name(requested_ds)

        return requested_ds

    @staticmethod
    def validate_file(path):
        """
        Check whether a given path is a file.
        Args:
            path: The path to verify is a file

        Returns:
            True or False
        """
        return os.path.isfile(path)

    def import_packets(self, packets):
        """
        Take in packets received via collector and return translated lines.

        :param packets: a string received by the collector. May be ascii or binary. This base function presumes ascii.
        :type packets: string
        :return: a list translated log lines
        :rtype: List [ Dict [ str, any ]
        """
        stripped = [line.strip() for line in packets]
        translated = []
        for line in stripped:
            translated_line = {}
            success = self.translate(line, 1, translated_line)
            if success == 0:
                translated.append(translated_line)
        return translated


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
        raise NotImplementedError("importers must implement this function")

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
        rows = [dict.fromkeys(self.keys, '') for _ in range(1000)]
        for line in all_lines:
            line_num += 1

            try:
                if self.translate(line, line_num, rows[counter]) != 0:
                    continue
            except:
                traceback.print_exc()
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
        return lines_inserted

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
            rows = [dict.fromkeys(self.keys, '') for _ in range(1000)]
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
        return lines_inserted

    def set_subscription(self, sub_id):
        self.subscription = sub_id

    def set_datasource_id(self, ds_id):
        """
        :param ds: integer datasource id
         :type ds: numbers.Integral
        :return: None 
        """
        self.ds_id = int(ds_id)

    def set_datasource_name(self, ds_name):
        """
        :param ds: string datasource id
         :type ds: basestring
        :return: None 
        """
        self.ds_name = ds_name

    @staticmethod
    def reverse_connection(conn):
        temp = conn['srcport']
        conn['srcport'] = conn['dstport']
        conn['dstport'] = temp

        temp = conn['src']
        conn['src'] = conn['dst']
        conn['dst'] = temp

        temp = conn['bytes_received']
        conn['bytes_received'] = conn['bytes_sent']
        conn['bytes_sent'] = temp

        temp = conn['packets_received']
        conn['packets_received'] = conn['packets_sent']
        conn['packets_sent'] = temp

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
        global common
        global Datasources

        if self.subscription is None:
            raise ValueError("No account (subscription) specified.)")

        try:
            import sam.common
            common = sam.common
            from sam.models.datasources import Datasources
        except:
            traceback.print_exc()
            import sam.integrity
            sam.integrity.check_and_fix_db_access(sam.constants.dbconfig.copy())
        try:
            self.dsModel = Datasources(common.db_quiet, {}, self.subscription)
            datasources = self.dsModel.datasources.values()
        except Exception as e:
            # traceback.print_exc()
            print(e)
            import sam.integrity
            sam.integrity.check_and_fix_integrity()

        if self.ds_id is None:
            self.dsModel = Datasources(common.db_quiet, {}, self.subscription)
            if self.ds_name:
                self.ds_id = self.dsModel.name_to_id(self.ds_name)
            if self.ds_id is None and len(self.dsModel.ds_ids) == 1:
                self.ds_id = self.dsModel.ds_ids[0]
            else:
                raise ValueError("No datasource specified")

        table_name = "s{acct}_ds{ds}_Syslog".format(acct=self.subscription, ds=self.ds_id)

        try:
            truncated_rows = rows[:count]
            if set(rows[0].keys()) != set(self.keys):
                print("Database keys don't match. Check that your importer's translate function "
                      "fills all the dictionary keys in import_base.keys exactly.")
                print("Expected keys: {0}".format(repr(sorted(self.keys))))
                print("Received keys: {0}".format(repr(sorted(rows[0].keys()))))
                raise AssertionError("Insertion keys do not match expected keys.")

            # multiple_insert example:
            # >>> table_name = "my_table"
            # >>> values = [{"name": "foo", "email": "foo@example.com"}, {"name": "bar", "email": "bar@example.com"}]
            # >>> db.multiple_insert(table_name, values=values)
            common.db_quiet.multiple_insert(table_name, values=truncated_rows)
        except Exception as e:
            self.failed_attempts += 1
            print("Error inserting into database:")
            print("\t{0}".format(e))
            from sam import integrity
            if self.failed_attempts < 2:
                if integrity.check_and_fix_integrity() == 0:
                    print("Resuming...")
                    self.insert_data(rows, count)
                else:
                    print("Aborting...")
                    raise AssertionError("Failed to fix database access. ")
            else:
                print("Critical failure. Aborting.")
                raise AssertionError("Failed to fix problem multiple times. Aborting.")


class_ = BaseImporter


def get_importer(import_format, sub_id, ds_id):
    """
    :param import_format: The format you're trying to import. must match file name. 
                   examples: paloalto, tcpdump, nfdump, tshark, ...
     :type import_format: unicode
    :param sub_id: subscription id
     :type sub_id: int
    :param ds_id: datasource id
     :type sub_id: int
    :return: importer instance or None
     :rtype: BaseImporter or None
    """
    if import_format is None:
        raise ImportError("Unable to get find importer given format.")
    module_ = None
    importer = None

    # normalize format name
    import_format = import_format.lower()
    if import_format.startswith("import_"):
        import_format = import_format[7:]
    i = import_format.rfind(".py")
    if i != -1:
        import_format = import_format[:i]

    # try to load the importer from plugin libraries
    for path in sam.constants.plugin_importers:
        fullname = "{path}.importers.import_{format}".format(path=path, format=import_format)
        try:
            module_ = importlib.import_module(fullname)
        except ImportError:
            continue
        break

    # if the above failed, attempt to import it from the default library
    if not module_:
        fullname = "sam.importers.import_{0}".format(import_format)
        try:
            module_ = importlib.import_module(fullname)
        except ImportError:
            pass

    # instantiate the importer class
    if module_:
        try:
            importer = module_.class_()
            importer.set_subscription(sub_id)
            try:
                importer.set_datasource_id(int(ds_id))
            except:
                importer.set_datasource_name(ds_id)
        except:
            print("Error instantiating importer for {}. Is module.class_ defined?".format(import_format))
            raise
    else:
        raise ImportError("Unable to get find importer given format.")

    return importer

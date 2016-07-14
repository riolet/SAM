import sys
import os
import json
import common
import dbaccess
import MySQLdb

def validate_file(path):
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


def instructions():
    print("""
This program imports a syslog dump into the MySQL database.
It extracts IP addresses and ports and discards other data. Only TCP traffic data is used.

Usage:
    python {0} <input-file>
    """.format(sys.argv[0]))


def translate(line, line_num):
    """
    Converts a given syslog line into a tuple of (ip, port, ip, port)
    Args:
        line: The syslog line to parse
        line_num: The line number, for error printouts

    Returns:
        A tuple consisting of (Source IP, Source Port, Dest IP, Dest Port)
    """
    data = json.loads(line)['message']
    # TODO: this assumes the data will not have any commas embedded in strings
    split_data = data.split(',')

    if split_data[3] != "TRAFFIC":
        print("Line {0}: Ignoring non-TRAFFIC entry (was {1})".format(line_num, split_data[3]))
        return None
    if len(split_data) < 29:
        print("error parsing line {0}: {1}".format(line_num, line))
        return None
    # 29 is protocol: tcp, udp, ...
    # TODO: don't ignore everything but TCP
    if split_data[29] != 'tcp':
        # printing this is very noisy and slow
        # print("Line {0}: Ignoring non-TCP entry (was {1})".format(lineNum, split_data[29]))
        return None

    # srcIP, srcPort, dstIP, dstPort
    return (common.IPtoInt(*(split_data[7].split("."))),
            split_data[24],
            common.IPtoInt(*(split_data[8].split("."))),
            split_data[25])


def import_file(path_in):
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
        rows = [("", "", "", "")] * 1000
        for line in fin:
            line_num += 1

            translated_line = translate(line, line_num)
            if translated_line is None:
                continue

            rows[counter] = translated_line
            counter += 1

            # Perform the actual insertion in batches of 1000
            if counter == 1000:
                insert_data(rows, counter)
                lines_inserted += counter
                counter = 0
        if counter != 0:
            insert_data(rows, counter)
            lines_inserted += counter
        print("Done. {0} lines processed, {1} rows inserted".format(line_num, lines_inserted))


def insert_data(rows, count):
    """
    Attempt to insert the first `count` items in `rows` into the database table `samapper`.`Syslog`.
    Exits script on critical failure.
    Args:
        rows: The iterable containing data to insert
        count: The number of items from rows to insert

    Returns:
        None
    """
    try:
        params = common.dbconfig.params.copy()
        params.pop('dbn')
        pw = params.pop('pw')
        params['passwd'] = pw
        with MySQLdb.connect(**params) as connection:
            truncated_rows = rows[:count]
            connection.executemany("""INSERT INTO Syslog (SourceIP, SourcePort, DestinationIP, DestinationPort)
            VALUES (%s, %s, %s, %s);""", truncated_rows)
    except Exception as e:
        # see http://dev.mysql.com/doc/refman/5.7/en/error-messages-server.html for codes
        if e[0] == 1049: # Unknown database 'samapper'
            dbaccess.create_database()
            insert_data(rows, count)
        elif e[0] == 1045: # Access Denied for '%s'@'%s' (using password: (YES|NO))
            print(e[1])
            print("Check your username / password? (dbconfig_local.py)")
            sys.exit(1)
        else:
            print("Critical failure.")
            print(e.message)
            sys.exit(2)


def main(argv):
    if len(argv) != 2:
        instructions()
        return

    if validate_file(argv[1]):
        import_file(argv[1])
    else:
        instructions()
        return


# If running as a script, begin by executing main.
if __name__ == "__main__":
    main(sys.argv)

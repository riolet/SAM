import sys
import os
import subprocess
import shlex
import common
import dbaccess


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
This program imports a nfdump into the MySQL database.
It extracts IP addresses and ports and discards other data. Only TCP traffic data is imported.

Usage:
    python {0} <input-file>
    """.format(sys.argv[0]))


def import_file(path_in):
    pass
    # Assume a binary file as input
    args = shlex.split('nfdump -r {0} -o "fmt:%pr,%sa,%sp,%da,%dp,%byt,%bps"'.format(path_in))
    proc = subprocess.Popen(args, bufsize=1, stdout=subprocess.PIPE)

    line_num = -1
    lines_inserted = 0
    counter = 0
    row = {"SourceIP": "", "SourcePort": "", "DestinationIP": "", "DestinationPort": ""}
    rows = [row.copy() for i in range(1000)]

    #bypass the header line at the start of the file
    proc.stdout.readline()


    proc.poll()
    while proc.returncode == None:
        line_num += 1
        line = proc.stdout.readline()
        if translate(line, line_num, rows[counter]) != 0:
            continue

        counter += 1

        if counter == 1000:
            insert_data(rows, counter)
            lines_inserted += counter
            counter = 0
        proc.poll()
    if counter != 0:
        insert_data(rows, counter)
        lines_inserted += counter

    proc.poll()
    #pass through anything else and close the file
    while proc.returncode == None:
        proc.stdout.readline()
        proc.poll()
    proc.wait()
    # proc.stdout.readlines()
    print("Done. {0} lines processed, {1} rows inserted".format(line_num, lines_inserted))


def translate(line, linenum, dictionary):
    #remove trailing newline
    line = line.rstrip("\n")
    split_data = line.split(",");
    if len(split_data) != 7:
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
    return 0


def insert_data(rows, count):
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

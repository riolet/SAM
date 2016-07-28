import sys
import os
import subprocess
import shlex
import common
import dbaccess
import import_paloalto


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
    # prepare buffer
    row = {"SourceIP": "", "SourcePort": "", "DestinationIP": "", "DestinationPort": ""}
    rows = [row.copy() for i in range(1000)]

    # skip the titles line at the start of the file
    proc.stdout.readline()

    proc.poll()
    while proc.returncode == None:
        line_num += 1
        line = proc.stdout.readline()
        if translate(line, line_num, rows[counter]) != 0:
            continue

        counter += 1

        if counter == 1000:
            import_paloalto.insert_data(rows, counter)
            lines_inserted += counter
            counter = 0
        proc.poll()
    if counter != 0:
        import_paloalto.insert_data(rows, counter)
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


def main(argv):
    if len(argv) != 2:
        instructions()
        return

    if import_paloalto.validate_file(argv[1]):
        import_file(argv[1])
    else:
        instructions()
        return


# If running as a script, begin by executing main.
if __name__ == "__main__":
    main(sys.argv)

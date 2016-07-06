import sys
import os
import json
import MySQLdb

try:
    sys.dont_write_bytecode = True
    import dbconfig_local as dbconfig
    sys.dont_write_bytecode = False
except:
    import dbconfig

def validate_file(path):
    # TODO: check output file doesn't exist, or confirm overwrite
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


# Translate an IP address into a number, [0..2^32 - 1]
def convert(a, b, c, d):
  return (int(a)<<24) + (int(b)<<16) + (int(c)<<8) + int(d)


def translate(line, lineNum):
    data = json.loads(line)['message']
    # TODO: this assumes the data will not have any commas embedded in strings
    split_data = data.split(',')

    if split_data[3] != "TRAFFIC":
        print("Line {0}: Ignoring non-TRAFFIC entry (was {1})".format(lineNum, split_data[3]))
        return None
    if len(split_data) < 29:
        print("error parsing line {0}: {1}".format(lineNum, line))
        return None
    # 29 is protocol: tcp, udp, ....
    # TODO: don't ignore everything but TCP
    if split_data[29] != 'tcp':
        # printing this is very noisy and slow
        # print("Line {0}: Ignoring non-TCP entry (was {1})".format(lineNum, split_data[29]))
        return None

    # srcIP, srcPort, dstIP, dstPort
    return (convert(*(split_data[7].split("."))),
            split_data[24],
            convert(*(split_data[8].split("."))),
            split_data[25])


def import_file(path_in):
    with open(path_in) as fin:
        lineNum = -1
        counter = 0
        rows = [("","","","")]*1000
        for line in fin:
            lineNum += 1

            translated_line = translate(line, lineNum);
            if translated_line is None:
                continue

            rows[counter] = translated_line
            counter += 1

            if counter == 1000:
                insert_data(rows, counter)
                counter = 0
        if counter != 0:
            insert_data(rows, counter)


def insert_data(rows, count):
    with MySQLdb.connect(**dbconfig.params) as connection:
        truncatedRows = rows[:count]
        connection.executemany("""INSERT INTO Syslog (SourceIP, SourcePort, DestinationIP, DestinationPort)
        VALUES (%s, %s, %s, %s);""", truncatedRows)



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

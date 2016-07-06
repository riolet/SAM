import sys
import os
import json


def validate_file(path):
    # TODO: check output file doesn't exist, or confirm overwrite
    if os.path.isfile(path):
        return True
    else:
        print("File not found:", path)
        return False


def instructions():
    print("""
This program filters a syslog dump to extract just IP addresses and ports. Only TCP data is used.
Output format is: SourceIP, SourcePort, DestIP, DestPort
Usage:
    {0} <input-file> <output-file>
    """.format(sys.argv[0]))


def import_file(path_in, path_out):
    with open(path_in) as fin, open(path_out, 'w') as fout:
        for line in fin:
            data = json.loads(line)['message']
            # TODO: this assumes the data will not have any commas embedded in strings
            split_data = data.split(',')

            # 29 is protocol: tcp, udp, ....
            # TODO: don't ignore everything but TCP
            if split_data[29] != 'tcp':
                continue

            fout.write("{0}, {1}, {2}, {3}\n".format(
                split_data[7],  # source IP
                split_data[24],  # source port
                split_data[8],  # dest IP
                split_data[25]))  # dest port


def main(argv):
    if len(argv) != 3:
        instructions()
        return

    if validate_file(argv[1]):
        import_file(argv[1], argv[2])
    else:
        instructions()
        return


# If running as a script, begin by executing main.
if __name__ == "__main__":
    main(sys.argv)

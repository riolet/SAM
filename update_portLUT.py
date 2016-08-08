import csv
import common
import os
import dbaccess
import urllib2


def get_raw_data():
    resource = "http://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.csv"
    print("requesting data from iana.org...")
    response = urllib2.urlopen(resource)
    print("reading response...")
    html = response.read()
    reader = csv.reader(html.split("\n"))
    rows = list(reader)
    print("raw data acquired")
    return rows


def expand(group):
    # expand "1, 2,3-6" into [1, 2, 3, 4, 5, 6]
    ungrouped = group.split(",")
    result = []
    for number in ungrouped:
        values = number.split('-')
        if len(values) == 1:
            result.extend(values)
        elif len(values) == 2:
            result.extend(range(int(values[0]), int(values[1]) + 1))
    as_ints = [int(i) for i in result]
    unique_only = list(set(as_ints))
    return unique_only


def escape(text):
    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = text.replace("\"", "\\\"")
    return text


def filter_lines(rows):
    key_name = 0
    key_portnumber = 1
    key_protocol = 2
    key_description = 3

    # cols = rows[0] # column headers
    raw_ports = rows[1:]
    filtered_rows = []
    for i in raw_ports:
        if len(i) < 12:
            continue
        name = i[key_name]
        desc = escape(i[key_description])
        protocol = i[key_protocol]
        if protocol == "tcp":
            tcp = 1
            udp = 0
        elif protocol == "udp":
            tcp = 0
            udp = 1
        else:
            continue
        if name == "" or i[key_portnumber] == "" or desc == "":
            continue
        try:
            number = int(i[key_portnumber])
            filtered_rows.append([name, number, tcp, udp, desc])
        except ValueError as e:
            # expand the number range
            try:
                number = expand(i[key_portnumber])
            except ValueError as e:
                print(e.message)
                print("row is: " + str(i))
                raise e
            for n in number:
                filtered_rows.append([name, n, tcp, udp, desc])
    print("rows filtered")
    return filtered_rows


def combine_duplicates(rows):
    key_name = 0
    key_portnumber = 1
    key_tcp = 2
    key_udp = 3

    rows.sort(key=lambda p : p[key_portnumber])

    ports = []
    currentPortNumber = -1
    last_index = -1
    for i in rows:
        if i[key_portnumber] != currentPortNumber:
            currentPortNumber = i[key_portnumber]
            ports.append(i)
            last_index += 1
        else:
            if i[key_name] == ports[last_index][key_name]:
                ports[last_index][key_tcp] |= i[key_tcp]
                ports[last_index][key_udp] |= i[key_udp]
    print("rows made unique; duplicates combined")
    return ports


def write_default_port_data(ports):
    key_name = 0
    key_portnumber = 1
    key_tcp = 2
    key_udp = 3
    key_description = 4
    with open(os.path.join(common.base_path, 'sql/default_port_data.json'), 'wb') as f:
        f.write("""{
  "ports": {
""")
        for port in ports[:-1]:
            text = \
                """    \"{0}\": {{
    \"port\": {0},
    \"tcp\": {1},
    \"udp\": {2},
    \"name\": \"{3}\",
    \"description\": \"{4}\"
  }},
 """.format(port[key_portnumber], port[key_tcp], port[key_udp], port[key_name], port[key_description])
            f.write(text)
        text = \
            """    \"{0}\": {{
    \"port\": {0},
    \"tcp\": {1},
    \"udp\": {2},
    \"name\": \"{3}\",
    \"description\": \"{4}\"
  }}
""".format(ports[-1][key_portnumber], ports[-1][key_tcp], ports[-1][key_udp], ports[-1][key_name],
                       ports[-1][key_description])
        f.write(text)
        f.write("""  }
}""")
    print("default port data written out")


def rebuild_lut():
    # 1.  download port name data and recreate default_port_data.json.
    rows = get_raw_data()
    filtered_rows = filter_lines(rows)
    ports = combine_duplicates(filtered_rows)
    write_default_port_data(ports)

    # 2.  rebuild database with new port information
    dbaccess.reset_port_names()

if __name__ == '__main__':
    rebuild_lut()

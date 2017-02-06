import csv
import common
import os
import urllib2
import integrity


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
        protocol = {i[key_protocol]}
        if name == "" or i[key_portnumber] == "" or desc == "":
            continue
        try:
            number = int(i[key_portnumber])
            filtered_rows.append([name, number, protocol, desc])
        except ValueError:
            # expand the number range
            try:
                number = expand(i[key_portnumber])
            except ValueError as e:
                print(e.message)
                print("row is: " + str(i))
                raise e
            for n in number:
                filtered_rows.append([name, n, protocol, desc])
    print("rows filtered")
    return filtered_rows


def combine_duplicates(rows):
    key_name = 0
    key_portnumber = 1
    key_protocol = 2

    rows.sort(key=lambda p: p[key_portnumber])

    ports = []
    current_port_number = -1
    last_index = -1
    for i in rows:
        if i[key_portnumber] != current_port_number:
            current_port_number = i[key_portnumber]
            ports.append(i)
            last_index += 1
        else:
            if i[key_name] == ports[last_index][key_name]:

                ports[last_index][key_protocol] |= i[key_protocol]
    print("rows made unique; duplicates combined")
    return ports


def write_default_port_data(ports):
    key_name = 0
    key_portnumber = 1
    key_protocol = 2
    key_description = 3
    with open(os.path.join(common.base_path, 'sql/default_port_data.json'), 'wb') as f:
        f.write("""{
  "ports": {
""")
        for port in ports[:-1]:
            text = \
                """    \"{port}\": {{
    \"port\": {port},
    \"protocols\": \"{protocol}\",
    \"name\": \"{name}\",
    \"description\": \"{desc}\"
  }},
""".format(port=port[key_portnumber],
            protocol=",".join(port[key_protocol]).upper().strip(','),
            name=port[key_name],
            desc=port[key_description])
            f.write(text)
        text = """    \"{port}\": {{
    \"port\": {port},
    \"protocols\": \"{protocols}\",
    \"name\": \"{name}\",
    \"description\": \"{desc}\"
  }}
""".format(port=ports[-1][key_portnumber],
           protocols=",".join(ports[-1][key_protocol]).upper().strip(','),
           name=ports[-1][key_name],
           desc=ports[-1][key_description])
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
    integrity.fill_port_table()


if __name__ == '__main__':
    rebuild_lut()

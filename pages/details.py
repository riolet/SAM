import json
import web
import dbaccess
import common


# This class is for getting the main selection details, such as ins, outs, and ports.


class Details:
    def __init__(self):
        self.ip_range = (0, 4294967295)
        self.ips = []
        self.ip_string = ""
        self.time_range = None
        self.port = None
        self.limit=50
        self.components = {
            "quick_info": self.quick_info,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "ports": self.ports,
            "summary": self.summary,
        }

    def process_input(self, GET_data):
        # ignore port, for now at least.
        if 'filter' in GET_data:
            # TODO: ignore port filters. For now.
            # self.port = GET_data.filter
            pass
        if 'tstart' in GET_data and 'tend' in GET_data:
            self.time_range = (int(GET_data.tstart), int(GET_data.tend))
        if 'address' in GET_data:
            try:
                self.ip_string = GET_data["address"]
                ips = self.ip_string.split(".")
                self.ips = [int(i) for i in ips]
                self.ip_range = dbaccess.determine_range(*self.ips)
            except ValueError:
                print("could not convert address ({0}) to integers.".format(GET_data['address']))

    def nice_ip_address(self):
        address = ".".join(map(str, self.ips))
        zeroes = 4 - len(self.ips)
        for i in range(zeroes):
            address += ".0"
        subnet = 32 - zeroes * 8
        if subnet != 32:
            address += "/" + str(subnet)
        return address

    def quick_info(self):
        info = []
        info.append(("IPv4 Address / Subnet", self.nice_ip_address()))
        node_info = dbaccess.get_node_info(self.ip_string)
        if node_info:
            if node_info.alias:
                info.append(("Name", node_info.alias))
            else:
                info.append(("Name", ""))

            summary = self.summary()
            info.append(("Unique inbound connections", summary.unique_in))
            info.append(("Unique outbound connections", summary.unique_out))
            info.append(("Ports accessed", summary.unique_ports))
        else:
            info.append(('No host found this address', '...'))
        return info

    def inputs(self):
        inputs = dbaccess.get_details_connections(self.ip_range, True, self.time_range, self.port, self.limit)
        conn_in = {}
        for connection in inputs:
            ip = common.IPtoString(connection.pop("ip"))
            if ip in conn_in:
                # add a port
                conn_in[ip] += [connection]
            else:
                # add a new entry
                conn_in[ip] = [connection]
        # convert to list of tuples to make it sortable
        conn_in = conn_in.items()
        conn_in.sort(key=key_by_link_sum, reverse=True)
        return conn_in

    def outputs(self):
        outputs = dbaccess.get_details_connections(self.ip_range, False, self.time_range, self.port, self.limit)
        conn_out = {}
        for connection in outputs:
            ip = common.IPtoString(connection.pop("ip"))
            if ip in conn_out:
                # add a port
                conn_out[ip] += [connection]
            else:
                # add a new entry
                conn_out[ip] = [connection]
        # convert to list of tuples to make it sortable
        conn_out = conn_out.items()
        conn_out.sort(key=key_by_link_sum, reverse=True)
        return conn_out

    def ports(self):
        ports = dbaccess.get_details_ports(self.ip_range, self.time_range, self.port, self.limit)
        return ports

    def summary(self):
        summary = dbaccess.get_details_summary(self.ip_range, self.time_range, self.port)
        return summary

    def selection_info(self):
        summary = self.summary()
        details = {}
        details['unique_out'] = summary.unique_out
        details['unique_in'] = summary.unique_in
        details['unique_ports'] = summary.unique_ports
        details['conn_in'] = self.inputs()
        details['conn_out'] = self.outputs()
        details['ports_in'] = self.ports()
        return details

    def GET(self, component=None):
        """
        The expected GET data includes:
            'address': dotted-decimal IP addresses.
                Each address is only as long as the subnet,
                    so 12.34.0.0/16 would be written as 12.34
            'filter': optional. If included, ignored.
            'tstart': optional. Used with 'tend'. The start of the time range to report links during.
            'tend': optional. Used with 'tstart'. The end of the time range to report links during.
        :return: A JSON-encoded dictionary where
            the keys are ['conn_in', 'conn_out', 'ports_in', 'unique_in', 'unique_out', 'unique_ports'] and
            the values are numbers or lists
        """
        web.header("Content-Type", "application/json")

        self.process_input(web.input())
        details = {}

        if self.ips:
            if component:
                components = component.split(",")
                for c_name in components:
                    if c_name in self.components:
                        details[c_name] = self.components[c_name]()
                    else:
                        details[c_name] = {"result": "No data source matches request for {0}".format(c_name)}
            else:
                details = self.selection_info()
        else:
            details = {"result": "ERROR: Malformed request. The 'address' key was missing"}
        return json.dumps(details)


def key_by_link_sum(connection):
    tally = 0
    for con in connection[1]:
        tally += con.links
    return tally

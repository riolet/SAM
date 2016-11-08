import json
import web
import dbaccess
import common
import decimal


# This class is for getting the main selection details, such as ins, outs, and ports.

def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError

class Details:
    def __init__(self):
        self.ip_range = (0, 4294967295)
        self.subnet = 0
        self.ips = []
        self.ip_string = ""
        self.time_range = None
        self.port = None
        self.page = 1
        self.page_size=50
        self.components = {
            "quick_info": self.quick_info,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "ports": self.ports,
            "children": self.children,
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
                self.ip_range = common.determine_range(*self.ips)
                self.subnet = len(ips) * 8
            except ValueError:
                print("details.py: process_input: Could not convert address ({0}) to integers.".format(repr(GET_data['address'])))
        if 'page' in GET_data:
            try:
                page = int(GET_data['page'])
                self.page = max(0, page)
            except ValueError:
                print("details.py: process_input: Could not interpret page number: {0}".format(repr(GET_data['page'])))
        if 'page_size' in GET_data:
            try:
                page_size = int(GET_data['page_size'])
                self.page_size = max(0, page_size)
            except ValueError:
                print("details.py: process_input: Could not interpret page_size: {0}".format(repr(GET_data['page_size'])))

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
            #node_info has:
            # hostname
            # unique_out
            # total_out
            # unique_in
            # total_in
            # ports_used
            # seconds
            info.append(("Name", node_info.hostname))

            in_per = float(node_info.total_in / node_info.seconds)
            in_per_time = "second"
            if 0 < in_per < 1:
                in_per *= 60
                in_per_time = "minute"
            if 0 < in_per < 1:
                in_per *= 60
                in_per_time = "hour"
            info.append(("Inbound connections",
                         ["{0} total connections".format(node_info.total_in),
                          "{0} unique connections (source & port)".format(node_info.unique_in),
                          "{0:.2f} connections / {1}".format(in_per, in_per_time)
                          ]))

            out_per = float(node_info.total_out / node_info.seconds)
            out_per_time = "second"
            if 0 < out_per < 1:
                out_per *= 60
                out_per_time = "minute"
            if 0 < out_per < 1:
                out_per *= 60
                out_per_time = "hour"
            info.append(("Outbound connections",
                         ["{0} total connections".format(node_info.total_out),
                          "{0} unique connections (destination & port)".format(node_info.unique_out),
                          "{0:.2f} connections / {1}".format(out_per, out_per_time)
                          ]))
            role = float(node_info.total_in / (node_info.total_in + node_info.total_out))
            if role <= 0:
                role_text = "client"
            elif role < 0.35:
                role_text = "mostly client"
            elif role < 0.65:
                role_text = "mixed client/server"
            elif role < 1.0:
                role_text = "mostly server"
            else:
                role_text = "server"
            info.append(("Role (0 = client, 1 = server)", "{0:.2f} ({1})".format(role, role_text)))
            info.append(("Local ports accessed", node_info.ports_used))
        else:
            info.append(('No host found this address', '...'))
        return info

    def inputs(self):
        inputs = dbaccess.get_details_connections(
            ip_range=self.ip_range,
            inbound=True,
            timestamp_range=self.time_range,
            port=self.port,
            page=self.page,
            page_size=self.page_size,
            order="-links")
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
        outputs = dbaccess.get_details_connections(
            ip_range=self.ip_range,
            inbound=False,
            timestamp_range=self.time_range,
            port=self.port,
            page=self.page,
            page_size=self.page_size,
            order="-links")
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
        ports = dbaccess.get_details_ports(self.ip_range, self.time_range, self.port, self.page_size)
        return ports

    def children(self):
        children = dbaccess.get_details_children(self.ip_range, self.subnet)
        return children

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
        return json.dumps(details, default=decimal_default)


def key_by_link_sum(connection):
    tally = 0
    for con in connection[1]:
        tally += con.links
    return tally

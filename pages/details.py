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
        self.order = None
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
        if 'order' in GET_data:
            self.order = GET_data['order']

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
        info = {}
        node_info = dbaccess.get_node_info(self.ip_string)

        info['address'] = self.nice_ip_address()
        
        if node_info:
            tags = dbaccess.get_tags(self.ip_string)
            envs = dbaccess.get_env(self.ip_string)
            #node_info has:
            # hostname
            # unique_out_ip
            # unique_out_conn
            # total_out
            # out_bytes_sent
            # out_bytes_received
            # out_packets_sent
            # out_packets_received
            # unique_in_ip
            # unique_in_conn
            # total_in
            # in_bytes_sent
            # in_bytes_received
            # in_packets_sent
            # in_packets_received
            # ports_used
            # endpoints
            # seconds
            info['name'] = node_info.hostname
            info['tags'] = tags
            info['envs'] = envs
            info['in'] = {}
            info['in']['total'] = node_info.total_in
            info['in']['u_ip'] = node_info.unique_in_ip
            info['in']['u_conn'] = node_info.unique_in_conn
            info['in']['seconds'] = node_info.seconds
            if not node_info.in_bytes_sent and not node_info.in_bytes_received:
                info['in']['bytes_sent'] = 0
                info['in']['bytes_received'] = 0
            else:
                info['in']['bytes_sent'] = node_info.in_bytes_sent
                info['in']['bytes_received'] = node_info.in_bytes_received
            info['in']['max_bps'] = node_info.in_max_bps if node_info.in_max_bps else 0
            info['in']['min_bps'] = node_info.in_min_bps if node_info.in_min_bps else 0
            info['in']['avg_bps'] = node_info.in_avg_bps if node_info.in_avg_bps else 0
            if not node_info.in_packets_sent and not node_info.in_packets_received:
                info['in']['packets_sent'] = 0
                info['in']['packets_received'] = 0
            else:
                info['in']['packets_sent'] = node_info.in_packets_sent
                info['in']['packets_received'] = node_info.in_packets_received
            info['in']['duration'] = node_info.in_duration
            info['out'] = {}
            info['out']['total'] = node_info.total_out
            info['out']['u_ip'] = node_info.unique_out_ip
            info['out']['u_conn'] = node_info.unique_out_conn
            info['out']['seconds'] = node_info.seconds
            if not node_info.out_bytes_sent and not node_info.out_bytes_received:
                info['out']['bytes_sent'] = 0
                info['out']['bytes_received'] = 0
            else:
                info['out']['bytes_sent'] = node_info.out_bytes_sent
                info['out']['bytes_received'] = node_info.out_bytes_received
            info['out']['max_bps'] = node_info.out_max_bps if node_info.out_max_bps else 0
            info['out']['min_bps'] = node_info.out_min_bps if node_info.out_min_bps else 0
            info['out']['avg_bps'] = node_info.out_avg_bps if node_info.out_avg_bps else 0
            if not node_info.out_packets_sent and not node_info.out_packets_received:
                info['out']['packets_sent'] = 0
                info['out']['packets_received'] = 0
            else:
                info['out']['packets_sent'] = node_info.out_packets_sent
                info['out']['packets_received'] = node_info.out_packets_received
            info['out']['duration'] = node_info.out_duration
            info['role'] = float(node_info.total_in / (node_info.total_in + node_info.total_out))
            info['ports'] = node_info.ports_used
            info['endpoints'] = int(node_info.endpoints)
        else:
            info['error'] = 'No host found this address'
        return info

    def inputs(self, light=False):
        inputs = dbaccess.get_details_connections(
            ip_range=self.ip_range,
            inbound=True,
            timestamp_range=self.time_range,
            port=self.port,
            page=self.page,
            page_size=self.page_size,
            order=self.order)
        if light:
            headers = [
                ['src', "Source IP"],
                ['port', "Dest. Port"],
                ['links', 'Count']
            ]
        else:
            headers = [
                ['src', "Source IP"],
                ['dst', "Dest. IP"],
                ['port', "Dest. Port"],
                ['links', 'Count']
            ]
        # convert list of dicts to ordered list of values
        conn_in = [[row[h[0]] for h in headers] for row in inputs]
        response = {
            "page": self.page,
            "page_size": self.page_size,
            "order": self.order,
            "direction": "desc",
            "component": "inputs",
            "headers": headers,
            "rows": conn_in
        }
        return response

    def outputs(self, light=False):
        outputs = dbaccess.get_details_connections(
            ip_range=self.ip_range,
            inbound=False,
            timestamp_range=self.time_range,
            port=self.port,
            page=self.page,
            page_size=self.page_size,
            order=self.order)
        if light:
            headers = [
                ['dst', "Dest. IP"],
                ['port', "Dest. Port"],
                ['links', 'Count']
            ]
        else:
            headers = [
                ['src', "Source IP"],
                ['dst', "Dest. IP"],
                ['port', "Dest. Port"],
                ['links', 'Count']
            ]
        conn_out = [[row[h[0]] for h in headers] for row in outputs]
        response = {
            "page": self.page,
            "page_size": self.page_size,
            "order": self.order,
            "direction": "desc",
            "component": "outputs",
            "headers": headers,
            "rows": conn_out
        }
        return response

    def ports(self):
        ports = dbaccess.get_details_ports(
            ip_range=self.ip_range,
            timestamp_range=self.time_range,
            port=self.port,
            page=self.page,
            page_size=self.page_size,
            order=self.order)
        headers = [
            ['port', "Port Accessed"],
            ['links', 'Occurrences']
        ]
        response = {
            "page": self.page,
            "page_size": self.page_size,
            "order": self.order,
            "component": "ports",
            "headers": headers,
            "rows": [[row[h[0]] for h in headers] for row in ports]
        }
        return response

    def children(self):
        children = dbaccess.get_details_children(
            ip_range=self.ip_range,
            subnet=self.subnet,
            page=self.page,
            page_size=self.page_size,
            order=self.order)
        response = {
            "page": self.page,
            "page_size": self.page_size,
            "order": self.order,
            "count": len(children),
            "component": "children",
            "headers": [
                ['ipstart', "Address"],
                ['hostname', 'Name'],
                ['endpoints', 'Active Endpoints'],
                ['ratio', 'Role (0=client, 1=server)']
            ],
            "rows": children
        }
        return response

    def summary(self):
        summary = dbaccess.get_details_summary(self.ip_range, self.time_range, self.port)
        return summary

    def selection_info(self):
        # called for selections in the map pane
        summary = self.summary()
        details = {}
        details['unique_out'] = summary.unique_out
        details['unique_in'] = summary.unique_in
        details['unique_ports'] = summary.unique_ports
        details['inputs'] = self.inputs(light=True)
        details['outputs'] = self.outputs(light=True)
        details['ports'] = self.ports()
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

import json
import dbaccess
import web
import decimal
import common
import re


# This class is for getting the links or edges connecting nodes in the graph


def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError


class Links:
    def __init__(self):
        self.addresses = []
        self.port = ""
        self.protocol = None
        self.timestart = 1
        self.timeend = 2 ** 31 - 1
        self.ds = 0

    def get_links(self):
        result = {}
        timerange = (self.timestart, self.timeend)
        for address in self.addresses:
            ipstart, ipend = common.determine_range_string(address)
            result[address] = {}
            result[address]['inputs'] = dbaccess.get_links(self.ds, ipstart, ipend, inbound=True, port_filter=self.port, timerange=timerange, protocol=self.protocol)
            result[address]['outputs'] = dbaccess.get_links(self.ds, ipstart, ipend, inbound=False, port_filter=self.port, timerange=timerange, protocol=self.protocol)

            # remove duplicate protocol names
            for row in result[address]['inputs']:
                row['protocols'] = ",".join(set(row['protocols'].split(',')))
            for row in result[address]['outputs']:
                row['protocols'] = ",".join(set(row['protocols'].split(',')))

        return json.dumps(result, default=decimal_default)

    def parse_request(self, get_data):
        if "address" in get_data:
            self.addresses = get_data['address'].split(",")

        if "filter" in get_data:
            self.port = get_data['filter']

        if "tstart" in get_data:
            try:
                self.timestart = int(get_data['tstart'])
            except ValueError:
                pass

        if "tend" in get_data:
            try:
                self.timeend = int(get_data['tend'])
            except ValueError:
                pass

        if "protocol" in get_data and get_data['protocol'] != "ALL":
            self.protocol = get_data['protocol']

        if "ds" in get_data:
            ds_match = re.search("(\d+)", get_data['ds'])
            if ds_match:
                self.ds = int(ds_match.group())

    def GET(self):
        """
        The expected GET data includes:
            'address': comma-seperated list of dotted-decimal IP addresses.
                Each address is only as long as the subnet,
                    so 12.34.0.0/16 would be written as 12.34
                A request for 1.2.3.0/24, 192.168.0.0/16, and 21.0.0.0/8
                    would be "1.2.3,192.168,21"
            'ds': string, data source. like: "ds_19_"
            'filter': optional. If included, only report links to this destination port.
            'tstart': optional. Used with 'tend'. The start of the time range to report links during.
            'tend': optional. Used with 'tstart'. The end of the time range to report links during.
        :return: A JSON-encoded dictionary where 
            the keys are the IPs requested and 
            the values are dictionaries where
                the keys are ['inputs', 'outputs'] and
                the values are lists of connections 
        """
        web.header("Content-Type", "application/json")

        self.parse_request(web.input())

        if not self.addresses:
            return json.dumps({'result': "ERROR: no 'address' specified."})
        elif self.ds == 0:
            return json.dumps({'result': "ERROR: data source ('ds') not specified."})
        else:
            return self.get_links()

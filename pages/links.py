import json
import dbaccess
import web
import decimal
import datetime
import common


# This class is for getting the links or edges connecting nodes in the graph


def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError


class Links:
    def get_links(self, addresses, port_filter, timerange, protocol):
        result = {}
        for address in addresses:
            ipstart, ipend = common.determine_range_string(address)
            result[address] = {}
            if port_filter:
                result[address]['inputs'] = dbaccess.get_links(ipstart, ipend, inbound=True, port_filter=port_filter, timerange=timerange, protocol=protocol)
                result[address]['outputs'] = dbaccess.get_links(ipstart, ipend, inbound=False, port_filter=port_filter, timerange=timerange, protocol=protocol)
            else:
                result[address]['inputs'] = dbaccess.get_links(ipstart, ipend, inbound=True, timerange=timerange, protocol=protocol)
                result[address]['outputs'] = dbaccess.get_links(ipstart, ipend, inbound=False, timerange=timerange, protocol=protocol)

            # remove duplicate protocol names
            for row in result[address]['inputs']:
                row['protocols'] = ",".join(set(row['protocols'].split(',')))
            for row in result[address]['outputs']:
                row['protocols'] = ",".join(set(row['protocols'].split(',')))

        return json.dumps(result, default=decimal_default)

    def GET(self):
        """
        The expected GET data includes:
            'address': comma-seperated list of dotted-decimal IP addresses.
                Each address is only as long as the subnet,
                    so 12.34.0.0/16 would be written as 12.34
                A request for 1.2.3.0/24, 192.168.0.0/16, and 21.0.0.0/8
                    would be "1.2.3,192.168,21"
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

        get_data = web.input()
        addresses = []
        address_str = get_data.get('address', None)
        if address_str is not None:
            addresses = address_str.split(",")
        port_filter = get_data.get('filter', '')

        timestart = get_data.get("tstart", 1)
        timeend = get_data.get("tend", 2 ** 31 - 1)
        timestart = int(timestart)
        timeend = int(timeend)
        #print("getting links from: {0} \n"
        #      "                to: {1}".format(
        #    datetime.datetime.fromtimestamp(timestart),
        #    datetime.datetime.fromtimestamp(timeend)))
        protocol = get_data.get("protocol", "ALL")
        protocol = protocol.upper()
        if protocol == "ALL":
            protocol = None

        if addresses:
            return self.get_links(addresses,
                                  port_filter=port_filter,
                                  timerange=(timestart, timeend),
                                  protocol=protocol)
        else:
            return json.dumps({'result': "ERROR: no 'address' specified."})

import json
import dbaccess
import web
import decimal
import datetime

# This class is for getting the links or edges connecting nodes in the graph


def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError


class Links:
    def get_links(self, addresses, filter, timerange):
        result = {}
        for address in addresses:
            ips = [int(i) for i in address.split(".")]
            result[address] = {}
            if filter:
                result[address]['inputs'] = dbaccess.get_links_in(*ips, filter=filter, timerange=timerange)
                result[address]['outputs'] = dbaccess.get_links_out(*ips, filter=filter, timerange=timerange)
            else:
                result[address]['inputs'] = dbaccess.get_links_in(*ips, timerange=timerange)
                result[address]['outputs'] = dbaccess.get_links_out(*ips, timerange=timerange)
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
        filter = get_data.get('filter', '')

        timestart = get_data.get("tstart", 1)
        timeend = get_data.get("tend", 2**31 - 1)
        timestart = int(timestart)
        timeend = int(timeend)
        print("getting links from: {0} \n"
              "                to: {1}".format(
            datetime.datetime.fromtimestamp(timestart),
            datetime.datetime.fromtimestamp(timeend)))
        if addresses:
            return self.get_links(addresses,
                                  filter=filter,
                                  timerange=(timestart, timeend))
        else:
            return json.dumps({'result': "ERROR: no 'address' specified."})

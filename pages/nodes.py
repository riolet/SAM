import json
import dbaccess
import web
import decimal
import common

# This class is for getting the child nodes of all nodes in a node list, for the map


def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError


class Nodes:
    def get_children(self, addresses):
        # should return JSON compatible data...for javascript on the other end.
        # result = dbaccess.connections()
        result = {}
        if not addresses:
            result["_"] = list(dbaccess.get_nodes(0x00000000, 0xFFFFFFFF))
        else:
            for address in addresses:
                ip_start, ip_end = common.determine_range_string(address)
                result[address] = list(dbaccess.get_nodes(ip_start, ip_end))

        return json.dumps(result, default=decimal_default)

    def GET(self):
        """
        The expected GET data includes:
            'address': comma-seperated list of dotted-decimal IP addresses.
                Each address is only as long as the subnet,
                    so 12.34.0.0/16 would be written as 12.34
                A request for 1.2.3.0/24, 192.168.0.0/16, and 21.0.0.0/8
                    would be "1.2.3,192.168,21"
        :return: A JSON-encoded dictionary where 
            the keys are the supplied addresses (or _ if no address) and
            the values are a list of child nodes.
        """
        web.header("Content-Type", "application/json")
        get_data = web.input()

        addresses = []
        address_str = get_data.get('address', None)
        if address_str is not None:
            addresses = address_str.split(",")

        return self.get_children(addresses)

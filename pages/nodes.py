import json
import dbaccess
import web
import decimal

# This class is for getting the child nodes of all nodes in a node list, for the map


def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError


class Nodes:
    def get_children(self, get_data):
        addresses = []
        address_str = get_data.get('address', None)
        if address_str is not None:
            addresses = address_str.split(",")

        # should return JSON compatible data...for javascript on the other end.
        # result = dbaccess.connections()
        result = {}
        if not addresses:
            result["_"] = list(dbaccess.getNodes())
        else:
            for address in addresses:
                result[address] = list(dbaccess.getNodes(*address.split(".")))

        return json.dumps(result, default=decimal_default)

    def GET(self):
        web.header("Content-Type", "application/json")
        get_data = web.input()
        return self.get_children(get_data)

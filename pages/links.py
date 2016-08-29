import json
import dbaccess
import web
import decimal


def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError

class Links:
    def get_links(self, addresses, filter):
        result = {}
        print("Searching for links for:")
        for address in addresses:
            ips = [int(i) for i in address.split(".")]
            result[address] = {}
            if filter:
                result[address]['inputs'] = dbaccess.getLinksIn(*ips, filter=filter)
                result[address]['outputs'] = dbaccess.getLinksOut(*ips, filter=filter)
            else:
                result[address]['inputs'] = dbaccess.getLinksIn(*ips)
                result[address]['outputs'] = dbaccess.getLinksOut(*ips)
        return json.dumps(result, default=decimal_default)

    def GET(self):
        web.header("Content-Type", "application/json")

        get_data = web.input()
        addresses = []
        address_str = get_data.get('address', None)
        if address_str is not None:
            addresses = address_str.split(",")
        filter = get_data.get('filter', '')
        if addresses:
            return self.get_links(addresses, filter)
        else:
            return json.dumps({})

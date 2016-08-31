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
                result[address]['inputs'] = dbaccess.getLinksIn(*ips, filter=filter, timerange=timerange)
                result[address]['outputs'] = dbaccess.getLinksOut(*ips, filter=filter, timerange=timerange)
            else:
                result[address]['inputs'] = dbaccess.getLinksIn(*ips, timerange=timerange)
                result[address]['outputs'] = dbaccess.getLinksOut(*ips, timerange=timerange)
        return json.dumps(result, default=decimal_default)

    def GET(self):
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
            return json.dumps({})

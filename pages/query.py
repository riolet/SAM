import json
import dbaccess
import web
import decimal


def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError


class Query:
    def GET(self):
        web.header("Content-Type", "application/json")

        addresses = []

        get_data = web.input()
        print("-"*50)
        print("Query: get_data is")
        print(get_data)
        print("requesting data on: ")
        address_str = get_data.get('address', None)
        if address_str is not None:
            addresses = address_str.split(",")
            for i in addresses:
                print("\t" + i)
        else:
            print("\troot nodes")
        print("-"*50)

        # should return JSON compatible data...for javascript on the other end.
        # result = dbaccess.connections()
        result = {}
        if not addresses:
            result["_"] = list(dbaccess.getNodes())
        else:
            for address in addresses:
                result[address] = list(dbaccess.getNodes(*address.split(".")))

        portFilter = get_data.get('filter', "")
        if portFilter == "":
            portFilter = -1
        else:
            portFilter = int(portFilter)

        print("filtering by " + str(portFilter))

        for children in result.values():
            for child in children:
                if "ip32" in child:
                    child.inputs = dbaccess.getLinksIn(child.ip8, child.ip16, child.ip24,
                                                       child.ip32, filter=portFilter)
                    child.outputs = dbaccess.getLinksOut(child.ip8, child.ip16, child.ip24,
                                                         child.ip32, filter=portFilter)
                elif "ip24" in child:
                    child.inputs = dbaccess.getLinksIn(child.ip8, child.ip16,
                                                       child.ip24, filter=portFilter)
                    child.outputs = dbaccess.getLinksOut(child.ip8, child.ip16,
                                                         child.ip24, filter=portFilter)
                elif "ip16" in child:
                    child.inputs = dbaccess.getLinksIn(child.ip8, child.ip16, filter=portFilter)
                    child.outputs = dbaccess.getLinksOut(child.ip8, child.ip16, filter=portFilter)
                else:
                    child.inputs = dbaccess.getLinksIn(child.ip8, filter=portFilter)
                    child.outputs = dbaccess.getLinksOut(child.ip8, filter=portFilter)

        return json.dumps(result, default=decimal_default)

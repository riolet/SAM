import json
import dbaccess
import web
import decimal
import time


def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError


class Query:
    def get_children(self, get_data):
        before = time.time()
        queries = 0
        addresses = []
        print("-" * 50)
        print("requesting data on: ")
        address_str = get_data.get('address', None)
        if address_str is not None:
            addresses = address_str.split(",")
            for i in addresses:
                print("\t" + i)
        else:
            print("\troot nodes")

        # should return JSON compatible data...for javascript on the other end.
        # result = dbaccess.connections()
        result = {}
        if not addresses:
            result["_"] = list(dbaccess.getNodes())
            queries += 1
        else:
            for address in addresses:
                result[address] = list(dbaccess.getNodes(*address.split(".")))
                queries += 1

        portFilter = get_data.get('filter', "")
        if portFilter == "":
            portFilter = -1
        else:
            portFilter = int(portFilter)

        print("time elapsed before getting links: {0:0.3f} seconds".format(time.time() - before))
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
                queries += 2

        answer = json.dumps(result, default=decimal_default)
        after = time.time()
        print("total time: {0:0.3f} seconds".format(after - before))
        print("total queries: {0}".format(queries))
        print("-" * 50)
        return answer

    def GET(self):
        web.header("Content-Type", "application/json")


        get_data = web.input()

        return self.get_children(get_data)

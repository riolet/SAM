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

        get_data = web.input()
        print(get_data)

        # should return JSON compatible data...for javascript on the other end.
        # result = dbaccess.connections()
        result = dbaccess.getNodes(
            int(get_data.get('ipA', -1)),
            int(get_data.get('ipB', -1)),
            int(get_data.get('ipC', -1)))

        rows = list(result)

        portFilter = get_data.get('filter', "")
        if portFilter == "":
            portFilter = -1
        else:
            portFilter = int(portFilter)

        print("filtering by " + str(portFilter))

        for row in rows:
            if "parent24" in row:
                row.inputs = dbaccess.getLinksIn(row.parent8, row.parent16, row.parent24, row.address, filter=portFilter)
                row.outputs = dbaccess.getLinksOut(row.parent8, row.parent16, row.parent24, row.address, filter=portFilter)
            elif "parent16" in row:
                row.inputs = dbaccess.getLinksIn(row.parent8, row.parent16, row.address, filter=portFilter)
                row.outputs = dbaccess.getLinksOut(row.parent8, row.parent16, row.address, filter=portFilter)
            elif "parent8" in row:
                row.inputs = dbaccess.getLinksIn(row.parent8, row.address, filter=portFilter)
                row.outputs = dbaccess.getLinksOut(row.parent8, row.address, filter=portFilter)
            else:
                row.inputs = dbaccess.getLinksIn(row.address, filter=portFilter)
                row.outputs = dbaccess.getLinksOut(row.address, filter=portFilter)

        return json.dumps(rows, default=decimal_default)
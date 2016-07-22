import json
import dbaccess
import web


class Query:
    # TODO: convert to POST data like pages/details
    def GET(self):
        web.header("Content-Type", "application/json")

        get_data = web.input()

        # should return JSON compatible data...for javascript on the other end.
        # result = dbaccess.connections()
        result = dbaccess.getNodes(
            int(get_data.get('ipA', -1)),
            int(get_data.get('ipB', -1)),
            int(get_data.get('ipC', -1)))

        rows = list(result)

        for row in rows:
            if "parent24" in row:
                row.inputs = dbaccess.getLinksIn(row.parent8, row.parent16, row.parent24, row.address)
                row.outputs = dbaccess.getLinksOut(row.parent8, row.parent16, row.parent24, row.address)
            elif "parent16" in row:
                row.inputs = dbaccess.getLinksIn(row.parent8, row.parent16, row.address)
                row.outputs = dbaccess.getLinksOut(row.parent8, row.parent16, row.address)
            elif "parent8" in row:
                row.inputs = dbaccess.getLinksIn(row.parent8, row.address)
                row.outputs = dbaccess.getLinksOut(row.parent8, row.address)
            else:
                row.inputs = dbaccess.getLinksIn(row.address)
                row.outputs = dbaccess.getLinksOut(row.address)

        return json.dumps(rows)
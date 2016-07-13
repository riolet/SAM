import json
import dbaccess
import web


class Query:
    def GET(self, ipA=-1, ipB=-1, ipC=-1):
        web.header("Content-Type", "application/json");

        # should return JSON compatible data...for javascript on the other end.
        # result = dbaccess.connections()
        result = dbaccess.getNodes(int(ipA), int(ipB), int(ipC))

        rows = list(result);

        for row in rows:
            if "parent24" in row:
                row.inputs = dbaccess.getLinks(row.parent8, row.parent16, row.parent24, row.address)
            elif "parent16" in row:
                row.inputs = dbaccess.getLinks(row.parent8, row.parent16, row.address)
            elif "parent8" in row:
                row.inputs = dbaccess.getLinks(row.parent8, row.address)
            else:
                row.inputs = dbaccess.getLinks(row.address)

        return json.dumps(rows)
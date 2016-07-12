import json
import dbaccess


class Query:
    def GET(self, ipA=-1, ipB=-1, ipC=-1):
        # should return JSON compatible data...for javascript on the other end.
        # result = dbaccess.connections()
        result = dbaccess.getNodes(int(ipA), int(ipB), int(ipC))

        return json.dumps(list(result))

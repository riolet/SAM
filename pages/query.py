import json
import dbaccess


class Query:
    def GET(self):
        #should return JSON compatible data...for javascript on the other end.

        result = dbaccess.connections(8)

        return json.dumps(list(result))
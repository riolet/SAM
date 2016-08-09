import json
import dbaccess
import web

class Portinfo:
    def GET(self):
        web.header("Content-Type", "application/json")

        get_data = web.input()

        # should return JSON compatible data...for javascript on the other end.
        # result = dbaccess.connections()
        port = get_data.get('port', -1)
        if "port" not in get_data:
            return json.dumps({})

        result = dbaccess.getPortInfo(port)

        return json.dumps(result)
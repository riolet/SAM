import json
import dbaccess
import web

class Portinfo:
    def GET(self):
        web.header("Content-Type", "application/json")

        get_data = web.input()
        if "port" not in get_data:
            return json.dumps({})

        # should return JSON compatible data...for javascript on the other end.
        # result = dbaccess.connections()
        port = get_data.get('port', "-1")
        port = port.split(",")
        port = [int(i) for i in port]

        result = dbaccess.getPortInfo(port)

        return json.dumps(list(result))

    def POST(self):
        web.header("Content-Type", "application/json")

        get_data = web.input()
        dbaccess.setPortInfo(get_data)

        return json.dumps({"code": 0, "message": ""})
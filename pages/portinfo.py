import json
import dbaccess
import web

# This class is for getting the aliases for a port number


class Portinfo:
    def GET(self):
        web.header("Content-Type", "application/json")

        get_data = web.input()
        if "port" not in get_data:
            return json.dumps({'result': 'ERROR: "port" not specified.'})

        # should return JSON compatible data...for javascript on the other end.
        # result = dbaccess.connections()
        port = get_data.get('port', "-1")
        port = port.split(",")
        port = [int(i) for i in port]

        result = dbaccess.get_port_info(port)

        return json.dumps(list(result))

    def POST(self):
        web.header("Content-Type", "application/json")

        get_data = web.input()
        if 'port' in get_data:
            dbaccess.set_port_info(get_data)
            result = "Success!"
        else:
            result = "ERROR: 'port' missing from request."

        return json.dumps({"result": result})

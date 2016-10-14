import json
import dbaccess
import web

# This class is for getting the aliases for a port number


class Portinfo:
    def GET(self):
        """
        The expected GET data includes:
            'port': comma-seperated list of port numbers
                A request for ports 80, 443, and 8080
                would look like: "80,443,8080"
        :return: A JSON-encoded dictionary where
            the keys are the requested ports and
            the values are dictionaries describing the port's attributes
        """
        web.header("Content-Type", "application/json")

        get_data = web.input()
        if "port" not in get_data:
            return json.dumps({'result': 'ERROR: "port" not specified.'})

        portstring = get_data.get('port', "-1")
        ports = portstring.split(",")
        ports = [int(i) for i in ports]

        port_data = dbaccess.get_port_info(ports)
        result = {str(i.port): i for i in port_data}

        return json.dumps(result)

    def POST(self):
        """
        The expected POST data includes:
            'port': The port to set data upon
            'alias_name': the new short name to give that port
            'alias_description': the new long name to give that port
            'active': (1 or 0) where 1 means use the name and 0 means use the number for display.
        :return: A JSON-encoded dictionary with one key "result" and a value of success or error.
        """
        web.header("Content-Type", "application/json")

        get_data = web.input()
        if 'port' in get_data:
            dbaccess.set_port_info(get_data)
            result = "Success!"
        else:
            result = "ERROR: 'port' missing from request."

        return json.dumps({"result": result})

import json
import web
import dbaccess
import common

class Details:
    def GET(self):
        web.header("Content-Type", "application/json")

        get_data = web.input()

        ips = [
            int(get_data.get('ip8', -1)),
            int(get_data.get('ip16', -1)),
            int(get_data.get('ip24', -1)),
            int(get_data.get('ip32', -1))
            ]

        details = dbaccess.getDetails(*ips)

        for connection in details['conn_in']:
            connection.ip = common.IPtoString(connection.ip)
        for connection in details['conn_out']:
            connection.ip = common.IPtoString(connection.ip)

        return json.dumps(details)


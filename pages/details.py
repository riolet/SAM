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
        # details['conn_in'] is a list
        # each element has an 'ip' and a 'port'


        conn_in = {}
        for connection in details['conn_in']:
            ip = common.IPtoString(connection.pop("ip"))
            if ip in conn_in:
                # add a port
                conn_in[ip] += [connection]
            else:
                # add a new entry
                conn_in[ip] = [connection]
        details['conn_in'] = conn_in

        conn_out = {}
        for connection in details['conn_out']:
            ip = common.IPtoString(connection.pop("ip"))
            if ip in conn_out:
                # add a port
                conn_out[ip] += [connection]
            else:
                # add a new entry
                conn_out[ip] = [connection]
        details['conn_out'] = conn_out

        return json.dumps(details)


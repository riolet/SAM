import json
import web
import dbaccess
import common

class Details:
    def GET(self):
        return "Only POST requests served."


    def POST(self):
        data = web.data()
        # data is a string.
        # if the post data was a js object, it looks like "key1=val1&key2=val2&key3=val3"

        web.header("Content-Type", "application/json")

        # data is expected to be something like 12.34.192
        ips = data.split(".")
        ips = [int(i) for i in ips]

        # return json.dumps(rows)
        details = dbaccess.getDetails(*ips)

        # details: dictionary
        # details['conn_in']: list
        # details['conn_in'][0]: WebPy storage, like dictionary
        # details['conn_in'][0].ip: long integer
        for connection in details['conn_in']:
            connection.ip = common.IPtoString(connection.ip)
        for connection in details['conn_out']:
            connection.ip = common.IPtoString(connection.ip)

        return json.dumps(details)
        # return common.render._details(details)


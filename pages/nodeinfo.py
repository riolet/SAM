import json
import dbaccess
import web

# This class is for getting and setting node metadata


class Nodeinfo:
    def GET(self):
        web.header("Content-Type", "application/json")

        get_data = web.input()
        if "node" not in get_data:
            return json.dumps({})

        node = get_data.get('node')

        node = node.split(".")
        node = [int(i) for i in node]

        result = dbaccess.getNodeInfo(*node)

        return json.dumps(list(result))

    def POST(self):
        web.header("Content-Type", "application/json")

        get_data = web.input()
        if "node" not in get_data or "alias" not in get_data:
            return json.dumps({"code": 1, "message": "'node' and 'alias' fields are required."})

        dbaccess.setNodeInfo(get_data.node, {"alias": get_data.alias})

        return json.dumps({"code": 0, "message": ""})

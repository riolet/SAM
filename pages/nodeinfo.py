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

        result = dbaccess.get_node_info(*node)

        return json.dumps(list(result))

    def POST(self):
        """
        Expects a query string including:
            node: ip address
                like "189.179.4.0/24"
                or "189.179" ( == 189.179.0.0/16)
                or "189.2.3/8" ( == 189.0.0.0/8)
            alias: (optional) new alias string for the node
            tags: (optional) comma separated string of tags to associate with this node

        :return:
        """
        web.header("Content-Type", "application/json")

        get_data = web.input()
        if "node" not in get_data:
            return json.dumps({"result": "ERROR: 'node' and 'alias' fields are required."})

        if 'alias' in get_data:
            dbaccess.set_node_info(get_data.node, {"alias": get_data.alias})

        if 'tags' in get_data:
            tags = get_data.tags.split(',')
            tags = [i for i in tags if i]
            dbaccess.set_tags(get_data.node, tags)

        if 'env' in get_data:
            env = get_data.env
            if env == "":
                env = None
            dbaccess.set_env(get_data.node, env)

        return json.dumps({"code": 0, "message": ""})

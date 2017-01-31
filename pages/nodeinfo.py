import json
import dbaccess
import web
import base
import common

# This class is for getting and setting node metadata


class Nodeinfo(base.HeadlessPost):
    """
    POST Expects a query string including:
        node: ip address
            like "189.179.4.0/24"
            or "189.179" ( == 189.179.0.0/16)
            or "189.2.3/8" ( == 189.0.0.0/8)
        alias: (optional) new alias string for the node
        tags: (optional) comma separated string of tags to associate with this node
        env: (optional) string, this host's environment category

    :return:
    """
    def decode_get_request(self, data):
        node = data.get('node')
        if not node:
            raise base.RequiredKey('node', 'node')

        return common.IPStringtoInt(node)

    def perform_get_command(self, request):
        raise NotImplementedError

    def encode_get_response(self, response):
        return response

    def decode_post_request(self, data):
        node = data.get('node')
        if not node:
            raise base.RequiredKey('node', 'node')

        alias = data.get('alias')
        tags = data.get('tags')
        env = data.get('env')

        request = {'node': node}
        if alias is not None:
            request['alias'] = alias
        if tags is not None:
            request['tags'] = tags
        if env is not None:
            request['env'] = env

        return request

    def perform_post_command(self, request):
        node = request.pop('node')
        for key, value in request.iteritems():
            if key == 'alias':
                common.nodes.set_alias(node, value)
            elif key == 'tags':
                tags = filter(lambda x: x, value.split(','))
                common.nodes.set_tags(node, tags)
            elif key == 'env':
                if value:
                    common.nodes.set_env(node, value)
                else:
                    common.nodes.set_env(node, None)
            else:
                print("Error in nodeinfo, unrecognized assignment {0} = {1}".format(key, value))
        return 0, "Success"

    def encode_post_response(self, response):
        return {'code': response[0], 'message': response[1]}

#    def GET(self):
#
#        get_data = web.input()
#        if "node" not in get_data:
#            return json.dumps({})
#
#        node = get_data.get('node')
#
#        node = node.split(".")
#        node = [int(i) for i in node]
#
#        result = dbaccess.get_node_info(*node)
#
#        return json.dumps(list(result))

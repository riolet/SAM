import re
import base
import sam.models.nodes
from sam import errors
from sam import common

# This class is for getting the child nodes of all nodes in a node list, for the map


class Nodes(base.headless_post):
    """
    The expected GET data includes:
        'address': comma-seperated list of dotted-decimal IP addresses.
            Each address is only as long as the subnet,
                so 12.34.0.0/16 would be written as 12.34
            A request for 1.2.3.0/24, 192.168.0.0/16, and 21.0.0.0/8
                would be "1.2.3,192.168,21"
    :return: A JSON-encoded dictionary where
        the keys are the supplied addresses (or _ if no address) and
        the values are a list of child nodes.


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
    def __init__(self):
        base.HeadlessPost.__init__(self)
        self.flatmode_tolerance = 256
        self.nodesModel = sam.models.nodes.Nodes(common.db, self.user.viewing)

    def check_flat_tolerance(self):
        endpoints = self.nodesModel.get_all_endpoints()
        count = len(endpoints)
        return count <= self.flatmode_tolerance

    def decode_get_request(self, data):
        addresses = []
        address_str = data.get('address')
        if address_str:
            addresses = address_str.split(',')
        addresses = filter(lambda x: bool(x), addresses)

        flat = data.get('flat', 'false').lower() == 'true'

        if 'ds' in data:
            ds_match = re.search('(\d+)', data['ds'])
            if ds_match:
                ds = int(ds_match.group())
            else:
                raise errors.MalformedRequest("Could not read data source ('ds')")
        else:
            raise errors.RequiredKey('data source', 'ds')

        return {'addresses': addresses, 'flat': flat, 'ds': ds}

    def perform_get_command(self, request):
        self.require_group('read')
        if request['flat']:
            if self.check_flat_tolerance():
                response = {'flat': self.nodesModel.get_flat_nodes(request['ds'])}
            else:
                response = {'error': 'Flat mode is not supported once a graphs has exceeded {} hosts.'.format(self.flatmode_tolerance)}
        elif len(request['addresses']) == 0:
            response = {'_': self.nodesModel.get_root_nodes()}
        else:
            response = {address: self.nodesModel.get_children(address) for address in request['addresses']}
        return response

    def encode_get_response(self, response):
        return response

    def decode_post_request(self, data):
        node = data.get('node')
        if not node:
            raise errors.RequiredKey('node', 'node')

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
        self.require_group('write')
        node = request.pop('node')
        for key, value in request.iteritems():
            if key == 'alias':
                self.nodesModel.set_alias(node, value)
            elif key == 'tags':
                tags = filter(lambda x: bool(x), value.split(','))
                self.nodesModel.set_tags(node, tags)
            elif key == 'env':
                if value:
                    self.nodesModel.set_env(node, value)
                else:
                    self.nodesModel.set_env(node, None)
            else:
                print("Error in nodeinfo, unrecognized assignment {0} = {1}".format(key, value))
        return 0, "Success"

    def encode_post_response(self, response):
        return {'code': response[0], 'message': response[1]}
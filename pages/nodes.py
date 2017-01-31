import base
import models.nodes

# This class is for getting the child nodes of all nodes in a node list, for the map


class Nodes(base.Headless):
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
    """

    def decode_get_request(self, data):
        addresses = []
        address_str = data.get('address')
        if address_str:
            addresses = address_str.split(',')

        addresses = filter(lambda x: bool(x), addresses)

        return {'addresses': addresses}

    def perform_get_command(self, request):
        nodes = models.nodes.Nodes()
        if len(request['addresses']) == 0:
            response = {'_': nodes.get_root_nodes()}
        else:
            response = {address: nodes.get_children(address) for address in request['addresses']}
        return response

    def encode_get_response(self, response):
        return response

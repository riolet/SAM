import base
import models.ports
import errors

# This class is for getting the aliases for a port number


class Portinfo(base.HeadlessPost):
    """
    The expected GET data includes:
        'port': comma-seperated list of port numbers
            A request for ports 80, 443, and 8080
            would look like: "80,443,8080"
    :return: A JSON-encoded dictionary where
        the keys are the requested ports and
        the values are dictionaries describing the port's attributes

    The expected POST data includes:
        'port': The port to set data upon
        'alias_name': optional, the new short name to give that port
        'alias_description': optional, the new long name to give that port
        'active': optional, (1 or 0) where 1 means use the name and 0 means use the number for display.
    :return: A JSON-encoded dictionary with one key "result" and a value of success or error.
    """

    def decode_get_request(self, data):
        port_string = data.get('port')
        if not port_string:
            raise errors.RequiredKey('port', 'port')

        try:
            ports = [int(port) for port in port_string.split(',') if port]
        except ValueError:
            raise errors.MalformedRequest("Could not read port ('port') number. Use comma delimited list.")

        return {'ports': ports}

    def perform_get_command(self, request):
        self.require_group('read')
        portModel = models.ports.Ports(self.user.viewing)
        ports = portModel.get(request['ports'])
        return ports

    def encode_get_response(self, response):
        return {str(i.port): i for i in response}

    def decode_post_request(self, data):
        port_string = data.get('port')
        if not port_string:
            raise errors.RequiredKey('port', 'port')

        return dict(data)

    def perform_post_command(self, request):
        self.require_group('write')
        portModel = models.ports.Ports(self.user.viewing)
        port = request.pop('port')
        portModel.set(port, request)
        return 'success'

    def encode_post_response(self, response):
        return {'result': response}

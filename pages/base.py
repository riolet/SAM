import web
import json
import decimal


def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError


class MalformedRequest(Exception): pass


class RequiredKey(MalformedRequest):
    def __init__(self, name, key, *args, **kwargs):
        MalformedRequest.__init__(self, args, kwargs)
        self.message = "Missing key: {name} ('{key}') not specified.".format(name=name, key=key)


class Headless:
    def __init__(self):
        self.inbound = web.input()
        self.request = None
        self.response = None
        self.outbound = None

    def decode_get_request(self, data):
        raise NotImplementedError("Sub-class must implement this method")

    def perform_get_command(self, request):
        raise NotImplementedError("Sub-class must implement this method")

    def encode_get_response(self, response):
        raise NotImplementedError("Sub-class must implement this method")

    def GET(self):
        web.header("Content-Type", "application/json")

        try:
            self.request = self.decode_get_request(self.inbound)
            self.response = self.perform_get_command(self.request)
            self.outbound = self.encode_get_response(self.response)
        except MalformedRequest as e:
            return json.dumps({'result': 'failure', 'message': e.message})

        return json.dumps(self.outbound, default=decimal_default)

    def POST(self):
        raise web.nomethod()


class HeadlessPost(Headless):
    def __init__(self):
        Headless.__init__(self)

    def decode_post_request(self, data):
        raise NotImplementedError("Sub-class must implement this method")

    def perform_post_command(self, request):
        raise NotImplementedError("Sub-class must implement this method")

    def encode_post_response(self, response):
        raise NotImplementedError("Sub-class must implement this method")

    def POST(self):
        self.request = self.decode_post_request(self.inbound)
        self.response = self.perform_post_command(self.request)
        self.outbound = self.encode_post_response(self.response)

        web.header("Content-Type", "application/json")
        if self.outbound:
            return json.dumps(self.outbound, default=decimal_default)
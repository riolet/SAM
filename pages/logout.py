import constants
import base
import web


class Logout(base.Headless):
    def perform_get_command(self, request):
        self.session.kill()
        raise web.seeother(constants.access_control['login_url'])

    def encode_get_response(self, response):
        pass

    def decode_get_request(self, data):
        pass

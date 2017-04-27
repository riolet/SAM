from sam import constants
from sam.pages import base
import web


class Logout(base.headless):
    def perform_get_command(self, request):
        self.session.kill()

    def encode_get_response(self, response):
        raise web.seeother(constants.find_url(constants.access_control['login_page']))

    def decode_get_request(self, data):
        pass

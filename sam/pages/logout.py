from sam import constants
from sam.pages import base
import web


class Logout(base.headless):
    def __init__(self):
        super(Logout, self).__init__()
        self.logout_redirect = '/'

    def decode_get_request(self, data):
        if 'logout_redirect' in data:
            self.logout_redirect = data['logout_redirect']

    def perform_get_command(self, request):
        self.session.kill()

    def encode_get_response(self, response):
        raise web.seeother(self.logout_redirect)

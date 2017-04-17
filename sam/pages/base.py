import decimal
import json
from sam import constants
from sam import errors
import web
from sam import common
from sam.models.user import User
import traceback


def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError


class Page(object):
    def __init__(self):
        self.session = common.session
        self.user = User(self.session)
        self.inbound = web.input()

    def require_group(self, group):
        return self.require_all_groups([group])

    def require_any_group(self, groups):
        if self.user.any_group(groups):
            return True
        raise web.seeother(constants.access_control['login_url'])

    def require_all_groups(self, groups):
        if self.user.all_groups(groups):
            return True
        raise web.seeother(constants.access_control['login_url'])


class Headed(Page):
    def __init__(self, title, header, footer):
        super(Headed, self).__init__()
        self.scripts = []
        self.styles = []
        self.page_title = title
        self.header = header
        self.footer = footer

    def render(self, page, *args, **kwargs):
        head = str(common.render._head(self.page_title, stylesheets=self.styles, scripts=self.scripts))
        if self.header:
            header = str(common.render._header(constants.navbar, self.page_title, self.user, constants.debug))
        else:
            header = ''
        page = str(getattr(common.render, page)(*args, **kwargs))
        if self.footer:
            footer = str(common.render._footer())
        else:
            footer = ''
        tail = str(common.render._tail())

        return head+header+page+footer+tail


class Headless(Page):
    def __init__(self):
        super(Headless, self).__init__()
        self.request = None
        self.response = None
        self.outbound = None

    def decode_get_request(self, data):
        """
        Use this method to figure out if the request is valid, and what parameters are being supplied
        :param data: dictionary, The GET parameters extracted from the URL query
        :return: any extracted information, as needed, to be used in `perform_get_command`.
        """
        raise NotImplementedError("Sub-class must implement this method")

    def perform_get_command(self, request):
        """
        Use this method to instantiate outside classes and call functions to do the work required to fulfill the request.
        :param request: The request parameters extracted in `decode_get_request`
        :return: The results gathered from fulfilling the request, for use in `encode_get_response`.
        """
        raise NotImplementedError("Sub-class must implement this method")

    def encode_get_response(self, response):
        """
        Transform the result data into the format that the caller understands
        :param response: The results returned from `perform_get_command`
        :return: Data ready to be json encoded and sent back to the client.
        """
        raise NotImplementedError("Sub-class must implement this method")

    def GET(self):
        """
        Entry point for GET requests to this endpoint.  Should not need to be overridden
        except to handle exceptions differently.
        :return: HTTP response data
        """
        try:
            self.request = self.decode_get_request(self.inbound)
            self.response = self.perform_get_command(self.request)
            self.outbound = self.encode_get_response(self.response)
        except errors.MalformedRequest as e:
            traceback.print_exc()
            self.outbound = {'result': 'failure', 'message': e.message}

        web.header("Content-Type", "application/json")
        return json.dumps(self.outbound, default=decimal_default)

    def POST(self):
        raise web.nomethod()


class HeadlessPost(Headless):
    def __init__(self):
        super(HeadlessPost, self).__init__()

    def decode_post_request(self, data):
        """
        Use this method to figure out if the request is valid, and what parameters are being supplied
        :param data: dictionary, The POST parameters extracted from the request body
        :return: any extracted information, as needed, to be used in `perform_post_command`.
        """
        raise NotImplementedError("Sub-class must implement this method")

    def perform_post_command(self, request):
        """
        Use this method to instantiate outside classes and call functions to do the work required to fulfill the request.
        :param request: The request parameters extracted in `decode_post_request`
        :return: The results gathered from fulfilling the request, for use in `encode_post_response`.
        """
        raise NotImplementedError("Sub-class must implement this method")

    def encode_post_response(self, response):
        """
        Transform the result data into the format that the caller understands
        :param response: The results returned from `perform_post_command`
        :return: (optional) Data ready to be json encoded and sent back to the client.
        """
        raise NotImplementedError("Sub-class must implement this method")

    def require_ownership(self):
        if not self.user.may_post():
            raise web.unauthorized("Cannot modify data. Do you have an active account?")

    def POST(self):
        """
        Entry point for POST requests to this endpoint.  Should not need to be overridden
        except to handle exceptions differently.
        :return: HTTP response data
        """

        self.require_ownership()

        try:
            self.request = self.decode_post_request(self.inbound)
            self.response = self.perform_post_command(self.request)
            self.outbound = self.encode_post_response(self.response)
        except Exception as e:
            traceback.print_exc()
            self.outbound = {'result': 'failure', 'message': e.message}

        web.header("Content-Type", "application/json")
        if self.outbound:
            return json.dumps(self.outbound, default=decimal_default)
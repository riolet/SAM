# coding=utf-8
import importlib
import decimal
import os
import json
from sam import constants
from sam import errors
import web
from sam import common
from sam.models.user import User
import traceback


def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return obj.__float__()
    raise TypeError


class Page(object):

    def __init__(self):
        self.session = common.session
        self.user = User(self.session)
        self.language = self.session.get('lang', constants.default_lang)
        self.strings = importlib.import_module("sam.local." + self.language)
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

    def require_ownership(self):
        if not self.user.may_post():
            raise web.unauthorized("Cannot modify data. Do you have an active account?")

page = Page


class Headed(object):
    def __init__(self, header, footer):
        self.page = page()
        self.scripts = []
        self.styles = []
        self.page_title = "Untitled"
        self.header = header
        self.footer = footer

    def set_title(self, title):
        self.page_title = title

    def render(self, page_template, *args, **kwargs):
        lang_prefix = '{}{}'.format(self.page.language, os.path.sep)
        head = str(common.renderer.render('_head', self.page_title, lang=self.page.language, stylesheets=self.styles, scripts=self.scripts))
        navbar = constants.get_navbar(self.page.language)
        if web.ctx.env['QUERY_STRING']:
            uri_path = "{}?{}".format(web.ctx.env['PATH_INFO'], web.ctx.env['QUERY_STRING'])
        else:
            uri_path = web.ctx.env['PATH_INFO']

        if self.header:
            if self.page.language == "en":
                lang = ("version française", "/fr{}".format(uri_path))
            else:
                lang = ("English version", "/en{}".format(uri_path))
            header = str(common.renderer.render(lang_prefix + '_header', navbar, self.page_title, self.page.user, constants.debug, web.ctx.path, constants.access_control, lang))
        else:
            header = ''
        try:
            body = str(common.renderer.render(lang_prefix + page_template, *args, **kwargs))
        except:
            body = str(common.renderer.render(page_template, *args, **kwargs))
        if self.footer:
            links = {"English": "/en{}".format(uri_path),
                     "Française": "/fr{}".format(uri_path)}
            footer = str(common.renderer.render(lang_prefix + '_footer', links))
        else:
            footer = ''
        tail = str(common.renderer.render('_tail'))

        return head+header+body+footer+tail


headed = Headed


class Headless(object):
    def __init__(self):
        self.page = page()
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
        self.page.require_group('read')
        try:
            self.request = self.decode_get_request(self.page.inbound)
            self.response = self.perform_get_command(self.request)
            self.outbound = self.encode_get_response(self.response)
        except errors.MalformedRequest as e:
            traceback.print_exc()
            self.outbound = {'result': 'failure', 'message': e.message}

        web.header("Content-Type", "application/json")
        return json.dumps(self.outbound, default=decimal_default)

    def POST(self):
        raise web.nomethod()


headless = Headless


class HeadlessPost(headless):
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

    def POST(self):
        """
        Entry point for POST requests to this endpoint.  Should not need to be overridden
        except to handle exceptions differently.
        :return: HTTP response data
        """
        self.page.require_ownership()
        self.page.require_all_groups(['read', 'write'])

        try:
            self.request = self.decode_post_request(self.page.inbound)
            self.response = self.perform_post_command(self.request)
            self.outbound = self.encode_post_response(self.response)
        except Exception as e:
            traceback.print_exc()
            self.outbound = {'result': 'failure', 'message': e.message}

        web.header("Content-Type", "application/json")
        if self.outbound:
            return json.dumps(self.outbound, default=decimal_default)


headless_post = HeadlessPost

# coding=utf-8
from spec.python import db_connection
import sam.pages.base
import web
from sam import constants
from sam import common
import pytest


def test_page():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = sam.pages.base.Page()
        p.user.groups = {'garbage'}
        with pytest.raises(Exception):
            assert p.require_group('write')

        p.user.groups = {'read', 'write', 'speak'}
        assert p.require_group('read')
        assert p.require_group('write')
        assert p.require_any_group({'read'})
        assert p.require_any_group({'reduce', 'reuse', 'recycle', 'write'})
        assert p.require_all_groups({'read', 'write'})
        with pytest.raises(Exception):
            assert p.require_all_groups({'read', 'write', 'arithemetic'})


def test_headed():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True, mock_render=True):
        p = sam.pages.base.Headed(True, True)
        p.set_title('TestTitle')
        p.styles = ['1', '2']
        p.scripts = ['3', '4']
        web.ctx.path = "/sam/testpage"
        web.ctx.env = {'PATH_INFO': '/sam/testpage', 'QUERY_STRING': ''}
        p.render('testPage', 'arg1', 'arg2', start=12, end=15)
        calls = common.renderer.calls
        assert calls[0] == ('render', ('_head', 'TestTitle'), {'lang': 'en', 'stylesheets': ['1', '2'], 'scripts': ['3', '4']})
        assert calls[1] == ('render', ('en/_header', constants.get_navbar('en'), 'TestTitle', p.page.user, constants.debug, "/sam/testpage", constants.access_control, ('version française', '/fr/sam/testpage')), {})
        assert calls[2] == ('render', ('en/testPage', 'arg1', 'arg2'), {'start': 12, 'end': 15})
        assert calls[3] == ('render', ('en/_footer', {'English': '/en/sam/testpage', 'Française': '/fr/sam/testpage'}), {})
        assert calls[4] == ('render', ('_tail', ), {})

        common.renderer.clear()
        p = sam.pages.base.Headed(True, False)
        p.set_title('TestTitle')
        p.render('testPage')
        calls = [x[1][0] for x in common.renderer.calls]
        assert calls == ['_head', 'en/_header', 'en/testPage', '_tail']

        common.renderer.clear()
        p = sam.pages.base.Headed(False, False)
        p.set_title('TestTitle')
        p.render('testPage')
        calls = [x[1][0] for x in common.renderer.calls]
        assert calls == ['_head', 'en/testPage', '_tail']

        common.renderer.clear()
        p = sam.pages.base.Headed(False, True)
        p.set_title('TestTitle')
        p.render('testPage')
        calls = [x[1][0] for x in common.renderer.calls]
        assert calls == ['_head', 'en/testPage', 'en/_footer', '_tail']


def test_headless():
    decode_calls = []
    perform_calls = []
    encode_calls = []

    class headless_t(sam.pages.base.Headless):
        def decode_get_request(self, data):
            decode_calls.append(data.copy())
            return {'a': 1, 'b': 2}

        def perform_get_command(self, request):
            perform_calls.append(request.copy())
            return {'z': 9, 'x': 8}

        def encode_get_response(self, response):
            encode_calls.append(response.copy())
            return 'abc', 123

    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        # web.input must be set before instantiating the class
        web.input = lambda: {'input': True}
        web.ctx['headers'] = []
        p = headless_t()
        resp = p.GET()

        assert decode_calls == [{'input': True}]
        assert perform_calls == [{'a': 1, 'b': 2}]
        assert encode_calls == [{'x': 8, 'z': 9}]
        assert resp == '["abc", 123]'

        with pytest.raises(web.nomethod):
            p.POST()


def test_headlesspost():
    decode_calls = []
    perform_calls = []
    encode_calls = []

    class headless_t(sam.pages.base.HeadlessPost):
        def decode_post_request(self, data):
            decode_calls.append(data.copy())
            return {'a': 1, 'b': 2}

        def perform_post_command(self, request):
            perform_calls.append(request.copy())
            return {'z': 9, 'x': 8}

        def encode_post_response(self, response):
            encode_calls.append(response.copy())
            return 'abc', 123

        def require_ownership(self):
            return True

    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        # web.input must be set before instantiating the class
        web.input = lambda: {'postinput': 'test'}
        web.ctx['headers'] = []
        p = headless_t()
        resp = p.POST()

        assert decode_calls == [{'postinput': 'test'}]
        assert perform_calls == [{'a': 1, 'b': 2}]
        assert encode_calls == [{'x': 8, 'z': 9}]
        assert resp == '["abc", 123]'

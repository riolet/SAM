from spec.python import db_connection
import pages.base
import web
import constants
import common
import pytest

# web.seeother = Exception


def test_page():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = pages.base.Page()
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
        p = pages.base.Headed('TestTitle', True, True)
        p.styles = ['1', '2']
        p.scripts = ['3', '4']
        page = p.render('testPage', 'arg1', 'arg2', start=12, end=15)
        calls = common.render.calls
        assert calls[0] == ('_head', ('TestTitle',), {'stylesheets': ['1', '2'], 'scripts': ['3', '4']})
        assert calls[1] == ('_header', (constants.navbar, 'TestTitle', p.user, constants.debug), {})
        assert calls[2] == ('testPage', ('arg1', 'arg2'), {'start': 12, 'end': 15})
        assert calls[3] == ('_footer', (), {})
        assert calls[4] == ('_tail', (), {})

        common.render.clear()
        p = pages.base.Headed('TestTitle', True, False)
        page = p.render('testPage')
        calls = [x[0] for x in common.render.calls]
        assert calls == ['_head', '_header', 'testPage', '_tail']

        common.render.clear()
        p = pages.base.Headed('TestTitle', False, False)
        page = p.render('testPage')
        calls = [x[0] for x in common.render.calls]
        assert calls == ['_head', 'testPage', '_tail']

        common.render.clear()
        p = pages.base.Headed('TestTitle', False, True)
        page = p.render('testPage')
        calls = [x[0] for x in common.render.calls]
        assert calls == ['_head', 'testPage', '_footer', '_tail']

def test_headless():
    decode_calls = []
    perform_calls = []
    encode_calls = []
    class headless_t(pages.base.Headless):
        def decode_get_request(self, data):
            decode_calls.append(data.copy())
            return {'a': 1, 'b': 2}
        def perform_get_command(self, request):
            perform_calls.append(request.copy())
            return {'z': 9, 'x': 8}
        def encode_get_response(self, response):
            encode_calls.append(response.copy())
            return ('abc', 123)

    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        # web.input must be set before instantiating the class
        web.input = lambda: {'input': True}
        web.ctx['headers'] = []
        p = headless_t()
        response = p.GET()

        assert decode_calls == [{'input': True}]
        assert perform_calls == [{'a': 1, 'b': 2}]
        assert encode_calls == [{'x': 8, 'z': 9}]
        assert response == '["abc", 123]'

        with pytest.raises(web.nomethod):
            p.POST()

def test_headlesspost():
    decode_calls = []
    perform_calls = []
    encode_calls = []

    class headless_t(pages.base.HeadlessPost):
        def decode_post_request(self, data):
            decode_calls.append(data.copy())
            return {'a': 1, 'b': 2}
        def perform_post_command(self, request):
            perform_calls.append(request.copy())
            return {'z': 9, 'x': 8}
        def encode_post_response(self, response):
            encode_calls.append(response.copy())
            return ('abc', 123)
        def require_ownership(self):
            return True

    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        # web.input must be set before instantiating the class
        web.input = lambda: {'postinput': 'test'}
        web.ctx['headers'] = []
        p = headless_t()
        response = p.POST()

        assert decode_calls == [{'postinput': 'test'}]
        assert perform_calls == [{'a': 1, 'b': 2}]
        assert encode_calls == [{'x': 8, 'z': 9}]
        assert response == '["abc", 123]'

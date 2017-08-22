# coding=utf-8
from spec.python import db_connection
import web
import pytest
import sam.pages.login
from sam import common
from sam import constants
from sam import errors


def test_render():
    with db_connection.env(mock_input=True, login_active=True, mock_session=True, mock_render=True):
        p = sam.pages.login.Login_LDAP()
        common.session.clear()
        web.ctx.env = {'PATH_INFO': '/sam/testpage', 'QUERY_STRING': ''}
        dummy = p.GET()
        calls = common.renderer.calls
        assert calls[0] == ('render', ('_head', 'Login',), {'lang': 'en', 'stylesheets': ['/static/css/general.css'], 'scripts': []})
        assert calls[1] == ('render', ('en/login', '/login',), {})
        assert calls[2] == ('render', ('en/_footer', {'English': '/en/sam/testpage', 'Française': '/fr/sam/testpage'}), {})
        assert calls[3] == ('render', ('_tail', ), {})
        assert dummy == "NoneNoneNoneNone"


def test_decode_post():
    with db_connection.env(mock_input=True, mock_session=True):
        p = sam.pages.login.Login_LDAP()
        common.session.clear()
        with pytest.raises(errors.MalformedRequest):
            p.decode_post_request({'user': 'bob'})
        p.errors = []
        with pytest.raises(errors.MalformedRequest):
            p.decode_post_request({'password': 'bobpass'})
        p.errors = []
        with pytest.raises(errors.MalformedRequest):
            p.decode_post_request({'user': '', 'password': 'bobpass'})
        p.errors = []
        with pytest.raises(errors.MalformedRequest):
            p.decode_post_request({'user': 'bob', 'password': ''})
        p.errors = []
        actual = p.decode_post_request({'user': 'bob', 'password': 'bobpass'})
        expected = {'user': 'bob', 'password': 'bobpass'}
        assert actual == expected


def test_decode_connection_string():
    with db_connection.env(mock_input=True, mock_session=True):
        p = sam.pages.login.Login_LDAP()
        cs = 'ldaps://ipa.demo1.freeipa.org/CN=users,CN=accounts,DC=demo1,DC=freeipa,DC=org'
        address, ns = p.decode_connection_string(cs)
        assert address == 'ldaps://ipa.demo1.freeipa.org'
        assert ns == 'CN=users,CN=accounts,DC=demo1,DC=freeipa,DC=org'


def test_connect():
    # TODO: I don't control this test server. This could break.
    with db_connection.env(mock_input=True, mock_session=True):
        p = sam.pages.login.Login_LDAP()
        p.server_address = 'ldaps://ipa.demo1.freeipa.org'
        p.namespace = 'CN=users,CN=accounts,DC=demo1,DC=freeipa,DC=org'

        # wrong password
        request = {
            'user': 'bob',
            'password': 'bobpass'
        }
        with pytest.raises(errors.AuthenticationError):
            p.perform_post_command(request)

        # correct details
        #request = {
        #    'user': 'admin',
        #    'password': 'Secret123',
        #}
        #assert p.perform_post_command(request)

        # wrong url
        p.server_address = 'ldaps://ipa.demo1.garbage.org'
        with pytest.raises(errors.AuthenticationError):
            p.perform_post_command(request)

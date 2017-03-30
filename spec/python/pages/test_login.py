from spec.python import db_connection

import pytest
import web
import pages.login
import common
import constants
import errors
import json
import urllib

common.session = {}
db = db_connection.db
sub_id = db_connection.default_sub
ds_full = db_connection.dsid_default

def test_render():
    web.input_real = web.input
    try:
        web.input = lambda: {}
        common.render = db_connection.mocker()
        p = pages.login.Login_LDAP()
        common.session.clear()
        dummy = p.GET()
        calls = common.render.calls
        assert calls[0] == ('_head', ('Login',), {'stylesheets': ['/static/css/general.css'], 'scripts': []})
        assert calls[1] == ('login', (constants.access_control['login_url'],), {})
        assert calls[2] == ('_footer', (), {})
        assert calls[3] == ('_tail', (), {})
        assert dummy == "NoneNoneNoneNone"
    finally:
        web.input = web.input_real


def test_decode_post():
    web.input_real = web.input
    try:
        web.input = lambda: {}
        p = pages.login.Login_LDAP()
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
    finally:
        web.input = web.input_real


def test_decode_connection_string():
    web.input_real = web.input
    try:
        web.input = lambda: {}
        p = pages.login.Login_LDAP()
        cs = 'ldaps://ipa.demo1.freeipa.org/CN=users,CN=accounts,DC=demo1,DC=freeipa,DC=org'
        address, ns = p.decode_connection_string(cs)
        assert address == 'ldaps://ipa.demo1.freeipa.org'
        assert ns == 'CN=users,CN=accounts,DC=demo1,DC=freeipa,DC=org'
    finally:
        web.input = web.input_real

def test_connect():
    # TODO: I don't control the test server. This could break.
    web.input_real = web.input
    try:
        web.input = lambda: {}
        p = pages.login.Login_LDAP()
        cs = 'ldaps://ipa.demo1.freeipa.org/CN=users,CN=accounts,DC=demo1,DC=freeipa,DC=org'
        address, ns = p.decode_connection_string(cs)
        p.server_address = 'ldaps://ipa.demo1.freeipa.org'
        p.namespace = 'CN=users,CN=accounts,DC=demo1,DC=freeipa,DC=org'

        request = {
            'user': 'bob',
            'password': 'bobpass'
        }
        with pytest.raises(errors.AuthenticationError):
            p.perform_post_command(request)
        request = {
            'user': 'admin',
            'password': 'Secret123',
        }
        assert p.perform_post_command(request)
        p.server_address = 'ldaps://ipa.demo1.garbage.org'
        with pytest.raises(errors.AuthenticationError):
            p.perform_post_command(request)
    finally:
        web.input = web.input_real

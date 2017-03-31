import db_connection
import constants
import wsgiserver
import web

app = web.application(constants.urls, globals())


def test_404():
    with db_connection.env(login_active=False):
        req = app.request('/invalidendpoint', method='GET')
        assert req.status == "404 Not Found"
        req = app.request('/invalidendpoint', method='POST')
        assert req.status == "404 Not Found"


def test_exists_map():
    with db_connection.env(login_active=False):
        req = app.request('/map', method='POST')
        assert req.status == "405 Method Not Allowed"
        req = app.request('/map', method='GET')
        assert req.status == "200 OK"


def test_exists_stats():
    with db_connection.env(login_active=False):
        req = app.request('/stats', 'GET')
        assert req.status == "200 OK"
        req = app.request('/stats', 'POST')
        assert req.status == "405 Method Not Allowed"


def test_exists_nodes():
    with db_connection.env(login_active=False):
        req = app.request('/nodes', 'GET')
        assert req.status == "200 OK"
        req = app.request('/nodes', 'POST')
        assert req.status == "200 OK"


def test_exists_links():
    with db_connection.env(login_active=False):
        req = app.request('/links', 'GET')
        assert req.status == "200 OK"
        req = app.request('/links', 'POST')
        assert req.status == "405 Method Not Allowed"


def test_exists_details():
    with db_connection.env(login_active=False):
        req = app.request('/details', 'GET')
        assert req.status == "200 OK"
        req = app.request('/details', 'POST')
        assert req.status == "405 Method Not Allowed"


def test_exists_portinfo():
    with db_connection.env(login_active=False):
        req = app.request('/portinfo', 'GET')
        assert req.status == "200 OK"
        req = app.request('/portinfo', 'POST')
        assert req.status == "200 OK"


def test_exists_metadata():
    with db_connection.env(login_active=False):
        req = app.request('/metadata', 'GET')
        assert req.status == "200 OK"
        req = app.request('/metadata', 'POST')
        assert req.status == "405 Method Not Allowed"


def test_exists_table():
    with db_connection.env(login_active=False):
        req = app.request('/table', 'GET')
        assert req.status == "200 OK"
        req = app.request('/table', 'POST')
        assert req.status == "405 Method Not Allowed"

def test_exists_settings():
    with db_connection.env(login_active=False):
        req = app.request('/settings', 'GET')
        assert req.status == "200 OK"
        req = app.request('/settings', 'POST')
        assert req.status == "200 OK"

def test_exists_settings_page():
    with db_connection.env(login_active=False):
        req = app.request('/settings_page', 'GET')
        assert req.status == "200 OK"
        req = app.request('/settings_page', 'POST')
        assert req.status == "405 Method Not Allowed"

def test_exists_login_LDAP():
    with db_connection.env(login_active=True):
        req = app.request('/login_LDAP', 'GET')
        assert req.status == "200 OK"
        req = app.request('/login_LDAP', 'POST')
        assert req.status == "200 OK"

def test_exists_logout():
    with db_connection.env(login_active=True, mock_session=True):
        req = app.request('/logout', 'GET')
        assert req.status == "303 See Other"
        req = app.request('/logout', 'POST')
        assert req.status == "405 Method Not Allowed"

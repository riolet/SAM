import server
import wsgiserver
import web

app = web.application(server.urls, globals())
wsgiapp = web.application(wsgiserver.urls, globals(), autoreload=False)


def test_404():
    req = app.request('/invalidendpoint', method='GET')
    assert req.status == "404 Not Found"
    req = app.request('/invalidendpoint', method='POST')
    assert req.status == "404 Not Found"

    req = wsgiapp.request('/invalidendpoint', method='GET')
    assert req.status == "404 Not Found"
    req = wsgiapp.request('/invalidendpoint', method='POST')
    assert req.status == "404 Not Found"


def test_exists_map():
    req = app.request('/map', method='POST')
    assert req.status == "405 Method Not Allowed"
    req = app.request('/map', method='GET')
    assert req.status == "200 OK"

    req = wsgiapp.request('/map', method='POST')
    assert req.status == "405 Method Not Allowed"
    req = wsgiapp.request('/map', method='GET')
    assert req.status == "200 OK"


def test_exists_stats():
    req = app.request('/stats', 'GET')
    assert req.status == "200 OK"
    req = app.request('/stats', 'POST')
    assert req.status == "405 Method Not Allowed"

    req = wsgiapp.request('/stats', 'GET')
    assert req.status == "200 OK"
    req = wsgiapp.request('/stats', 'POST')
    assert req.status == "405 Method Not Allowed"


def test_exists_nodes():
    req = app.request('/nodes', 'GET')
    assert req.status == "200 OK"
    req = app.request('/nodes', 'POST')
    assert req.status == "405 Method Not Allowed"

    req = wsgiapp.request('/nodes', 'GET')
    assert req.status == "200 OK"
    req = wsgiapp.request('/nodes', 'POST')
    assert req.status == "405 Method Not Allowed"


def test_exists_links():
    req = app.request('/links', 'GET')
    assert req.status == "200 OK"
    req = app.request('/links', 'POST')
    assert req.status == "405 Method Not Allowed"

    req = wsgiapp.request('/links', 'GET')
    assert req.status == "200 OK"
    req = wsgiapp.request('/links', 'POST')
    assert req.status == "405 Method Not Allowed"


def test_exists_details():
    req = app.request('/details', 'GET')
    assert req.status == "200 OK"
    req = app.request('/details', 'POST')
    assert req.status == "405 Method Not Allowed"

    req = wsgiapp.request('/details', 'GET')
    assert req.status == "200 OK"
    req = wsgiapp.request('/details', 'POST')
    assert req.status == "405 Method Not Allowed"


def test_exists_portinfo():
    req = app.request('/portinfo', 'GET')
    assert req.status == "200 OK"
    req = app.request('/portinfo', 'POST')
    assert req.status == "200 OK"

    req = wsgiapp.request('/portinfo', 'GET')
    assert req.status == "200 OK"
    req = wsgiapp.request('/portinfo', 'POST')
    assert req.status == "200 OK"


def test_exists_nodeinfo():
    req = app.request('/nodeinfo', 'GET')
    assert req.status == "200 OK"
    req = app.request('/nodeinfo', 'POST')
    assert req.status == "200 OK"

    req = wsgiapp.request('/nodeinfo', 'GET')
    assert req.status == "200 OK"
    req = wsgiapp.request('/nodeinfo', 'POST')
    assert req.status == "200 OK"


def test_exists_metadata():
    req = app.request('/metadata', 'GET')
    assert req.status == "200 OK"
    req = app.request('/metadata', 'POST')
    assert req.status == "405 Method Not Allowed"

    req = wsgiapp.request('/metadata', 'GET')
    assert req.status == "200 OK"
    req = wsgiapp.request('/metadata', 'POST')
    assert req.status == "405 Method Not Allowed"


def test_exists_table():
    req = app.request('/table', 'GET')
    assert req.status == "200 OK"
    req = app.request('/table', 'POST')
    assert req.status == "405 Method Not Allowed"

    req = wsgiapp.request('/table', 'GET')
    assert req.status == "200 OK"
    req = wsgiapp.request('/table', 'POST')
    assert req.status == "405 Method Not Allowed"

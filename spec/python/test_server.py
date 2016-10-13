import server
import web

app = web.application(server.urls, globals())


def test_404():
    req = app.request('/invalidendpoint', method='POST')
    assert req.status == "404 Not Found"


def test_exists_details():
    req = app.request('/details', 'GET')
    assert req.status == "200 OK"
    req = app.request('/details', 'POST')
    assert req.status == "405 Method Not Allowed"


def test_exists_links():
    req = app.request('/links', 'GET')
    assert req.status == "200 OK"
    req = app.request('/links', 'POST')
    assert req.status == "405 Method Not Allowed"


def test_exists_map():
    req = app.request('/map', method='POST')
    assert req.status == "405 Method Not Allowed"
    req = app.request('/map', method='GET')
    assert req.status == "200 OK"


def test_exists_nodeinfo():
    req = app.request('/nodeinfo', 'GET')
    assert req.status == "200 OK"
    req = app.request('/nodeinfo', 'POST')
    assert req.status == "200 OK"


def test_exists_portinfo():
    req = app.request('/portinfo', 'GET')
    assert req.status == "200 OK"
    req = app.request('/portinfo', 'POST')
    assert req.status == "200 OK"


def test_exists_stats():
    req = app.request('/stats', 'GET')
    assert req.status == "200 OK"
    req = app.request('/stats', 'POST')
    assert req.status == "405 Method Not Allowed"

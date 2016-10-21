import server
import web

app = web.application(server.urls, globals())


def test_exists():
    req = app.request('/map')
    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "text/html; charset=utf-8"
    lines = req.data.splitlines()
    assert lines[0] == "<!DOCTYPE html>"
    assert lines[-1] == "</html>"

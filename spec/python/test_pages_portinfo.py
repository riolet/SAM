import server
import web
import urllib
import json
from datetime import datetime
import time

app = web.application(server.urls, globals())


def test_simple_request0():
    req = app.request('/portinfo', 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert data.keys() == ['result']
    assert data['result'].startswith("ERROR")
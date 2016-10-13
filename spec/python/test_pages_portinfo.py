import server
import web
import urllib
import json
from datetime import datetime
import time

app = web.application(server.urls, globals())


def test_get_empty():
    req = app.request('/portinfo', 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert data.keys() == ['result']
    assert data['result'].startswith("ERROR")


def test_get_single():
	test_port = 80
    input_data = {"port": test_port}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/portinfo?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert data.keys() == [test_port]
    assert sorted(data[test_port].keys()) == ['active', 'alias_description', 'alias_name', 'description', 'name', 'port']


def test_get_missing():
	test_port = 4
    input_data = {"port": test_port}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/portinfo?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert data == {}


def test_get_many():
	test_ports = "3,4,5,6"
    input_data = {"port": test_ports}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/portinfo?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert sorted(data.keys()) == ['3', '5']
    assert sorted(data['3'].keys()) == ['active', 'alias_description', 'alias_name', 'description', 'name', 'port']
    assert sorted(data['5'].keys()) == ['active', 'alias_description', 'alias_name', 'description', 'name', 'port']
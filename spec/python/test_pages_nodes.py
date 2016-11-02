import server
import web
import json
import urllib
import common

app = web.application(server.urls, globals())


def test_blank():
    req = app.request('/nodes', 'GET')
    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert data.keys() == [u'_']
    assert sorted(data['_'][0].keys()) == [u'alias', u'ipend', u'ipstart', u'radius', u'subnet', u'x', u'y']
    assert [common.IPtoString(i['ipstart']) for i in data['_']] == \
           ['21.0.0.0', '53.0.0.0', '79.0.0.0', '110.0.0.0', '121.0.0.0', '136.0.0.0', '189.0.0.0', '208.0.0.0']


def test_8():
    input_data = {"address": "79"}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/nodes?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert data.keys() == ['79']
    assert sorted(data['79'][0].keys()) == [u'alias', u'ipend', u'ipstart', u'radius', u'subnet', u'x', u'y']
    assert [common.IPtoString(i['ipstart']) for i in data['79']] == \
           ['79.35.0.0', '79.80.0.0', '79.106.0.0', '79.119.0.0', '79.146.0.0', '79.179.0.0', '79.229.0.0']


def test_16():
    input_data = {"address": "79.106"}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/nodes?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert data.keys() == ['79.106']
    assert sorted(data['79.106'][0].keys()) == [u'alias', u'ipend', u'ipstart', u'radius', u'subnet', u'x', u'y']
    assert [common.IPtoString(i['ipstart']) for i in data['79.106']] == \
           ['79.106.151.0', '79.106.191.0', '79.106.226.0']


def test_24():
    input_data = {"address": "79.106.151"}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/nodes?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert data.keys() == ['79.106.151']
    assert sorted(data['79.106.151'][0].keys()) == [u'alias', u'ipend', u'ipstart', u'radius', u'subnet', u'x', u'y']
    assert [common.IPtoString(i['ipstart']) for i in data['79.106.151']] == \
           ['79.106.151.27', '79.106.151.50', '79.106.151.92']


def test_32():
    input_data = {"address": "79.106.151.50"}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/nodes?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert data['79.106.151.50'] == []


def test_multiple():
    input_data = {"address": "79,79.106,79.106.151,79.106.151.50"}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/nodes?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert sorted(data.keys()) == ['79', '79.106', '79.106.151', '79.106.151.50']
    assert len(data['79.106.151.50']) == 0
    assert len(data['79.106.151']) == 3
    assert len(data['79.106']) == 3
    assert len(data['79']) == 7

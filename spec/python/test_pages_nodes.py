import server
import web
import json
import urllib

app = web.application(server.urls, globals())


def test_blank():
    req = app.request('/nodes', 'GET')
    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert data.keys() == [u'_']
    assert sorted(data['_'][0].keys()) == [u'alias', u'children', u'connections', u'ip8', u'radius', u'x', u'y']
    assert [i['ip8'] for i in data['_']] == [21, 53, 79, 110, 121, 136, 189, 208]


def test_8():
    input_data = {"address": "79"}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/nodes?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert data.keys() == ['79']
    assert sorted(data['79'][0].keys()) == [u'alias', u'children', u'connections', u'ip16', u'ip8', u'radius', u'x',
                                            u'y']
    assert [i['ip16'] for i in data['79']] == [35, 80, 106, 119, 146, 179, 229]


def test_16():
    input_data = {"address": "79.106"}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/nodes?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert data.keys() == ['79.106']
    assert sorted(data['79.106'][0].keys()) == [u'alias', u'children', u'connections', u'ip16', u'ip24', u'ip8',
                                                u'radius', u'x', u'y']
    assert [i['ip24'] for i in data['79.106']] == [151, 191, 226]


def test_24():
    input_data = {"address": "79.106.151"}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/nodes?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert data.keys() == ['79.106.151']
    assert sorted(data['79.106.151'][0].keys()) == [u'alias', u'children', u'connections', u'ip16', u'ip24', u'ip32',
                                                    u'ip8', u'radius', u'x', u'y']
    assert [i['ip32'] for i in data['79.106.151']] == [27, 50, 92]


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

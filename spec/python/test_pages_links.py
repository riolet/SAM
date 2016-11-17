import server
import web
import urllib
import json
from datetime import datetime
import time

app = web.application(server.urls, globals())


def test_empty_request():
    req = app.request('/links', 'GET')
    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert data.keys() == ['result']
    assert data['result'].startswith("ERROR")


def test_simple_request8():
    test_ip = '79'
    input_data = {"address": test_ip}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/links?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert data.keys() == [test_ip]
    assert sorted(data[test_ip].keys()) == ['inputs', 'outputs']
    keys = [u'dst_end', u'dst_start', u'links', u'src_end', u'src_start']
    assert sorted(data[test_ip]['inputs'][0].keys()) == keys
    assert sorted(data[test_ip]['outputs'][0].keys()) == keys


def test_simple_request16():
    test_ip = '21.66'
    input_data = {"address": test_ip}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/links?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert data.keys() == [test_ip]
    assert sorted(data[test_ip].keys()) == ['inputs', 'outputs']
    keys = [u'dst_end', u'dst_start', u'links', u'src_end', u'src_start']
    assert sorted(data[test_ip]['inputs'][0].keys()) == keys
    assert sorted(data[test_ip]['outputs'][0].keys()) == keys


def test_simple_request24():
    test_ip = '21.66.10'
    input_data = {"address": test_ip}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/links?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert data.keys() == [test_ip]
    assert sorted(data[test_ip].keys()) == ['inputs', 'outputs']
    keys = [u'dst_end', u'dst_start', u'links', u'src_end', u'src_start']
    assert sorted(data[test_ip]['inputs'][0].keys()) == keys
    assert sorted(data[test_ip]['outputs'][0].keys()) == keys


def test_simple_request32():
    test_ip = '21.66.10.231'
    input_data = {"address": test_ip}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/links?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert data.keys() == [test_ip]
    assert sorted(data[test_ip].keys()) == ['inputs', 'outputs']
    keys = [u'dst_end', u'dst_start', u'links', u'port', u'src_end', u'src_start']
    assert sorted(data[test_ip]['inputs'][0].keys()) == keys
    assert sorted(data[test_ip]['outputs'][0].keys()) == keys


def test_filter():
    test_ip = '21.66.15.183'

    input_data = {"address": test_ip}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/links?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert len(data[test_ip]['inputs']) == 1
    assert len(data[test_ip]['outputs']) == 1

    input_data = {"address": test_ip, 'filter': 443}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/links?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert len(data[test_ip]['inputs']) == 0
    assert len(data[test_ip]['outputs']) == 1

    input_data = {"address": test_ip, 'filter': 8080}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/links?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert len(data[test_ip]['inputs']) == 1
    assert len(data[test_ip]['outputs']) == 0

    input_data = {"address": test_ip, 'filter': 2}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/links?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert len(data[test_ip]['inputs']) == 0
    assert len(data[test_ip]['outputs']) == 0


def make_timestamp(ts):
    d = datetime.strptime(ts, "%Y-%m-%d %H:%M")
    ts = time.mktime(d.timetuple())
    return int(ts)


def test_timerange():
    test_ip = '21.66.15.183'
    time_all = (1, 2 ** 31 - 1)
    time_crop = (make_timestamp('2016-06-21 17:10'), make_timestamp('2016-06-21 18:05'))
    time_tiny = (make_timestamp('2016-06-21 17:50'), make_timestamp('2016-06-21 17:55'))
    time_out = (make_timestamp('2016-06-21 17:00'), make_timestamp('2016-06-21 17:05'))

    input_data = {"address": test_ip, 'tstart': time_all[0], 'tend': time_all[1]}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/links?{0}'.format(GET_data), 'GET')
    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert len(data[test_ip]['inputs']) == 1
    assert len(data[test_ip]['outputs']) == 1

    input_data = {"address": test_ip, 'tstart': time_crop[0], 'tend': time_crop[1]}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/links?{0}'.format(GET_data), 'GET')
    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert len(data[test_ip]['inputs']) == 1
    assert len(data[test_ip]['outputs']) == 1

    input_data = {"address": test_ip, 'tstart': time_tiny[0], 'tend': time_tiny[1]}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/links?{0}'.format(GET_data), 'GET')
    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert len(data[test_ip]['inputs']) == 0
    assert len(data[test_ip]['outputs']) == 1

    input_data = {"address": test_ip, 'tstart': time_out[0], 'tend': time_out[1]}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/links?{0}'.format(GET_data), 'GET')
    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert len(data[test_ip]['inputs']) == 0
    assert len(data[test_ip]['outputs']) == 0

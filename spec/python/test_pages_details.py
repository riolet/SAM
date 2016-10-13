import server
import web
import urllib
import json
from datetime import datetime
import time

app = web.application(server.urls, globals())


def test_simple_request0():
    req = app.request('/details', 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert data.keys() == ['result']
    assert data['result'].startswith("ERROR")


def test_simple_request8():
    test_ip = '21'
    input_data = {"address": test_ip}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/details?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert sorted(data.keys()) == [u'conn_in', u'conn_out', u'ports_in', u'unique_in', u'unique_out', u'unique_ports']
    assert data['unique_in'] == 9311
    assert data['unique_out'] == 468
    assert data['unique_ports'] == 94
    assert len(data['conn_in']) == 32
    assert len(data['conn_out']) == 38
    assert len(data['ports_in']) == 50


def test_simple_request16():
    test_ip = '21.66'
    input_data = {"address": test_ip}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/details?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert sorted(data.keys()) == [u'conn_in', u'conn_out', u'ports_in', u'unique_in', u'unique_out', u'unique_ports']
    assert data['unique_in'] == 9311
    assert data['unique_out'] == 468
    assert data['unique_ports'] == 94
    assert len(data['conn_in']) == 32
    assert len(data['conn_out']) == 38
    assert len(data['ports_in']) == 50


def test_simple_request24():
    test_ip = '21.66.10'
    input_data = {"address": test_ip}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/details?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert sorted(data.keys()) == [u'conn_in', u'conn_out', u'ports_in', u'unique_in', u'unique_out', u'unique_ports']
    assert data['unique_in'] == 2503
    assert data['unique_out'] == 1
    assert data['unique_ports'] == 38
    assert len(data['conn_in']) == 38
    assert len(data['conn_out']) == 1
    assert len(data['ports_in']) == 38


def test_simple_request32():
    test_ip = '21.66.10.70'
    input_data = {"address": test_ip}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/details?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert sorted(data.keys()) == [u'conn_in', u'conn_out', u'ports_in', u'unique_in', u'unique_out', u'unique_ports']
    assert data['unique_in'] == 16
    assert data['unique_out'] == 0
    assert data['unique_ports'] == 13
    assert len(data['conn_in']) == 16
    assert len(data['conn_out']) == 0
    assert len(data['ports_in']) == 13


def test_request_filter():
    test_ip = '21.66.10.70'
    input_data = {"address": test_ip, 'filter': 2}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/details?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert sorted(data.keys()) == [u'conn_in', u'conn_out', u'ports_in', u'unique_in', u'unique_out', u'unique_ports']
    assert data['unique_in'] == 16
    assert data['unique_out'] == 0
    assert data['unique_ports'] == 13
    assert len(data['conn_in']) == 16
    assert len(data['conn_out']) == 0
    assert len(data['ports_in']) == 13


def make_timestamp(ts):
    d = datetime.strptime(ts, "%Y-%m-%d %H:%M")
    ts = time.mktime(d.timetuple())
    return int(ts)


def test_request_timerange():
    time_all = (1, 2**31-1)
    time_crop = (make_timestamp('2016-06-21 17:10'), make_timestamp('2016-06-21 18:05'))
    time_tiny = (make_timestamp('2016-06-21 17:45'), make_timestamp('2016-06-21 17:50'))
    
    test_ip = '21.66.40.231'
    


    input_data = {"address": test_ip, 'tstart': time_all[0], 'tend':time_all[1]}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/details?{0}'.format(GET_data), 'GET')
    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert data['unique_in'] == 7
    assert data['unique_out'] == 4
    assert data['unique_ports'] == 1
    assert len(data['conn_in']) == 7
    assert len(data['conn_out']) == 4
    assert len(data['ports_in']) == 1

    input_data = {"address": test_ip, 'tstart': time_crop[0], 'tend':time_crop[1]}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/details?{0}'.format(GET_data), 'GET')
    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert data['unique_in'] == 7
    assert data['unique_out'] == 4
    assert data['unique_ports'] == 1
    assert len(data['conn_in']) == 7
    assert len(data['conn_out']) == 4
    assert len(data['ports_in']) == 1

    input_data = {"address": test_ip, 'tstart': time_tiny[0], 'tend':time_tiny[1]}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/details?{0}'.format(GET_data), 'GET')
    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert data['unique_in'] == 1
    assert data['unique_out'] == 3
    assert data['unique_ports'] == 1
    assert len(data['conn_in']) == 1
    assert len(data['conn_out']) == 3
    assert len(data['ports_in']) == 1
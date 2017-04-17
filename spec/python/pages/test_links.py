from spec.python import db_connection

import pytest
import web
import sam.pages.links
from sam import constants
from sam import errors
import json
import urllib

db = db_connection.db
sub_id = db_connection.default_sub
ds_full = db_connection.dsid_default

keys = [u'bytes', u'dst_end', u'dst_start', u'links', u'packets', u'protocols', u'src_end', u'src_start']
keys_p = [u'bytes', u'dst_end', u'dst_start', u'links', u'packets',  u'port', u'protocols', u'src_end', u'src_start']


def test_decode_get():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = sam.pages.links.Links()
        good_data = {
            'address': '110,110.20,110.20.30,110.20.30.40',
            'filter': '180',
            'tstart': '1',
            'tend': str(2**31 - 1),
            'protocol': 'ALL',
            'ds': 'ds{}'.format(ds_full),
        }
        actual = p.decode_get_request(good_data)
        expected = {
            'protocol': None,
            'addresses': ['110', '110.20', '110.20.30', '110.20.30.40'],
            'ds': 1,
            'tend': 2147483647,
            'tstart': 1,
            'port': 180,
            'flat': False
        }
        assert actual == expected

        min_data = {
            'address': '50',
            'ds': 'ds{}'.format(ds_full),
        }
        actual = p.decode_get_request(min_data)
        expected = {
            'protocol': None,
            'addresses': ['50'],
            'ds': 1,
            'tstart': 1,
            'tend': 2147483647,
            'port': None,
            'flat': False
        }
        assert actual == expected

        data_no_address = {
            'ds': '{}'.format(ds_full),
        }
        with pytest.raises(errors.MalformedRequest):
            actual = p.decode_get_request(data_no_address)
            assert actual == expected

        data_no_ds = {
            'address': '50',
        }
        with pytest.raises(errors.MalformedRequest):
            actual = p.decode_get_request(data_no_ds)
            assert actual == expected


def test_filter_protocol_blank():
    qstring = '/links?address=10,50,110,150,59&filter=&protocol=&tstart=1521498000&tend=1521498300&ds=ds1'
    with db_connection.env(mock_session=True):
        app = web.application(constants.urls)
        req = app.request(qstring)
        assert req.status == "200 OK"
        data = json.loads(req.data)
        assert set(data.keys()) == {u'150', u'59', u'110', u'10', u'50'}


def test_empty_request():
    with db_connection.env(mock_session=True):
        app = web.application(constants.urls)
        req = app.request('/links', 'GET')

        assert req.status == "200 OK"
        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        assert 'result' in set(data.keys())
        assert data['result'] == 'failure'


def test_simple_request8():
    app = web.application(constants.urls)
    test_ip = '110'

    with db_connection.env(mock_session=True):
        input_data = {'address': test_ip, 'ds': ds_full}
        GET_data = urllib.urlencode(input_data)
        req = app.request('/links?{0}'.format(GET_data), 'GET')

        assert req.status == "200 OK"
        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        assert data.keys() == [test_ip]
        assert sorted(data[test_ip].keys()) == ['inputs', 'outputs']
        assert sorted(data[test_ip]['inputs'][0].keys()) == keys
        assert sorted(data[test_ip]['outputs'][0].keys()) == keys


def test_simple_request16():
    app = web.application(constants.urls)
    test_ip = '110.20'

    with db_connection.env(mock_session=True):
        input_data = {'address': test_ip, 'ds': ds_full}
        GET_data = urllib.urlencode(input_data)
        req = app.request('/links?{0}'.format(GET_data), 'GET')

        assert req.status == "200 OK"
        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        assert data.keys() == [test_ip]
        assert sorted(data[test_ip].keys()) == ['inputs', 'outputs']
        assert sorted(data[test_ip]['inputs'][0].keys()) == keys
        assert sorted(data[test_ip]['outputs'][0].keys()) == keys


def test_simple_request24():
    app = web.application(constants.urls)
    test_ip = '110.20.30'

    with db_connection.env(mock_session=True):
        input_data = {'address': test_ip, 'ds': ds_full}
        GET_data = urllib.urlencode(input_data)
        req = app.request('/links?{0}'.format(GET_data), 'GET')

        assert req.status == "200 OK"
        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        assert data.keys() == [test_ip]
        assert sorted(data[test_ip].keys()) == ['inputs', 'outputs']
        assert sorted(data[test_ip]['inputs'][0].keys()) == keys
        assert sorted(data[test_ip]['outputs'][0].keys()) == keys


def test_simple_request32():
    app = web.application(constants.urls)
    test_ip = '110.20.30.40'

    with db_connection.env(mock_session=True):
        input_data = {'address': test_ip, 'ds': ds_full}
        GET_data = urllib.urlencode(input_data)
        req = app.request('/links?{0}'.format(GET_data), 'GET')

        assert req.status == "200 OK"
        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        assert data.keys() == [test_ip]
        assert sorted(data[test_ip].keys()) == ['inputs', 'outputs']
        assert sorted(data[test_ip]['inputs'][0].keys()) == keys_p
        assert sorted(data[test_ip]['outputs'][0].keys()) == keys_p


def test_ports():
    app = web.application(constants.urls)
    test_ip = '50.60.70.80'

    with db_connection.env(mock_session=True):
        input_data = {'address': test_ip, 'ds': ds_full}
        GET_data = urllib.urlencode(input_data)
        req = app.request('/links?{0}'.format(GET_data), 'GET')

        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        assert len(data[test_ip]['inputs']) == 14
        assert len(data[test_ip]['outputs']) == 15

        input_data = {'address': test_ip, 'ds': ds_full, 'filter': '160'}
        GET_data = urllib.urlencode(input_data)
        req = app.request('/links?{0}'.format(GET_data), 'GET')

        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        assert len(data[test_ip]['inputs']) == 3
        assert len(data[test_ip]['outputs']) == 2

        input_data = {'address': test_ip, 'ds': ds_full, 'filter': '128'}
        GET_data = urllib.urlencode(input_data)
        req = app.request('/links?{0}'.format(GET_data), 'GET')

        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        assert len(data[test_ip]['inputs']) == 0
        assert len(data[test_ip]['outputs']) == 2

        input_data = {'address': test_ip, 'ds': ds_full, 'filter': '360'}
        GET_data = urllib.urlencode(input_data)
        req = app.request('/links?{0}'.format(GET_data), 'GET')

        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        assert len(data[test_ip]['inputs']) == 2
        assert len(data[test_ip]['outputs']) == 0

        input_data = {'address': test_ip, 'ds': ds_full, 'filter': '1040'}
        GET_data = urllib.urlencode(input_data)
        req = app.request('/links?{0}'.format(GET_data), 'GET')

        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        assert len(data[test_ip]['inputs']) == 0
        assert len(data[test_ip]['outputs']) == 0


def test_timerange():
    app = web.application(constants.urls)
    mkt = db_connection.make_timestamp
    time_all = (1, 2 ** 31 - 1)
    time_crop = (mkt('2017-3-21 6:13'), mkt('2017-3-24 13:30'))
    time_tiny = (mkt('2017-3-23 6:13'), mkt('2017-3-23 13:30'))

    test_ip = '50.60.70.80'

    with db_connection.env(mock_session=True):
        input_data = {'address': test_ip, 'ds': ds_full, 'tstart': time_all[0], 'tend': time_all[1]}
        GET_data = urllib.urlencode(input_data)
        req = app.request('/links?{0}'.format(GET_data), 'GET')

        assert req.status == "200 OK"
        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        assert len(data[test_ip]['inputs']) == 14
        assert len(data[test_ip]['outputs']) == 15

        test_ip = '50.60.70.80'
        input_data = {'address': test_ip, 'ds': ds_full, 'tstart': time_crop[0], 'tend': time_crop[1]}
        GET_data = urllib.urlencode(input_data)
        req = app.request('/links?{0}'.format(GET_data), 'GET')

        assert req.status == "200 OK"
        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        assert len(data[test_ip]['inputs']) == 14
        assert len(data[test_ip]['outputs']) == 15

        test_ip = '50.60.70.80'
        input_data = {'address': test_ip, 'ds': ds_full, 'tstart': time_tiny[0], 'tend': time_tiny[1]}
        GET_data = urllib.urlencode(input_data)
        req = app.request('/links?{0}'.format(GET_data), 'GET')

        assert req.status == "200 OK"
        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        assert len(data[test_ip]['inputs']) == 1
        assert len(data[test_ip]['outputs']) == 1

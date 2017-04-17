from spec.python import db_connection

import web
import sam.pages.details
from sam import constants
import json
import urllib

db = db_connection.db
sub_id = db_connection.default_sub
ds_full = db_connection.dsid_default


def test_nice_protocol():
    res = sam.pages.details.nice_protocol(u'tcp', u'udp')
    assert res == u'tcp (in), udp (out)'

    res = sam.pages.details.nice_protocol(u'tcp', u'')
    assert res == u'tcp (in)'
    res = sam.pages.details.nice_protocol(u'tcp', None)
    assert res == u'tcp (in)'

    res = sam.pages.details.nice_protocol(u'', u'udp')
    assert res == u'udp (out)'
    res = sam.pages.details.nice_protocol(None, u'udp')
    assert res == u'udp (out)'

    res = sam.pages.details.nice_protocol(u'abc,def', u'def,ghi,jkl')
    assert res == u'abc (in), def (i/o), jkl (out), ghi (out)'


def test_si_formatting():
    s = sam.pages.details.si_formatting(123)
    assert s == u'123.00'

    s = sam.pages.details.si_formatting(123456)
    assert s == u'123.46K'

    s = sam.pages.details.si_formatting(123456789)
    assert s == u'123.46M'

    s = sam.pages.details.si_formatting(12345678987)
    assert s == u'12.35G'

    s = sam.pages.details.si_formatting(12345678987, places=0)
    assert s == u'12G'

    s = sam.pages.details.si_formatting(12345678987, places=6)
    assert s == u'12.345679G'


def test_decode_get():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        d = sam.pages.details.Details()
        good_data = {
            'ds': 'ds{}'.format(ds_full),
            'tstart': 1000025,
            'tend': 2147000025,
            'address': '110.20',
            'page': '14',
            'page_size': '26',
            'order': '-links',
            'simple': 'false',
            'component': 'quick_info'
        }
        actual = d.decode_get_request(good_data)
        expected = {
            'time_range': (1000025, 2147000025),
            'components': ['quick_info'],
            'address': '110.20',
            'simple': False,
            'order': '-links',
            'ds': 1,
            'page': 14,
            'page_size': 26,
        }
        assert actual == expected

        minimal_data = {
            'ds': 'ds{}'.format(ds_full),
            'address': '110.20',
        }
        actual = d.decode_get_request(minimal_data)
        expected = {'time_range': (1453065600, 1521498300),
                    'components': [],
                    'address': '110.20',
                    'simple': False,
                    'order': None,
                    'ds': 1,
                    'page_size': 50,
                    'page': 1}
        assert actual == expected

        variation_data = {
            'ds': 'ds{}'.format(ds_full),
            'tstart': 1453070000,
            'tend': 1453071234,
            'address': '110.20',
            'page': '1000',
            'page_size': '1000',
            'order': '+port',
            'simple': 'true',
            'component': 'quick_info,inputs,outputs,ports,children,summary,other'
        }
        actual = d.decode_get_request(variation_data)
        expected = {
            'time_range': (1453070000, 1453071234),
            'components': ['quick_info', 'inputs', 'outputs', 'ports', 'children', 'summary', 'other'],
            'address': '110.20',
            'simple': True,
            'order': '+port',
            'ds': 1,
            'page': 1000,
            'page_size': 1000,
        }
        assert actual == expected


def test_nice_ip_address():
    nice = sam.pages.details.Details.nice_ip_address('110.20')
    assert nice == '110.20.0.0/16'
    nice = sam.pages.details.Details.nice_ip_address('110')
    assert nice == '110.0.0.0/8'
    nice = sam.pages.details.Details.nice_ip_address('10.20.30.40')
    assert nice == '10.20.30.40/32'
    nice = sam.pages.details.Details.nice_ip_address('11.22.33.44/0')
    assert nice == '0.0.0.0/0'
    nice = sam.pages.details.Details.nice_ip_address('11.22.33.44/8')
    assert nice == '11.0.0.0/8'
    nice = sam.pages.details.Details.nice_ip_address('11.22.33.44/16')
    assert nice == '11.22.0.0/16'
    nice = sam.pages.details.Details.nice_ip_address('11.22.33.44/24')
    assert nice == '11.22.33.0/24'
    nice = sam.pages.details.Details.nice_ip_address('11.22.33.44/32')
    assert nice == '11.22.33.44/32'

# ---------------------------------------------------------


def simplify(data):
    tup = (
        int(data['unique_in']),
        int(data['unique_out']),
        int(data['unique_ports']),
        len(data['inputs']['rows']),
        len(data['outputs']['rows']),
        len(data['ports']['rows']),
    )
    return tup


def test_simple_request0():
    with db_connection.env(mock_session=True):
        app = web.application(constants.urls)
        req = app.request('/details', 'GET')

        assert req.status == "200 OK"
        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        assert 'result' in set(data.keys())
        assert data['result'] == 'failure'


def test_simple_request8():
    app = web.application(constants.urls)
    test_ip = '10'
    input_data = {'address': test_ip, 'ds': 'ds{}'.format(ds_full)}
    GET_data = urllib.urlencode(input_data)

    with db_connection.env(mock_session=True):
        req = app.request('/details?{0}'.format(GET_data), 'GET')

        assert req.status == "200 OK"
        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        assert sorted(data.keys()) == [u'inputs', u'outputs', u'ports', u'unique_in', u'unique_out', u'unique_ports']
        assert simplify(data) == (17, 17, 40, 50, 50, 40)


def test_simple_request16():
    app = web.application(constants.urls)
    test_ip = '10.20'

    with db_connection.env(mock_session=True):
        input_data = {'address': test_ip, 'ds': ds_full}
        GET_data = urllib.urlencode(input_data)
        req = app.request('/details?{0}'.format(GET_data), 'GET')

        assert req.status == "200 OK"
        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        assert sorted(data.keys()) == [u'inputs', u'outputs', u'ports', u'unique_in', u'unique_out', u'unique_ports']
        assert simplify(data) == (17, 17, 31, 50, 50, 31)


def test_simple_request24():
    app = web.application(constants.urls)
    test_ip = '10.20.30'

    with db_connection.env(mock_session=True):
        input_data = {"address": test_ip, 'ds': ds_full}
        GET_data = urllib.urlencode(input_data)
        req = app.request('/details?{0}'.format(GET_data), 'GET')

        assert req.status == "200 OK"
        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        assert sorted(data.keys()) == [u'inputs', u'outputs', u'ports', u'unique_in', u'unique_out', u'unique_ports']
        assert simplify(data) == (14, 17, 13, 23, 29, 13)


def test_simple_request32():
    app = web.application(constants.urls)
    test_ip = '10.20.30.40'

    with db_connection.env(mock_session=True):
        input_data = {"address": test_ip, 'ds': ds_full}
        GET_data = urllib.urlencode(input_data)
        req = app.request('/details?{0}'.format(GET_data), 'GET')

        assert req.status == "200 OK"
        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        assert sorted(data.keys()) == [u'inputs', u'outputs', u'ports', u'unique_in', u'unique_out', u'unique_ports']
        assert simplify(data) == (8, 14, 2, 9, 17, 2)


def test_request_port():
    app = web.application(constants.urls)
    test_ip = '10.20.30.40'

    with db_connection.env(mock_session=True):
        input_data = {"address": test_ip, 'ds': ds_full, 'port': '136'}
        GET_data = urllib.urlencode(input_data)
        req = app.request('/details?{0}'.format(GET_data), 'GET')

        assert req.status == "200 OK"
        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        assert sorted(data.keys()) == [u'inputs', u'outputs', u'ports', u'unique_in', u'unique_out', u'unique_ports']
        assert simplify(data) == (5, 7, 1, 5, 7, 1)


def test_request_timerange():
    app = web.application(constants.urls)
    mkt = db_connection.make_timestamp
    time_all = (1, 2 ** 31 - 1)
    time_crop = (mkt('2017-3-21 6:13'), mkt('2017-3-24 13:30'))
    time_tiny = (mkt('2017-3-23 6:13'), mkt('2017-3-23 13:30'))

    test_ip = '50.60.70.80'

    with db_connection.env(mock_session=True):
        input_data = {"address": test_ip, 'ds': ds_full, 'tstart': time_all[0], 'tend': time_all[1]}
        GET_data = urllib.urlencode(input_data)
        req = app.request('/details?{0}'.format(GET_data), 'GET')
        assert req.status == "200 OK"
        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        assert simplify(data) == (9, 12, 11, 14, 17, 11)

        input_data = {"address": test_ip, 'ds': ds_full, 'tstart': time_crop[0], 'tend': time_crop[1]}
        GET_data = urllib.urlencode(input_data)
        req = app.request('/details?{0}'.format(GET_data), 'GET')
        assert req.status == "200 OK"
        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        assert simplify(data) == (9, 12, 11, 14, 17, 11)

        input_data = {"address": test_ip, 'ds': ds_full, 'tstart': time_tiny[0], 'tend': time_tiny[1]}
        GET_data = urllib.urlencode(input_data)
        req = app.request('/details?{0}'.format(GET_data), 'GET')
        assert req.status == "200 OK"
        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        assert simplify(data) == (1, 1, 1, 1, 1, 1)


def test_request_component():
    app = web.application(constants.urls)
    test_ip = '50.60.70.80'
    with db_connection.env(mock_session=True):
        for component in ['quick_info', 'inputs', 'outputs', 'ports', 'children', 'summary']:
            input_data = {'address': test_ip, 'ds': ds_full, 'component': component}
            GET_data = urllib.urlencode(input_data)
            req = app.request('/details?{0}'.format(GET_data), 'GET')
            assert req.status == "200 OK"
            assert req.headers['Content-Type'] == "application/json"
            data = json.loads(req.data)
            assert data.keys() == [component]
            assert type(data[component]) == dict


def test_multiple_components():
    app = web.application(constants.urls)
    test_ip = '59.69.79.89'
    input_data = {'address': test_ip, 'ds': ds_full, 'component': 'quick_info,ports,summary'}
    GET_data = urllib.urlencode(input_data)
    with db_connection.env(mock_session=True):
        req = app.request('/details?{0}'.format(GET_data), 'GET')
        assert req.status == "200 OK"
        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        keys = sorted(data.keys())
        assert keys == ['ports', 'quick_info', 'summary']
        for k in keys:
            assert type(data[k]) == dict

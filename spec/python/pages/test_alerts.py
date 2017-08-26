from spec.python import db_connection
import pytest
import cPickle
import datetime
from sam.pages import alerts
from sam.models.security.alerts import Alerts as AlertsModel, AlertFilter
from spec.python.models.security import test_warnings
from sam.models.security import anomaly_plugin as model_ap
from sam import errors

db = db_connection.db
sub_id = db_connection.default_sub
ds_full = db_connection.dsid_default


def reset_mock_alerts():
    table = "s{}_Alerts".format(sub_id)
    db.delete(table, where='1')

    # alert 1 with standard metadata
    details = cPickle.dumps({
        'src': 2292489578L,
        'dst': 3181255194L,
        'port': 389L,
        'protocol': u'UDP',
        'timestamp': datetime.datetime(2016, 6, 21, 18, 0),
        'links': 2L,
        'bytes_sent': 496L,
        'bytes_received': 0L,
        'packets_sent': 4L,
        'packets_received': 0L,
        'duration': 1811L,
    })
    db.insert(table, ipstart=2292489578, ipend=2292489578, log_time=1466532000, report_time=1496886794, severity=6,
              viewed=False, label="LDAP Access", rule_id=4, rule_name="Demo Alert", details=details)

    # alert 2 with details popup
    details = cPickle.dumps({
        'Unusual Inbound Port Access': 'Warning score: 3',
        'activities': [{'chart': {'data1': [0.2, 0.65, 0.15],
                                  'data2': [0.25, 0.75, 0],
                                  'h': 3.5,
                                  'legend': ['Current', 'Usual'],
                                  'sd1': None,
                                  'sd2': [0.1, 0.1, 0.1],
                                  'title': 'Inbound Ports',
                                  'w': 6,
                                  'xlabel': 'Port',
                                  'xticks': ['80', '443', '3306'],
                                  'ylabel': 'Connections Portion'},
                        'description': 'Usually this host receives 100% of connections on ports 80 and 443. '
                                       'Currently it is also receiving connections on port 3306.',
                        'score': 2,
                        'title': 'Unusual Inbound Port Access',
                        'warning_id': 3L}]})
    db.insert(table, ipstart=590000000, ipend=590000000, log_time=1496700000, report_time=1503699051, severity=5,
              viewed=False, label='Unusual inbound traffic', rule_id=None, rule_name='A.D.E.L.E.', details=details)


def test_time_to_seconds():
    assert alerts.time_to_seconds("0") == 0
    assert alerts.time_to_seconds("1 year") == 31556926
    assert alerts.time_to_seconds("3 min, 6 hr, 1 second 1 year 20 weeks") == 43674707
    assert alerts.time_to_seconds("500 trash") == 0


def test_iprange_to_string():
    assert alerts.iprange_to_string(167772160, 184549375) == "10.0.0.0/8"
    assert alerts.iprange_to_string(167772160, 167837695) == "10.0.0.0/16"
    assert alerts.iprange_to_string(167772160, 167772415) == "10.0.0.0/24"
    assert alerts.iprange_to_string(167772160, 167772160) == "10.0.0.0"


def test_fuzzy_time():
    assert alerts.fuzzy_time(0) == '0 seconds'
    assert alerts.fuzzy_time(10) == '10 seconds'
    assert alerts.fuzzy_time(100) == '100 seconds'
    assert alerts.fuzzy_time(1000) == '17 minutes'
    assert alerts.fuzzy_time(10000) == '2.8 hours'
    assert alerts.fuzzy_time(100000) == '28 hours'
    assert alerts.fuzzy_time(1000000) == '12 days'
    assert alerts.fuzzy_time(10000000) == '17 weeks'
    assert alerts.fuzzy_time(100000000) == '3.2 years'
    assert alerts.fuzzy_time(1000000000) == '32 years'
    assert alerts.fuzzy_time(10000000000) == '317 years'


# ---------------  Alerts  ---------------


def test_alerts_get_decode():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        a_page = alerts.Alerts()

        data = {}
        request = a_page.decode_get_request(data)
        expected = {
            'subnet': None,
            'severity': 1,
            'time': 604800,
            'sort': 'id',
            'sort_dir': 'DESC',
            'page_size': 50,
            'page_num': 1,
        }
        assert request == expected

        data = {'subnet': '127.0.0.0/24', 'severity': '6', 'time': '1 day', 'sort': 'severity', 'sort_dir': 'aSC',
                'page_size': '10', 'page_num': '2'}
        request = a_page.decode_get_request(data)
        expected = {
            'subnet': '127.0.0.0/24',
            'severity': 6,
            'time': 86400,
            'sort': 'severity',
            'sort_dir': 'ASC',
            'page_size': 10,
            'page_num': 2,
        }
        assert request == expected


def test_alerts_get_perform():
    reset_mock_alerts()

    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        a_page = alerts.Alerts()

        request = {
            'subnet': '127.0.0.0/24',
            'severity': 6,
            'time': 86400,
            'sort': 'severity',
            'sort_dir': 'ASC',
            'page_size': 10,
            'page_num': 2,
        }
        response = a_page.perform_get_command(request)
        assert set(response.keys()) == {'results', 'page', 'pages', 'alerts'}
        assert response['results'] == 0
        assert response['page'] == 2
        assert response['pages'] == 0
        assert response['alerts'] == []

        request = {
            'subnet': None,
            'severity': 1,
            'time': 10,
            'sort': 'id',
            'sort_dir': 'DESC',
            'page_size': 50,
            'page_num': 1,
        }
        response = a_page.perform_get_command(request)
        assert set(response.keys()) == {'results', 'page', 'pages', 'alerts'}
        assert response['results'] == 0
        assert response['page'] == 1
        assert response['pages'] == 0
        assert response['alerts'] == []

        request = {
            'subnet': None,
            'severity': 1,
            'time': 1000000000,
            'sort': 'id',
            'sort_dir': 'DESC',
            'page_size': 50,
            'page_num': 1,
        }
        response = a_page.perform_get_command(request)
        assert set(response.keys()) == {'results', 'page', 'pages', 'alerts'}
        assert response['results'] == 2
        assert response['page'] == 1
        assert response['pages'] == 1
        assert len(response['alerts']) == 2


def test_alerts_get_encode():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        a_page = alerts.Alerts()

        # empty response:
        response = {
            'alerts': [],
            'results': 0,
            'page': 1,
            'pages': 0,
        }
        encoded = a_page.encode_get_response(response)
        expected = {
            'alerts': [],
            'results': 0,
            'page': 1,
            'pages': 0,
        }
        assert encoded == expected

        # real response
        response = {
            'page': 1,
            'pages': 1,
            'results': 2L,
            'alerts': [
                {'report_time': 1503699051L, 'severity': 5, 'ipstart': 590000000L, 'ipend': 590000000L,
                 'label': u'Unusual inbound traffic', 'rule_name': u'A.D.E.L.E.', 'id': 2L,
                 'log_time': 1496700000L, 'rule_id': None},
                {'report_time': 1496886794L, 'severity': 6, 'ipstart': 2292489578L, 'ipend': 2292489578L,
                 'label': u'LDAP Access', 'rule_name': u'Demo Alert', 'id': 1L,
                 'log_time': 1466532000L, 'rule_id': 4L}],
        }
        encoded = a_page.encode_get_response(response)
        expected = {
            'page': 1,
            'pages': 1,
            'results': 2L,
            'alerts': [
                {
                    'id': '2',
                    'host': '35.42.175.128',
                    'severity': 'sev5',
                    'label': u'Unusual inbound traffic',
                    'rule_name': u'A.D.E.L.E.',
                    'log_time': '2017-06-05 15:00:00',
                    'report_time': '2017-08-25 15:10:51',
                }, {
                    'id': '1',
                    'host': '136.164.157.106',
                    'severity': 'sev6',
                    'label': u'LDAP Access',
                    'rule_name': u'Demo Alert',
                    'log_time': '2016-06-21 11:00:00',
                    'report_time': '2017-06-07 18:53:14',
                }
            ],
        }
        assert encoded == expected


def test_alerts_post_decode():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        a_page = alerts.Alerts()

        data = {}
        with pytest.raises(errors.MalformedRequest):
            a_page.decode_post_request(data)
        data = {'method': 'delete'}
        with pytest.raises(errors.RequiredKey):
            a_page.decode_post_request(data)
        data = {'method': 'delete', 'id': 'NaN'}
        with pytest.raises(errors.RequiredKey):
            a_page.decode_post_request(data)

        data = {'method': 'delete', 'id': 199}
        request = a_page.decode_post_request(data)
        expected = {'method': 'delete', 'id': 199}
        assert request == expected

        data = {'method': 'delete_all'}
        request = a_page.decode_post_request(data)
        expected = {'method': 'delete_all', 'id': None}
        assert request == expected

        data = {'method': 'delete_all', 'id': 201}
        request = a_page.decode_post_request(data)
        expected = {'method': 'delete_all', 'id': None}
        assert request == expected


def test_alerts_post_perform():
    reset_mock_alerts()
    a_model = AlertsModel(db, sub_id)
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        a_page = alerts.Alerts()
        assert a_model.count() == 2

        request = {'method': 'delete_all', 'id': None}
        response = a_page.perform_post_command(request)
        assert response == 'success'
        assert a_model.count() == 0

        reset_mock_alerts()
        assert a_model.count() == 2
        all_alerts = a_model.get(AlertFilter())
        a_id = all_alerts[0]['id']
        request = {'method': 'delete', 'id': a_id}
        a_page.perform_post_command(request)
        assert a_model.count() == 1
        all_alerts = a_model.get(AlertFilter())
        # we deleted the right one.
        assert all_alerts[0]['id'] != a_id


def test_alerts_post_encode():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        a = alerts.Alerts()
        assert a.encode_post_response("success") == {'result': 'success'}
        assert a.encode_post_response("failure") == {'result': 'failure'}


# ---------------  Alert Details  ---------------


def test_alertdetails_get_decode():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        ad_page = alerts.AlertDetails()

        data = {}
        with pytest.raises(errors.RequiredKey):
            ad_page.decode_get_request(data)
        data = {'id': 'not a number'}
        with pytest.raises(errors.RequiredKey):
            ad_page.decode_get_request(data)

        data = {'id': 199}
        request = ad_page.decode_get_request(data)
        expected = {'id': 199}
        assert request == expected


def test_alertdetails_get_perform():
    reset_mock_alerts()
    a_model = AlertsModel(db, sub_id)

    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        ad_page = alerts.AlertDetails()

        # bad id
        request = {'id': -500}
        response = ad_page.perform_get_command(request)
        expected = {
            'for': -500,
            'details': None
        }
        assert response == expected

        all_alerts = a_model.get(AlertFilter())
        a_id1 = [a['id'] for a in all_alerts if a['label'] == 'LDAP Access'][0]
        a_id2 = [a['id'] for a in all_alerts if a['label'] != 'LDAP Access'][0]
        # good ids
        request = {'id': a_id1}
        response = ad_page.perform_get_command(request)
        expected = {
            'details': {'bytes_received': 0L,
                        'bytes_sent': 496L,
                        'dst': 3181255194L,
                        'duration': 1811L,
                        'links': 2L,
                        'packets_received': 0L,
                        'packets_sent': 4L,
                        'port': 389L,
                        'protocol': u'UDP',
                        'src': 2292489578L,
                        'timestamp': datetime.datetime(2016, 6, 21, 18, 0)},
            # 'id': 7L,  # dynamically assigned. may not reliably be 7.
            'ipend': 2292489578L,
            'ipstart': 2292489578L,
            'label': u'LDAP Access',
            'log_time': 1466532000L,
            'report_time': 1496886794L,
            'rule_id': 4L,
            'rule_name': u'Demo Alert',
            'severity': 6,
            'viewed': 0
        }

        assert set(response.keys()) == {'for', 'details'}
        assert response['for'] == a_id1
        response['details'].pop('id')
        assert response['details'] == expected

        request = {'id': a_id2}
        response = ad_page.perform_get_command(request)
        expected = {
            'details': {'Unusual Inbound Port Access': 'Warning score: 3',
                        'activities': [{'chart': {'data1': [0.2, 0.65, 0.15],
                                                  'data2': [0.25, 0.75, 0],
                                                  'h': 3.5,
                                                  'legend': ['Current', 'Usual'],
                                                  'sd1': None,
                                                  'sd2': [0.1, 0.1, 0.1],
                                                  'title': 'Inbound Ports',
                                                  'w': 6,
                                                  'xlabel': 'Port',
                                                  'xticks': ['80', '443', '3306'],
                                                  'ylabel': 'Connections Portion'},
                                        'description': 'Usually this host receives 100% of connections on ports 80 and 443. Currently it is also receiving connections on port 3306.',
                                        'score': 2,
                                        'title': 'Unusual Inbound Port Access',
                                        'warning_id': 3L}]},
            # 'id': 8L,  # dynamically assigned. may not reliably be 8.
            'ipend': 590000000L,
            'ipstart': 590000000L,
            'label': u'Unusual inbound traffic',
            'log_time': 1496700000L,
            'report_time': 1503699051L,
            'rule_id': None,
            'rule_name': u'A.D.E.L.E.',
            'severity': 5,
            'viewed': 0}
        assert set(response.keys()) == {'for', 'details'}
        assert response['for'] == a_id2
        response['details'].pop('id')
        assert response['details'] == expected


def test_alertdetails_get_encode():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        a_page = alerts.AlertDetails()
        response = {'for': -500, 'details': None}
        encoded = a_page.encode_get_response(response)
        expected = {
            'for': -500,
            'time': None,
            'host': None,
            'severity': None,
            'label': None,
            'rule_name': None,
            'details': None,
            'description': None
        }
        assert encoded == expected

        response = {'for': 7, 'details': {
            'details': {'bytes_received': 0L,
                        'bytes_sent': 496L,
                        'dst': 3181255194L,
                        'duration': 1811L,
                        'links': 2L,
                        'packets_received': 0L,
                        'packets_sent': 4L,
                        'port': 389L,
                        'protocol': u'UDP',
                        'src': 2292489578L,
                        'timestamp': datetime.datetime(2016, 6, 21, 18, 0)},
            # 'id': 7L,  # dynamically assigned. may not reliably be 7.
            'ipend': 2292489578L,
            'ipstart': 2292489578L,
            'label': u'LDAP Access',
            'log_time': 1466532000L,
            'report_time': 1496886794L,
            'rule_id': 4L,
            'rule_name': u'Demo Alert',
            'severity': 6,
            'viewed': 0
        }}
        encoded = a_page.encode_get_response(response)
        expected = {
            'for': 7,
            'time': '2017-06-07 18:53:14',
            'host': '136.164.157.106',
            'severity': 6,
            'label': 'LDAP Access',
            'rule_name': 'Demo Alert',
            'description': 'Rule "Demo Alert" triggered on 136.164.157.106',
            'details': {'src': '136.164.157.106',
                        'dst': '189.158.26.26',
                        'port': 389L,
                        'protocol': u'UDP',
                        'links': 2L,
                        'duration': '30 minutes',
                        'bytes_sent': 496L,
                        'bytes_received': 0L,
                        'packets_sent': 4L,
                        'packets_received': 0L,
                        'timestamp': '2016-06-21 18:00:00'},
        }
        assert encoded == expected

        response = {'for': 8, 'details': {
            'details': {'Unusual Inbound Port Access': 'Warning score: 3',
                        'activities': [{'chart': {'data1': [0.2, 0.65, 0.15],
                                                  'data2': [0.25, 0.75, 0],
                                                  'h': 3.5,
                                                  'legend': ['Current', 'Usual'],
                                                  'sd1': None,
                                                  'sd2': [0.1, 0.1, 0.1],
                                                  'title': 'Inbound Ports',
                                                  'w': 6,
                                                  'xlabel': 'Port',
                                                  'xticks': ['80', '443', '3306'],
                                                  'ylabel': 'Connections Portion'},
                                        'description': 'Usually this host receives 100% of connections on ports 80 and 443. Currently it is also receiving connections on port 3306.',
                                        'score': 2,
                                        'title': 'Unusual Inbound Port Access',
                                        'warning_id': 3L}]},
            # 'id': 8L,  # dynamically assigned. may not reliably be 8.
            'ipend': 590000000L,
            'ipstart': 590000000L,
            'label': u'Unusual inbound traffic',
            'log_time': 1496700000L,
            'report_time': 1503699051L,
            'rule_id': None,
            'rule_name': u'A.D.E.L.E.',
            'severity': 5,
            'viewed': 0
        }}
        encoded = a_page.encode_get_response(response)
        expected = {
            'for': 8,
            'time': '2017-08-25 15:10:51',
            'host': '35.42.175.128',
            'severity': 5,
            'label': 'Unusual inbound traffic',
            'rule_name': 'A.D.E.L.E.',
            'description': 'Rule "A.D.E.L.E." triggered on 35.42.175.128',
            'details': {'Unusual Inbound Port Access': 'Warning score: 3',
                        'activities': [{'chart': {'data1': [0.2, 0.65, 0.15],
                                                  'data2': [0.25, 0.75, 0],
                                                  'h': 3.5,
                                                  'legend': ['Current', 'Usual'],
                                                  'sd1': None,
                                                  'sd2': [0.1, 0.1, 0.1],
                                                  'title': 'Inbound Ports',
                                                  'w': 6,
                                                  'xlabel': 'Port',
                                                  'xticks': ['80', '443', '3306'],
                                                  'ylabel': 'Connections Portion'},
                                        'description': 'Usually this host receives 100% of connections on ports 80 and 443. Currently it is also receiving connections on port 3306.',
                                        'score': 2,
                                        'title': 'Unusual Inbound Port Access',
                                        'warning_id': 3L
                                        }]
                        },
        }
        assert encoded == expected


def test_alertdetails_post_decode():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        a_page = alerts.AlertDetails()

        data = {}
        with pytest.raises(errors.RequiredKey):
            a_page.decode_post_request(data)
        data = {'method': 'bananas'}
        with pytest.raises(errors.RequiredKey):
            a_page.decode_post_request(data)
        data = {'method': 'update_label'}
        with pytest.raises(errors.RequiredKey):
            a_page.decode_post_request(data)
        data = {'method': 'update_label', 'id': 'non-number', 'label': 'new label'}
        with pytest.raises(errors.RequiredKey):
            a_page.decode_post_request(data)
        data = {'method': 'update_label', 'id': '55'}
        with pytest.raises(errors.RequiredKey):
            a_page.decode_post_request(data)
        data = {'method': 'update_label', 'id': '55', 'label': 'new label'}
        request = a_page.decode_post_request(data)
        expected = {
            'method': 'update_label',
            'id': 55,
            'label': 'new label'
        }
        assert request == expected


def test_alertdetails_post_perform():
    reset_mock_alerts()
    a_model = AlertsModel(db, sub_id)

    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        a_page = alerts.AlertDetails()

        all_alerts = a_model.get(AlertFilter())
        a_id1 = [a['id'] for a in all_alerts if a['label'] == 'LDAP Access'][0]
        a_id2 = [a['id'] for a in all_alerts if a['label'] != 'LDAP Access'][0]

        request = {
            'method': 'update_label',
            'id': a_id1,
            'label': 'new label'
        }
        a_page.perform_post_command(request)
        request = {
            'method': 'update_label',
            'id': a_id2,
            'label': 'meh label'
        }
        a_page.perform_post_command(request)

        labels = {row['label'] for row in db.select("s{}_Alerts".format(sub_id), what='label')}
        assert labels == {'new label', 'meh label'}


def test_alertdetails_post_encode():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        a = alerts.AlertDetails()
        assert a.encode_post_response("success") == {'result': 'success'}
        assert a.encode_post_response("failure") == {'result': 'failure'}
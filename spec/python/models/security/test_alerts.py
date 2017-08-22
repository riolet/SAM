from datetime import datetime
from spec.python import db_connection
from sam import common
from sam.models.security.alerts import Alerts, AlertFilter

session = {}
db = db_connection.db
sub_id = db_connection.default_sub

"""
# some of the preexisting ips in the test database
ips = [
'110.20.30.40',
'110.20.30.41',
'110.20.32.42',
'110.20.32.43',
'110.24.34.44',
'110.24.34.45',
'110.24.36.46',
'110.24.36.47',
'150.60.70.80',
'150.60.70.81',
'150.60.72.82',
'150.60.72.83',
'150.64.74.84',
'150.64.74.85',
'150.64.76.86',
'150.64.76.87']
"""


def add_test_data(model):
    """
    :type model: Alerts 
    """
    d1 = datetime(2017,6,5,4,3,2)
    low, high = common.determine_range_string("110.24.36.47")
    model.add_alert(low, high, 1, None, "Network Scanning", 'scanning', "details", d1)

    low, high = common.determine_range_string("110.24.36.46")
    model.add_alert(low, high, 2, None, "Smurf Amplifier DoS", 'sdos', [b'list', u'details'], d1)

    low, high = common.determine_range_string("110.24.34.45")
    model.add_alert(low, high, 3, None, "P2P Sharing / UDP Port Scanning", 'udp scan', {'count': 99321, 'oh': [1, 2, 3]}, d1)

    low, high = common.determine_range_string("110.24.34.44")
    model.add_alert(low, high, 4, 4, "DoS", 'dos', ['packet rate 1,000,000', 42], d1)

    low, high = common.determine_range_string("110.20.32.43")
    model.add_alert(low, high, 5, None, "Unexpected Traffic", 'unexpected', None, d1)

    low, high = common.determine_range_string("110.20.32.42")
    model.add_alert(low, high, 6, None, "Compromised Traffic", 'compromised', {114, 23}, d1)

    low, high = common.determine_range_string("110.20.30.41")
    model.add_alert(low, high, 7, None, "Suspicious Traffic", 'suspicious', False, d1)

    low, high = common.determine_range_string("110.20.30.40")
    model.add_alert(low, high, 8, None, "Custom Rule", 'custom', 5j + 2l, d1)


def test_add_clear_alert():
    a_model = Alerts(db, sub_id)

    try:
        add_test_data(a_model)

        # Did it work?
        filters = AlertFilter(sort='severity')
        stored = a_model.get(filters)

        assert a_model.count() == 8
        groups = [(row['ipstart'], row['rule_name']) for row in stored]
        t = common.IPStringtoInt
        assert groups[0] == (t('110.20.30.40'), 'Custom Rule')
        assert groups[1] == (t('110.20.30.41'), 'Suspicious Traffic')
        assert groups[2] == (t('110.20.32.42'), 'Compromised Traffic')
        assert groups[3] == (t('110.20.32.43'), 'Unexpected Traffic')
        assert groups[4] == (t('110.24.34.44'), 'DoS')
        assert groups[5] == (t('110.24.34.45'), 'P2P Sharing / UDP Port Scanning')
        assert groups[6] == (t('110.24.36.46'), 'Smurf Amplifier DoS')
        assert groups[7] == (t('110.24.36.47'), 'Network Scanning')

        # put it back the way we found it...
    finally:
        a_model.clear()
    assert a_model.count() == 0


def test_alert_already_exists():
    a = Alerts(db, sub_id)
    ipstart, ipend = common.determine_range_string("110.24.34.44")
    rule_id = 4
    timestamp = datetime(2017, 6, 5, 4, 3, 2)
    timestamp2 = datetime(2017, 6, 5, 4, 3, 1)
    ipstart2, ipend2 = common.determine_range_string("110.20.32.43")
    rule_id2 = None
    try:
        add_test_data(a)
        #finds exact matches
        assert a.alert_already_exists(ipstart, ipend, rule_id, timestamp)
        assert a.alert_already_exists(ipstart2, ipend2, rule_id2, timestamp)
        # doesn't find near matches
        assert a.alert_already_exists(ipstart+1, ipend, rule_id, timestamp) is None
        assert a.alert_already_exists(ipstart, ipend+1, rule_id, timestamp) is None
        assert a.alert_already_exists(ipstart, ipend, rule_id+1, timestamp) is None
        assert a.alert_already_exists(ipstart, ipend, rule_id, timestamp2) is None
    finally:
        a.clear()


def test_filters():
    a = AlertFilter(min_severity=12, limit=99, age_limit=8160, sort="severity", order="ASC")
    assert a.limit == 99
    # testing the timing may fail because get_where calls time.time()
    assert a.get_where()[:33] == "severity >= 12 AND report_time > "
    assert a.get_orderby() == "severity ASC"

    b = AlertFilter(min_severity=12, limit=99, sort="severity", order="DESC")
    assert b.get_where() == "severity >= 12"
    assert b.get_orderby() == "severity DESC"

    c = AlertFilter(sort="report_time", order="blah")
    assert c.get_orderby() == "report_time DESC"


def test_get_by_host():
    t = common.IPStringtoInt
    a = Alerts(db, sub_id)
    try:
        add_test_data(a)

        filters = AlertFilter(sort='severity')
        low, high = common.determine_range_string("110.20.32.43")
        stored = a.get_by_host(filters, low, high)
        groups = [(row['ipstart'], row['rule_name']) for row in stored]
        assert groups == [(t('110.20.32.43'), 'Unexpected Traffic')]

        low, high = common.determine_range_string("110.20.32")
        stored = a.get_by_host(filters, low, high)
        groups = [(row['ipstart'], row['rule_name']) for row in stored]
        assert groups == [
            (t('110.20.32.42'), 'Compromised Traffic'),
            (t('110.20.32.43'), 'Unexpected Traffic')
        ]

        low, high = common.determine_range_string("110.20")
        stored = a.get_by_host(filters, low, high)
        groups = [(row['ipstart'], row['rule_name']) for row in stored]
        assert groups == [
            (t('110.20.30.40'), 'Custom Rule'),
            (t('110.20.30.41'), 'Suspicious Traffic'),
            (t('110.20.32.42'), 'Compromised Traffic'),
            (t('110.20.32.43'), 'Unexpected Traffic'),
        ]
    finally:
        a.clear()


def test_get_details():
    t = common.IPStringtoInt
    a = Alerts(db, sub_id)
    low, high = common.determine_range_string("110.24.36.47")
    details = {'a': 1, True: 5j + 2l, (1, 2): [3, 4], None: u'unicode'}
    try:
        e_id = a.add_alert(low, high, 1, None, "Network Scanning", 'scan', details, datetime(2017,6,5,4,3,2))

        row = a.get_details(e_id)
        assert row['ipstart'] == t('110.24.36.47')
        assert row['rule_name'] == 'Network Scanning'
        assert row['details'] == details
    finally:
        a.clear()


def test_set_label():
    a = Alerts(db, sub_id)

    low, high = common.determine_range_string("110.24.36.47")
    try:
        e_id = a.add_alert(low, high, 1, None, "Network Scanning", 'scan', "details", datetime(2017,6,5,4,3,2))

        groups = a.get(AlertFilter())
        assert groups[0]['label'] == 'scan'

        a.set_label(e_id, 'alternative')
        groups = a.get(AlertFilter())
        assert groups[0]['label'] == 'alternative'

        a.set_label(e_id, None)
        groups = a.get(AlertFilter())
        assert groups[0]['label'] == 'alternative'
    finally:
        a.clear()

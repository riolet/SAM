# to run these tests (and have python find the sam package), go to your sam_cloud/sam and run:
#   python -m pytest ../plugins/security/spec

from spec.python import db_connection
from sam import common
from sam.models.alerts import Alerts, AlertFilter
from datetime import datetime
import time


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
    low, high = common.determine_range_string("110.24.36.47")
    model.add_alert(low, high, 1, "Network Scanning", "details")

    low, high = common.determine_range_string("110.24.36.46")
    model.add_alert(low, high, 2, "Smurf Amplifier DoS", [b'list', u'details'])

    low, high = common.determine_range_string("110.24.34.45")
    model.add_alert(low, high, 3, "P2P Sharing / UDP Port Scanning", {'count': 99321, 'oh': [1, 2, 3]})

    low, high = common.determine_range_string("110.24.34.44")
    model.add_alert(low, high, 4, "DoS", ['packet rate 1,000,000', 42])

    low, high = common.determine_range_string("110.20.32.43")
    model.add_alert(low, high, 5, "Unexpected Traffic", None)

    low, high = common.determine_range_string("110.20.32.42")
    model.add_alert(low, high, 6, "Compromised Traffic", {114, 23})

    low, high = common.determine_range_string("110.20.30.41")
    model.add_alert(low, high, 7, "Suspicious Traffic", False)

    low, high = common.determine_range_string("110.20.30.40")
    model.add_alert(low, high, 8, "Custom Rule", 5j + 2l)


def test_add():
    a_model = Alerts(db, sub_id)
    add_test_data(a_model)

    # Did it work?
    filters = AlertFilter(sort='severity')
    stored = a_model.get_recent(filters)

    assert len(stored) == 8
    groups = [(row['event_type'], row['details']) for row in stored]
    assert groups[0] == ('Custom Rule', 5j+2)
    assert groups[1] == ('Suspicious Traffic', False)
    assert groups[2] == ('Compromised Traffic', {114, 23})
    assert groups[3] == ('Unexpected Traffic', None)
    assert groups[4] == ('DoS', ['packet rate 1,000,000', 42])
    assert groups[5] == ('P2P Sharing / UDP Port Scanning', {'count': 99321, 'oh': [1,2,3]})
    assert groups[6] == ('Smurf Amplifier DoS', [b'list', u'details'])
    assert groups[7] == ('Network Scanning', 'details')

    # put it back the way we found it...
    a_model.clear()
    stored = a_model.get_recent(filters)
    assert len(stored) == 0


def test_filters():
    a = AlertFilter(min_severity=12, limit=99, age_limit=8160, sort="severity", order="ASC")
    assert a.limit == 99
    # testing the timing may fail because get_where calls time.time()
    assert a.get_where()[:31] == "severity >= 12 AND timestamp > "
    assert a.get_orderby() == "severity ASC"

    b = AlertFilter(min_severity=12, limit=99, sort="severity", order="DESC")
    assert b.get_where() == "severity >= 12"
    assert b.get_orderby() == "severity DESC"

    c = AlertFilter(sort="timestamp", order="blah")
    assert c.get_orderby() == "timestamp DESC"


def test_get_by_host():
    a = Alerts(db, sub_id)
    add_test_data(a)

    filters = AlertFilter(sort='severity')
    low, high = common.determine_range_string("110.20.32.43")
    stored = a.get_by_host(filters, low, high)
    groups = [(row['event_type'], row['details']) for row in stored]
    assert groups == [('Unexpected Traffic', None)]

    low, high = common.determine_range_string("110.20.32")
    stored = a.get_by_host(filters, low, high)
    groups = [(row['event_type'], row['details']) for row in stored]
    assert groups == [("Compromised Traffic", {114, 23}), ('Unexpected Traffic', None)]

    low, high = common.determine_range_string("110.20")
    stored = a.get_by_host(filters, low, high)
    groups = [(row['event_type'], row['details']) for row in stored]
    assert groups == [
        ("Custom Rule", 5j + 2l),
        ("Suspicious Traffic", False),
        ("Compromised Traffic", {114, 23}),
        ('Unexpected Traffic', None),
    ]

    a.clear()


def test_set_status():
    a = Alerts(db, sub_id)

    low, high = common.determine_range_string("110.24.36.47")
    e_id = a.add_alert(low, high, 1, "Network Scanning", "details")

    groups = a.get_recent(AlertFilter())
    assert groups[0]['status'] == Alerts.DEFAULT_STATUS

    a.set_status(e_id, "viewed")
    groups = a.get_recent(AlertFilter())
    assert groups[0]['status'] == "viewed"

    a.set_status(e_id, None)
    groups = a.get_recent(AlertFilter())
    assert groups[0]['status'] == "viewed"

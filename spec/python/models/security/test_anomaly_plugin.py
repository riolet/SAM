import pytest
from datetime import datetime
from spec.python import db_connection
from spec.python.models.security import test_warnings
from sam import common, errors
from sam.models.security import anomaly_plugin, alerts

"""
Note: all tests in this file assume the anomaly detection plugin is not installed.
"""

session = {}
db = db_connection.db
sub_id = db_connection.default_sub


def test_init():
    ap = anomaly_plugin.ADPlugin(db, sub_id)
    assert anomaly_plugin.PLUGIN_INSTALLED is False
    assert ap.status == 'unavailable'
    assert ap.adele == None


def test_get_set_active():
    ap = anomaly_plugin.ADPlugin(db, sub_id)
    initial = ap.get_active()
    ap.enable()
    assert ap.get_active() == True
    ap.disable()
    assert ap.get_active() == False

    # restore original state
    if initial:
        ap.enable()


def test__retrieve_warnings():
    ap = anomaly_plugin.ADPlugin(db, sub_id)
    assert ap._retrieve_warnings(None) is None


def test_get_warnings():
    test_warnings.populate_db_warnings()
    ap = anomaly_plugin.ADPlugin(db, sub_id)
    ws = ap.get_warnings()
    ws = {w['warning_id'] for w in ws}
    assert ws == {1,5,8,10,14}

    ws = ap.get_warnings(show_all=False)
    ws = {w['warning_id'] for w in ws}
    assert ws == {1,5,8,10,14}

    ws = ap.get_warnings(show_all=True)
    ws = {w['warning_id'] for w in ws}
    assert ws == set(range(1, 15))


def test_get_warning():
    test_warnings.populate_db_warnings()
    ap = anomaly_plugin.ADPlugin(db, sub_id)
    ws = ap.get_warnings(show_all=True)
    i = ws[7]['id']
    w = ap.get_warning(i)
    assert w['id'] == i
    assert w['warning_id'] == 7
    w = ap.get_warning(-200)
    assert w is None


def test_get_stats():
    ap = anomaly_plugin.ADPlugin(db, sub_id)
    assert ap.get_stats() == None


def test_accept_warning():
    test_warnings.populate_db_warnings()
    ap = anomaly_plugin.ADPlugin(db, sub_id)
    a_model = alerts.Alerts(db, sub_id)
    old_a = a_model.count()
    sample_warning = ap.get_warnings(show_all=False)[0]

    # bad warning id does nothing
    with pytest.raises(errors.MalformedRequest):
        ap.accept_warning(500000)

    # accept a warning
    a_id = ap.accept_warning(sample_warning['id'])
    w = ap.get_warning(sample_warning['id'])
    assert w['status'] == 'accepted'

    num_a1 = a_model.count()
    assert num_a1 == old_a + 1
    alert1 = a_model.get_details(a_id)
    assert alert1 is not None

    # reject and reaccept it
    ap.ignore_warning(sample_warning['id'])
    a_id = ap.accept_warning(sample_warning['id'])

    num_a2 = a_model.count()
    # no
    assert num_a2 == old_a + 1
    alert2 = a_model.get_details(a_id)
    assert alert2 is not None
    assert alert2 == alert1


def test_reject_warning():
    test_warnings.populate_db_warnings()
    ap = anomaly_plugin.ADPlugin(db, sub_id)
    sample_warning = ap.get_warnings(show_all=False)[1]

    # bad warning id does nothing
    with pytest.raises(errors.MalformedRequest):
        ap.reject_warning(500000)

    ap.reject_warning(sample_warning['id'])

    w = ap.get_warning(sample_warning['id'])
    assert w['status'] == 'rejected'


def test_ignore_warning():
    test_warnings.populate_db_warnings()
    ap = anomaly_plugin.ADPlugin(db, sub_id)
    sample_warning = ap.get_warnings(show_all=False)[1]

    # bad warning id does nothing
    with pytest.raises(errors.MalformedRequest):
        ap.ignore_warning(500000)

    ap.ignore_warning(sample_warning['id'])

    w = ap.get_warning(sample_warning['id'])
    assert w['status'] == 'ignored'

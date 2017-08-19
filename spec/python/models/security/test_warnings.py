import pytest
import cPickle
from spec.python import db_connection
from sam import common
from sam.models.security import warnings

session = {}
db = db_connection.db
sub_id = db_connection.default_sub


# CREATE TABLE IF NOT EXISTS s{acct}_ADWarnings
# (id                INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY
# ,warning_id        INT UNSIGNED NOT NULL UNIQUE
# ,host              INT UNSIGNED NOT NULL
# ,log_time          INT UNSIGNED NOT NULL
# ,reason            TEXT NOT NULL
# ,status            VARCHAR(32) NOT NULL  # should be one of "accepted", "rejected", "ignored", "uncategorized"
# ,details           TEXT
# );

details1 = {'activities': [
                {'title': 'title1', 'score': 3, 'description': 'desc1', 'warning_id': 2L, 'id': 1L},
                {'title': 'title2', 'score': 4, 'description': 'desc2', 'warning_id': 2L, 'id': 2L}],
            'key2': 'val2',
            'title1': 'Warning score: 3',
            'title2': 'Warning score: 4'}
details2 = {'activities': [
                {'title': 'title3', 'score': 5, 'description': 'desc3', 'warning_id': 3L, 'id': 3L}],
            'key3': 'val3',
            'title3': 'Warning score: 5'}
host1 = common.IPStringtoInt("100.101.102.103")
host2 = common.IPStringtoInt("100.101.102.104")
host3 = common.IPStringtoInt("100.101.103.105")
host4 = common.IPStringtoInt("100.102.103.106")
host5 = common.IPStringtoInt("101.102.103.108")
now = 1503089118
time1 = now
time2 = now - 60*5  # 5 minutes ago
time3 = now - 60*61  # 61 minutes ago
time4 = now - 60*60*24 # 24 hours ago
time5 = now - 60*60*24*7 # 1 week ago
time6 = now - 60*60*24*28 # 4 weeks ago
time7 = now - 31556926 # last year
statA = "uncategorized"
statB = "accepted"
statC = "rejected"
statD = "ignored"

def populate_db_warnings():
    entries = [
        {"warning_id":  1, "host": host1, "log_time": time1, 'reason': "test1", 'status': statA, "details": cPickle.dumps(details1)},
        {"warning_id":  2, "host": host2, "log_time": time1, 'reason': "test1", 'status': statB, "details": cPickle.dumps(details2)},
        {"warning_id":  3, "host": host2, "log_time": time2, 'reason': "test1", 'status': statC, "details": cPickle.dumps(details1)},
        {"warning_id":  4, "host": host3, "log_time": time2, 'reason': "test1", 'status': statD, "details": cPickle.dumps(details1)},
        {"warning_id":  5, "host": host3, "log_time": time3, 'reason': "test1", 'status': statA, "details": cPickle.dumps(details2)},
        {"warning_id":  6, "host": host4, "log_time": time3, 'reason': "test1", 'status': statB, "details": cPickle.dumps(details2)},
        {"warning_id":  7, "host": host4, "log_time": time4, 'reason': "test1", 'status': statC, "details": cPickle.dumps(details1)},
        {"warning_id":  8, "host": host5, "log_time": time4, 'reason': "test1", 'status': statA, "details": cPickle.dumps(details1)},
        {"warning_id":  9, "host": host5, "log_time": time5, 'reason': "test1", 'status': statB, "details": cPickle.dumps(details1)},
        {"warning_id": 10, "host": host4, "log_time": time5, 'reason': "test1", 'status': statA, "details": cPickle.dumps(details2)},
        {"warning_id": 11, "host": host4, "log_time": time6, 'reason': "test1", 'status': statD, "details": cPickle.dumps(details2)},
        {"warning_id": 12, "host": host3, "log_time": time6, 'reason': "test1", 'status': statC, "details": cPickle.dumps(details2)},
        {"warning_id": 13, "host": host2, "log_time": time7, 'reason': "test1", 'status': statB, "details": cPickle.dumps(details1)},
        {"warning_id": 14, "host": host1, "log_time": time7, 'reason': "test1", 'status': statA, "details": cPickle.dumps(details2)},
    ]
    table = warnings.Warnings.TABLE_FORMAT.format(acct=sub_id)
    db.delete(table, where="1")
    db.multiple_insert(table, entries)

populate_db_warnings()


def test_get_latest_warning_id():
    w_model = warnings.Warnings(db, sub_id)
    assert w_model.get_latest_warning_id() == 14


def test_get_warnings():
    w_model = warnings.Warnings(db, sub_id)
    ws = w_model.get_warnings()
    ws = {w['warning_id'] for w in ws}
    assert ws == {1,5,8,10,14}

    ws = w_model.get_warnings(show_all=False)
    ws = {w['warning_id'] for w in ws}
    assert ws == {1,5,8,10,14}

    ws = w_model.get_warnings(show_all=True)
    ws = {w['warning_id'] for w in ws}
    assert ws == set(range(1, 15))


def test_get_warning():
    w_model = warnings.Warnings(db, sub_id)
    ws = w_model.get_warnings(show_all=True)
    i = ws[7]['id']
    w = w_model.get_warning(i)
    assert w['id'] == i
    assert w['warning_id'] == 7
    assert w['details'] == details1
    assert w['host'] == host4
    assert w['log_time'] == time4

    w = w_model.get_warning(200)
    assert w is None


def test__warning_status():
    w_model = warnings.Warnings(db, sub_id)
    assert w_model._warning_status('rejected') == 'rejected'
    assert w_model._warning_status('accepted') == 'accepted'
    assert w_model._warning_status('ignored') == 'ignored'
    assert w_model._warning_status('unknown') == 'uncategorized'
    assert w_model._warning_status('uncategorized') == 'uncategorized'
    assert w_model._warning_status('') == 'uncategorized'


def test_insert_warnings():
    wlist = [
        {'id': 15, 'host': host1, 'log_time': time1, 'reason': 'tiw1', 'details': details2},
        {'id': 16, 'host': host2, 'log_time': time2, 'reason': 'tiw2', 'details': details2, 'status': statA},
        {'id': 19, 'host': host3, 'log_time': time3, 'reason': 'tiw1', 'details': details1, 'status': statB},
        {'id': 18, 'host': host4, 'log_time': time4, 'reason': 'tiw2', 'details': details2, 'status': statC},
        {'id': 17, 'host': host4, 'log_time': time4, 'reason': 'tiw2', 'details': details2, 'status': statD},
    ]
    w_model = warnings.Warnings(db, sub_id)

    ws = w_model.get_warnings(show_all=True)
    assert len(ws) == 14
    w_model.insert_warnings([])
    ws = w_model.get_warnings(show_all=True)
    assert len(ws) == 14
    w_model.insert_warnings(wlist)
    ws = w_model.get_warnings(show_all=True)
    assert len(ws) == 19

    third_from_last = ws[-3]['id']
    w = w_model.get_warning(third_from_last)
    assert w['details'] == details1

    # replace db content with original test content
    populate_db_warnings()


def test_update_status():
    w_model = warnings.Warnings(db, sub_id)

    # invalid warning_id
    with pytest.raises(ValueError):
        w_model.update_status(200, 'accepted')

    # find an ID to use
    ws = w_model.get_warnings(show_all=True)
    i = ws[5]['id']

    # valid warning_id, invalid status
    with pytest.raises(ValueError):
        w_model.update_status(i, 'garbage')

    # valid everything
    assert w_model.update_status(i, statA)
    assert w_model.update_status(i, statB)
    # worked?
    w = w_model.get_warning(i)
    assert w['status'] == statB
    assert w_model.update_status(i, statC)
    assert w_model.update_status(i, statD)
    # worked?
    w = w_model.get_warning(i)
    assert w['status'] == statD
    # reset to statA
    assert w_model.update_status(i, statA)

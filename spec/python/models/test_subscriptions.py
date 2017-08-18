import pytest
import numbers
import sys
from sam import constants
from spec.python import db_connection
from sam.models.subscriptions import Subscriptions

db = db_connection.db
sub_id = db_connection.default_sub


def test_get_all():
    s = Subscriptions(db)
    subs = s.get_all()
    assert type(subs) is list
    assert isinstance(subs[0], dict)


def test_get_id_list():
    s = Subscriptions(db)
    ids = s.get_id_list()
    assert type(ids) is list
    assert isinstance(ids[0], numbers.Integral)


def test_get_by_email():
    s = Subscriptions(db)
    sub = s.get_by_email(constants.subscription['default_email'])
    assert bool(sub)
    assert sub.plan == 'admin'


def test_get():
    s = Subscriptions(db)
    ids = s.get_id_list()
    for id in ids:
        sub = s.get(id)
        assert sub is not None


def xtest_create_subscription_tables():
    pass


def xtest_create_default_subscription():
    pass


def test_decode_sub():
    s = Subscriptions(db)

    #add an extra subscription entry
    test_id = 25
    test_email = "test@testing.co"
    query = """INSERT INTO Subscriptions VALUES ({}, "{}", "Test", "nimda", "r w a", 1, NULL);""".format(test_id, test_email)
    db.query(query)
    try:
        constants.access_control['active'] = True
        assert s.decode_sub(sub_id) == sub_id
        assert s.decode_sub(constants.subscription['default_email']) == sub_id
        assert s.decode_sub(25) == test_id
        assert s.decode_sub(24) == None
        assert s.decode_sub(32000) == None
        assert s.decode_sub(test_email) == test_id
        assert s.decode_sub("bad@email.com") == None

        constants.access_control['active'] = False
        assert s.decode_sub(sub_id) == sub_id
        assert s.decode_sub(constants.subscription['default_email']) == sub_id
        assert s.decode_sub(25) == test_id
        assert s.decode_sub(24) == sub_id
        assert s.decode_sub(32000) == sub_id
        assert s.decode_sub(test_email) == test_id
        assert s.decode_sub("bad@email.com") == sub_id
    finally:
        query = "DELETE FROM Subscriptions WHERE subscription={};".format(test_id)
        db.query(query)


def test_get_set_plugin_data():
    name1 = "p1"
    name2 = "p2"
    sub1 = sub_id
    sub2 = 25
    s = Subscriptions(db)
    data1 = {'a': 1, 'b': [2, 3], 'c': {4, 5}, 'd': 6l, 'e': True, 'f': 7+2j, 'g': 3.141}
    data2 = "This is a test"
    data3 = {'msg': "Nothing to see here", 'id': 41}
    data4 = ["one", "two", "three"]



    #add an extra subscription entry
    test_email = "test@testing.co"
    query = """INSERT INTO Subscriptions VALUES ({}, "{}", "Test", "nimda", "r w a", 1, NULL);""".format(sub2, test_email)
    db.query(query)
    try:
        s.set_plugin_data(sub1, name1, data1)
        s.set_plugin_data(sub1, name2, data2)
        s.set_plugin_data(sub2, name1, data3)
        s.set_plugin_data(sub2, name2, data4)

        with pytest.raises(ValueError):
            s.set_plugin_data(1000, name1, data1)
        with pytest.raises(TypeError):
            s.set_plugin_data(sub1, name1, sys.stderr)

        assert s.get_plugin_data(sub1, name1) == data1
        assert s.get_plugin_data(sub1, name2) == data2
        assert s.get_plugin_data(sub2, name1) == data3
        assert s.get_plugin_data(sub2, name2) == data4
        assert s.get_plugin_data(sub2, "noname") == {}

        with pytest.raises(ValueError):
            s.get_plugin_data(1000, name1)

        query = """UPDATE Subscriptions SET plugins="garbage" WHERE subscription={};""".format(sub1)
        db.query(query)
        assert s.get_plugin_data(sub1, name1) == {}
        assert s.get_plugin_data(sub2, name1) == data3
        assert s.get_plugin_data(sub2, name2) == data4
    finally:
        query = "DELETE FROM Subscriptions WHERE subscription={};".format(sub2)
        db.query(query)

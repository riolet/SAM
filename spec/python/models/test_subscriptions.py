import numbers
import constants
from spec.python import db_connection
import models.subscriptions
import models.user

db = db_connection.db


def test_get_all():
    s = models.subscriptions.Subscriptions(db)
    subs = s.get_all()
    assert type(subs) is list
    assert isinstance(subs[0], dict)


def test_get_id_list():
    s = models.subscriptions.Subscriptions(db)
    ids = s.get_id_list()
    assert type(ids) is list
    assert isinstance(ids[0], numbers.Integral)


def test_get_by_email():
    s = models.subscriptions.Subscriptions(db)
    sub = s.get_by_email(constants.demo['email'])
    assert bool(sub)
    assert sub.plan == 'admin'


def test_get():
    s = models.subscriptions.Subscriptions(db)
    ids = s.get_id_list()
    for id in ids:
        sub = s.get(id)
        assert sub is not None

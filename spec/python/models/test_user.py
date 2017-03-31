# importing db_connection has the side effect of setting the test database.
from spec.python import db_connection
from models.user import User

sub_id = db_connection.default_sub
session = {}


def logout():
    session.clear()


def login():
    user = User(session)
    user.logged_in = True
    user.name = 'Test User'
    user.email = 'test@email.com'
    user.subscription = 1
    user.plan = 'plan100'
    user.plan_active = True
    user.viewing = user.subscription


def test_empty_user():
    with db_connection.env(login_active=False):
        u = User(session)
        logout()

        assert u.email is 'SAM'
        assert u.name is 'SAM'
        assert u.logged_in is True
        assert u.plan_active is True
        assert u.plan is 'admin'
        assert u.subscription is sub_id
        assert u.viewing is sub_id
        assert u.groups.issuperset({'login', 'subscribed'})
        assert 'logout' not in u.groups
        assert 'unsubscribed' not in u.groups
        assert 'debug' not in u.groups

    with db_connection.env(login_active=True):
        u = User(session)
        logout()

        assert u.email is None
        assert u.name is None
        assert u.logged_in is False
        assert u.plan_active is False
        assert u.plan is None
        assert u.subscription is None
        assert u.viewing is sub_id
        assert u.groups.issuperset({'logout', 'unsubscribed'})
        assert 'login' not in u.groups
        assert 'subscribed' not in u.groups
        assert 'debug' not in u.groups


def test_logged_in_user():
    with db_connection.env(login_active=True):
        login()
        u = User(session)

        assert u.email == 'test@email.com'
        assert u.name == 'Test User'
        assert u.logged_in == True
        assert u.plan_active == True
        assert u.plan == 'plan100'
        assert u.subscription == 1
        assert u.viewing == 1
        assert u.groups.issuperset({'login', 'subscribed'})
        assert 'logout' not in u.groups
        assert 'unsubscribed' not in u.groups
        assert 'debug' not in u.groups


def test_may_post():
    login()
    u = User(session)

    assert u.may_post() is True
    u.viewing = 12345
    assert u.may_post() is False
    u.viewing = u.subscription
    assert u.may_post() is True
    u.plan = None
    assert u.may_post() is False
    u.plan = ""
    assert u.may_post() is False
    u.plan = "none"
    assert u.may_post() is False
    u.plan = "p"
    assert u.may_post() is True
    u.plan_active = False
    assert u.may_post() is False
    u.plan_active = True
    assert u.may_post() is True


def test_any_all_groups():
    login()
    u = User(session)
    assert u.any_group(['login', 'logout', 'subscribed', 'unsubscribed']) is True
    assert u.all_groups(['login', 'logout', 'subscribed', 'unsubscribed']) is False
    assert u.all_groups(['login', 'subscribed']) is True

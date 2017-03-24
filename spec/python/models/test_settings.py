# importing db_connection has the side effect of setting the test database.
import db_connection
from models.settings import Settings

sub_id = db_connection.default_sub
session = {}


def test_update_clear_cache():
    s_model = Settings(session, sub_id)
    s_model.update_cache()
    settings = s_model.storage[Settings.SESSION_KEY]
    s_model.clear_cache()
    assert bool(s_model.storage.get(Settings.SESSION_KEY)) is False
    s_model.update_cache()
    assert type(s_model.storage.get(Settings.SESSION_KEY)) is dict
    assert s_model.storage.get(Settings.SESSION_KEY) == settings


def test_get():
    s_model = Settings(session, sub_id)
    assert s_model['subscription'] == sub_id
    assert s_model['color_bg'] == 0xaaffdd


def test_set():
    target = 'color_bg'
    s_model = Settings({}, sub_id)
    old_color = s_model[target]
    new_color = 0xabcabc
    s_model[target] = new_color
    del s_model

    s_model = Settings({}, sub_id)
    assert s_model[target] == new_color
    s_model[target] = old_color
    del s_model

    s_model = Settings({}, sub_id)
    assert s_model[target] == old_color


def test_copy():
    s_model = Settings(session, sub_id)
    s_model.update_cache()
    old_copy = s_model.storage.get(Settings.SESSION_KEY)
    s_model2 = Settings({}, sub_id)
    new_copy = s_model2.copy()
    assert old_copy == new_copy
    assert old_copy is not new_copy


def test_keys():
    s_model = Settings(session, sub_id)
    keys = s_model.keys()
    for k in keys:
        assert s_model[k] is not None


def test_create():
    # TODO: cannot test here. see Subscription class.
    pass

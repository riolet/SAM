import db_connection
import models.livekeys
import models.datasources

sub_id = db_connection.default_sub
ds_full = db_connection.dsid_default
ds_empty = db_connection.dsid_short
ds_other = db_connection.dsid_live
session = {}


def test_create():
    lk_model = models.livekeys.LiveKeys(sub_id)
    ds_ids = (ds_full, ds_empty, ds_other)
    lk_model.delete_all()
    for id in ds_ids:
        lk_model.create(id)

    keys = lk_model.read()
    for key in keys:
        assert key['subscription'] == sub_id
        assert key['ds_id'] in ds_ids
        # TODO: assert key['access_key'] looks "random"?


def test_validate():
    lk_model = models.livekeys.LiveKeys(sub_id)
    lk_model.delete_all()
    lk_model.create(ds_full)
    key = lk_model.read()[0]

    bad_key = models.livekeys.LiveKeys.generate_salt(24)
    blank_key = ""
    no_key = None
    correct_key = key['access_key']

    assert lk_model.validate(bad_key) is None
    assert lk_model.validate(blank_key) is None
    assert lk_model.validate(no_key) is None
    match = lk_model.validate(correct_key)
    assert match and match['datasource'] == key['ds_id']


def test_delete():
    lk_model = models.livekeys.LiveKeys(sub_id)
    lk_model.delete_all()
    lk_model.create(ds_full)
    lk_model.create(ds_full)
    old_keys = lk_model.read()

    lk_model.delete(old_keys[0]['access_key'])

    assert lk_model.validate(old_keys[0]['access_key']) is None
    match = lk_model.validate(old_keys[1]['access_key'])
    assert match and match['datasource'] == old_keys[1]['ds_id']


def test_delete_ds():
    lk_model = models.livekeys.LiveKeys(sub_id)
    lk_model.delete_all()
    lk_model.create(ds_full)
    lk_model.create(ds_full)
    lk_model.create(ds_empty)
    lk_model.create(ds_empty)
    old_keys = lk_model.read()
    assert len(old_keys) == 4

    lk_model.delete_ds(ds_full)

    new_keys = lk_model.read()

    assert len(new_keys) == 2
    assert new_keys[0]['ds_id'] == ds_empty
    assert new_keys[1]['ds_id'] == ds_empty

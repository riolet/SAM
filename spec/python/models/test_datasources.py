import pytest
import web

from spec.python import db_connection
from models.datasources import Datasources

session = {}
db = db_connection.db
sub_id = db_connection.default_sub


def get_table_names(db):
    """
    :type db: web.DB
    :param db: 
    :return: 
    """
    if db.dbname == 'mysql':
        tables = [x.values()[0] for x in db.query("SHOW TABLES;")]
    elif db.dbname == 'sqlite':
        rows = list(db.select('sqlite_master', what='name', where="type='table'"))
        tables = [row['name'] for row in rows]
    else:
        raise ValueError("Unknown dbn. Cannot determine tables")
    return tables


def test_datasources():
    ds = Datasources(db, session, sub_id)
    assert bool(ds.storage.get(Datasources.SESSION_KEY)) is False
    sources = ds.datasources
    assert ds.storage.get(Datasources.SESSION_KEY) == sources
    assert type(sources) is dict


def test_ds_ids():
    ds = Datasources(db, session, sub_id)
    ids = ds.ds_ids
    assert type(ids) is list
    assert type(ids[0]) is long or type(ids[0]) is int


def test_sorted_list():
    ds = Datasources(db, session, sub_id)
    dss = ds.sorted_list()
    assert type(dss) is list
    assert type(dss[0]) is web.Storage

    ids = ds.ds_ids
    ids.sort()
    assert ids == [a['id'] for a in dss]


def test_priority_list():
    ds = Datasources(db, session, sub_id)
    target = ds.ds_ids[-1]
    dss = ds.priority_list(target)
    assert type(dss) is list
    assert type(dss[0]) is web.Storage

    # the first result matches.
    assert dss[0].id == target
    # and the rest are sorted.
    assert [d.id for d in dss[1:]] == sorted([d.id for d in dss[1:]])


def test_update_clear_cache():
    ds = Datasources(db, session, sub_id)
    sources = ds.datasources
    ds.clear_cache()
    assert bool(ds.storage.get(Datasources.SESSION_KEY)) is False
    ds.update_cache()
    assert type(ds.storage.get(Datasources.SESSION_KEY)) is dict
    assert ds.storage.get(Datasources.SESSION_KEY) == sources


def test_set():
    ds = Datasources(db, session, sub_id)
    dsid = ds.ds_ids[0]
    old_name = ds.datasources[dsid].name
    new_name = "temp_new_name"
    ds.set(dsid, name=new_name)
    assert ds.datasources[dsid].name == new_name
    ds.set(dsid, name=old_name)
    assert ds.datasources[dsid].name == old_name

    old_interval = ds.datasources[dsid].ar_interval
    new_interval = 60
    ds.set(dsid, ar_interval=new_interval)
    assert ds.datasources[dsid].ar_interval == new_interval
    ds.set(dsid, ar_interval=old_interval)
    assert ds.datasources[dsid].ar_interval == old_interval


def test_validate_name():
    assert bool(Datasources.validate_ds_name('hello')) is True
    assert bool(Datasources.validate_ds_name('abc123_ _321cba')) is True
    assert bool(Datasources.validate_ds_name('5')) is True
    assert bool(Datasources.validate_ds_name('_')) is True
    assert bool(Datasources.validate_ds_name('a   ')) is False
    assert bool(Datasources.validate_ds_name('   a')) is False
    assert bool(Datasources.validate_ds_name('a*')) is False
    assert bool(Datasources.validate_ds_name('a-a')) is False
    assert bool(Datasources.validate_ds_name('$')) is False


def test_validate_ds_interval():
    assert Datasources.validate_ds_interval(-1) is False
    assert Datasources.validate_ds_interval(4) is False
    assert Datasources.validate_ds_interval(5) is True
    assert Datasources.validate_ds_interval(300) is True
    assert Datasources.validate_ds_interval(1800) is True
    assert Datasources.validate_ds_interval(1801) is False
    assert Datasources.validate_ds_interval(9876543210l) is False


def test_create_remove_datasource():
    ds = Datasources(db, session, sub_id)
    old_tables = get_table_names(db)

    dsid = ds.create_datasource('temp_ds')

    # new table exists
    new_tables = get_table_names(db)
    assert len(new_tables) - len(old_tables) > 0
    assert ds.datasources[dsid].name == 'temp_ds'

    ds.remove_datasource(dsid)
    new_tables = get_table_names(db)
    assert len(new_tables) - len(old_tables) == 0
    with pytest.raises(KeyError):
        assert ds.datasources[dsid].name == 'temp_ds'

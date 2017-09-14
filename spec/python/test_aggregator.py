import os
import requests
import cPickle
import threading
import multiprocessing
import time
import signal
import pytest
from datetime import datetime
from spec.python import db_connection
from sam import server_aggregator
from sam.importers.import_base import BaseImporter
from sam.models.livekeys import LiveKeys
from py._path.local import LocalPath

db = db_connection.db
sub_id = db_connection.default_sub
ds_id = db_connection.dsid_short


def test_Buffer():
    b = server_aggregator.Buffer(sub=sub_id, ds=ds_id)
    assert b.sub == sub_id
    assert b.ds == ds_id
    assert str(b) == repr(b) == '{}-{}-0'.format(sub_id, ds_id)
    assert len(b) == 0
    assert b.expiring == False

    b.add('datum1')
    assert len(b) == 1
    b.add('datum2')
    b.add('datum3')
    assert len(b) == 3
    assert str(b) == repr(b) == '{}-{}-3'.format(sub_id, ds_id)

    b.flag_expired()
    assert b.expiring == True
    b.flag_unexpired()
    assert b.expiring == False

    data = b.pop_all()
    assert data == ['datum1', 'datum2', 'datum3']
    assert len(b) == 0
    assert str(b) == repr(b) == '{}-{}-0'.format(sub_id, ds_id)


def test_MemoryBuffers():
    m = server_aggregator.MemoryBuffers()
    assert len(m.buffers) == 0
    m.create(1,1)
    assert len(m.buffers) == 1
    m.create(1,2)
    assert len(m.buffers) == 1
    m.create(2,1)
    assert len(m.buffers) == 2
    m.create(2,2)
    assert len(m.buffers) == 2
    m.create(1,1)
    assert len(m.buffers) == 2
    m.create(1,2)
    assert len(m.buffers) == 2
    m.create(2,1)
    assert len(m.buffers) == 2
    assert len(m.buffers[1]) == 2
    assert len(m.buffers[2]) == 2

    m.add(3, 3, 'msg1')
    m.add(3, 3, 'msg2')
    m.add(2, 3, 'msg3')
    m.add(2, 2, 'msg4')
    m.add(1, 1, 'msg5')
    assert len(m.buffers) == 3
    assert len(m.buffers[1]) == 2
    assert len(m.buffers[2]) == 3
    assert len(m.buffers[3]) == 1

    d3 = m.yank(3,3)
    assert d3 == ['msg1', 'msg2']

    everything = m.get_all()
    assert len(everything) == 6
    assert map(str, everything) == ['1-1-1', '1-2-0', '2-1-0', '2-2-1', '2-3-1', '3-3-0']

    m.remove(2, 3)
    m.remove(1, 2)
    m.remove(99,99)
    everything = m.get_all()
    assert len(everything) == 4
    assert map(str, everything) == ['1-1-1', '2-1-0', '2-2-1', '3-3-0']


def test_dbi_importer():
    # Tests run_importer and buffer_to_syslog
    dbi = server_aggregator.DatabaseInserter
    table_syslog = "s{}_ds{}_Syslog".format(sub_id, ds_id)
    rows = db.query("SELECT COUNT(0) AS 'c' FROM {}".format(table_syslog))
    assert rows.first().c == 0

    dt = datetime(2016,7,22,13,20)
    messages = [
        {'headers': BaseImporter.keys,
         'lines': [
             [2852047408, 54323, 2852061180, 80, dt, 'TCP', 0, 2340, 0, 30, 1830],
             [2852047409, 54323, 2852061181, 80, dt, 'TCP', 0, 2340, 0, 30, 1830],
             [2852047410, 54323, 2852061182, 80, dt, 'TCP', 0, 2340, 0, 30, 1830]
         ]},
        {'headers': BaseImporter.keys,
         'lines': [
             [2852047411, 54323, 2852061183, 137, dt, 'UDP', 0, 2340, 0, 30, 1830],
             [2852047412, 54323, 2852061184, 137, dt, 'UDP', 0, 2340, 0, 30, 1830],
             [2852047413, 54323, 2852061185, 137, dt, 'UDP', 0, 2340, 0, 30, 1830]
         ]}
    ]

    dbi.run_importer(sub_id, ds_id, messages)

    rows = db.query("SELECT COUNT(0) AS 'c' FROM {}".format(table_syslog))
    assert rows.first().c == 6

    db.query("DELETE FROM {}".format(table_syslog))

    rows = db.query("SELECT COUNT(0) AS 'c' FROM {}".format(table_syslog))
    assert rows.first().c == 0

    dbi = server_aggregator.DatabaseInserter(server_aggregator.MemoryBuffers())
    b = server_aggregator.Buffer(sub_id, ds_id)
    map(b.add, messages)
    dbi.buffer_to_syslog(b)

    rows = db.query("SELECT COUNT(0) AS 'c' FROM {}".format(table_syslog))
    assert rows.first().c == 6

    db.query("DELETE FROM {}".format(table_syslog))

    rows = db.query("SELECT COUNT(0) AS 'c' FROM {}".format(table_syslog))
    assert rows.first().c == 0


def test_dbi_preprocessor():
    # tests run_preprocessor and syslog_to_tables
    dbi = server_aggregator.DatabaseInserter
    table_syslog = "s{}_ds{}_Syslog".format(sub_id, ds_id)
    table_links = "s{}_ds{}_Links".format(sub_id, ds_id)
    table_links1 = "s{}_ds{}_LinksIn".format(sub_id, ds_id)
    table_links2 = "s{}_ds{}_LinksOut".format(sub_id, ds_id)
    rows = db.query("SELECT COUNT(0) AS 'c' FROM {}".format(table_syslog))
    assert rows.first().c == 0

    dt = datetime(2016,7,22,13,20)
    messages = [
        {'headers': BaseImporter.keys,
         'lines': [
             [169090600, 54323, 842810961, 80, dt, 'TCP', 0, 2340, 0, 30, 1830],
             [169090601, 54323, 842811474, 80, dt, 'TCP', 0, 2340, 0, 30, 1830],
             [169091114, 54323, 842811475, 80, dt, 'TCP', 0, 2340, 0, 30, 1830],
             [169091115, 54323, 843074132, 137, dt, 'UDP', 0, 2340, 0, 30, 1830],
             [169353772, 54323, 843074133, 137, dt, 'UDP', 0, 2340, 0, 30, 1830],
             [169353773, 54323, 843074646, 137, dt, 'UDP', 0, 2340, 0, 30, 1830],
             [169090600, 54323, 842810961, 80, dt, 'TCP', 0, 2340, 0, 30, 1830],
             [169091115, 54323, 843074132, 137, dt, 'UDP', 0, 2340, 0, 30, 1830],
             [169353773, 54323, 843074646, 137, dt, 'UDP', 0, 2340, 0, 30, 1830]
         ]}
    ]
    dbi.run_importer(sub_id, ds_id, messages)
    rows = db.query("SELECT COUNT(0) AS 'c' FROM {}".format(table_syslog))
    assert rows.first().c == 9
    rows = db.query("SELECT COUNT(0) AS 'c' FROM {}".format(table_links))
    assert rows.first().c == 0

    dbi.run_preprocessor(sub_id, ds_id)
    rows = db.query("SELECT COUNT(0) AS 'c' FROM {}".format(table_syslog))
    assert rows.first().c == 0
    rows = db.query("SELECT COUNT(0) AS 'c' FROM {}".format(table_links))
    assert rows.first().c == 6

    db.query("DELETE FROM {}".format(table_links1))
    db.query("DELETE FROM {}".format(table_links2))
    db.query("DELETE FROM {}".format(table_links))

    rows = db.query("SELECT COUNT(0) AS 'c' FROM {}".format(table_links))
    assert rows.first().c == 0

    dbi = server_aggregator.DatabaseInserter(server_aggregator.MemoryBuffers())
    b = server_aggregator.Buffer(sub_id, ds_id)
    map(b.add, messages)
    dbi.buffer_to_syslog(b)
    rows = db.query("SELECT COUNT(0) AS 'c' FROM {}".format(table_syslog))
    assert rows.first().c == 9
    rows = db.query("SELECT COUNT(0) AS 'c' FROM {}".format(table_links))
    assert rows.first().c == 0
    dbi.syslog_to_tables(b)
    rows = db.query("SELECT COUNT(0) AS 'c' FROM {}".format(table_syslog))
    assert rows.first().c == 0
    rows = db.query("SELECT COUNT(0) AS 'c' FROM {}".format(table_links))
    assert rows.first().c == 6

    db.query("DELETE FROM {}".format(table_links1))
    db.query("DELETE FROM {}".format(table_links2))
    db.query("DELETE FROM {}".format(table_links))

    rows = db.query("SELECT COUNT(0) AS 'c' FROM {}".format(table_links))
    assert rows.first().c == 0


def test_dbi_process_buffer():
    dbi = server_aggregator.DatabaseInserter(server_aggregator.MemoryBuffers())
    dbi.syslog_to_tables = lambda x: True
    b = server_aggregator.Buffer(sub_id, ds_id)
    b.last_proc_time = time.time() - dbi.TIME_QUOTA - 0.5
    assert dbi.process_buffer(b) == 4

    b.last_proc_time = time.time() - dbi.TIME_QUOTA - 0.5
    assert dbi.process_buffer(b) == 3

    b = server_aggregator.Buffer(sub_id, ds_id)
    b.last_proc_time = time.time()
    b.add('datum1')
    assert dbi.process_buffer(b) == 5

    dt = datetime(2016, 7, 22, 13, 20)
    message = {
        'headers': BaseImporter.keys,
        'lines': [
            [2852047408, 54323, 2852061180, 80, dt, 'TCP', 0, 2340, 0, 30, 1830],
            [2852047409, 54323, 2852061181, 80, dt, 'TCP', 0, 2340, 0, 30, 1830],
            [2852047410, 54323, 2852061182, 80, dt, 'TCP', 0, 2340, 0, 30, 1830],
            [2852047411, 54323, 2852061183, 137, dt, 'UDP', 0, 2340, 0, 30, 1830],
            [2852047412, 54323, 2852061184, 137, dt, 'UDP', 0, 2340, 0, 30, 1830],
            [2852047413, 54323, 2852061185, 137, dt, 'UDP', 0, 2340, 0, 30, 1830],
            [2852047408, 54323, 2852061180, 80, dt, 'TCP', 0, 2340, 0, 30, 1830],
            [2852047411, 54323, 2852061183, 137, dt, 'UDP', 0, 2340, 0, 30, 1830],
            [2852047413, 54323, 2852061185, 137, dt, 'UDP', 0, 2340, 0, 30, 1830]
        ]
    }
    b = server_aggregator.Buffer(sub_id, ds_id)
    b.add(message)
    dbi.buffer_to_syslog(b)

    b.last_proc_time = time.time() - dbi.TIME_QUOTA - 0.5
    assert dbi.process_buffer(b) == 2

    b = server_aggregator.Buffer(sub_id, ds_id)
    b.last_proc_time = time.time()
    dbi.SIZE_QUOTA = 3
    assert dbi.process_buffer(b) == 1

    table_syslog = "s{}_ds{}_Syslog".format(sub_id, ds_id)
    db.query("DELETE FROM {}".format(table_syslog))


def test_dbi_run():
    m = server_aggregator.MemoryBuffers()
    m.add(sub_id, ds_id, 'bogus')
    dbi = server_aggregator.DatabaseInserter(m)
    dbi.buffer_to_syslog = lambda x: True
    dbi.daemon = True
    dbi.start()
    time.sleep(0.2)
    dbi.shutdown()
    dbi.join()
    assert True


def test_agg_validate_data():
    l_model = LiveKeys(db, sub_id)
    access_key = l_model.create(ds_id)

    # wrong data type
    agg = server_aggregator.Aggregator()
    access, errors = agg.validate_data('garbage')
    assert len(errors) != 0

    # access_key missing
    data = {'k': 'v'}
    access, errors = agg.validate_data(data)
    assert len(errors) != 0

    # version missing
    data = {'access_key': access_key}
    access, errors = agg.validate_data(data)
    assert len(errors) != 0

    # version incompatible
    data = {'access_key': access_key, 'version': '0.1'}
    access, errors = agg.validate_data(data)
    assert len(errors) != 0

    # incorrect access key
    data = {'access_key': "bad key", 'version': '1.0'}
    access, errors = agg.validate_data(data)
    assert bool(access) is False

    # success
    data = {'access_key': access_key, 'version': '1.0'}
    access, errors = agg.validate_data(data)
    assert len(errors) == 0

    l_model.delete_all()


def test_agg_socket_to_buffer():
    agg = server_aggregator.Aggregator()

    @staticmethod
    def error_response(x):
        return {}, "failed: blah"

    @staticmethod
    def no_access_response(x):
        return None, ''

    @staticmethod
    def good_response(x):
        return {'subscription': sub_id, 'datasource': ds_id}, ''

    old_validate = server_aggregator.Aggregator.validate_data
    try:
        server_aggregator.Aggregator.validate_data = error_response
        assert agg.socket_to_buffer('datum1') == "failed: blah"

        server_aggregator.Aggregator.validate_data = no_access_response
        assert agg.socket_to_buffer('datum1') == "Not Authorized"

        data = {'msg': 'handshake'}
        server_aggregator.Aggregator.validate_data = good_response
        assert agg.socket_to_buffer(data) == 'handshake'

        dt = datetime(2016, 7, 22, 13, 20)
        data = {
            'headers': BaseImporter.keys,
            'lines': [
                [2852047408, 54323, 2852061180, 80, dt, 'TCP', 0, 2340, 0, 30, 1830],
                [2852047413, 54323, 2852061185, 137, dt, 'UDP', 0, 2340, 0, 30, 1830]
            ]
        }
        server_aggregator.Aggregator.validate_data = good_response
        assert agg.socket_to_buffer(data) == False
    finally:
        server_aggregator.Aggregator.validate_data = old_validate


def test_agg_handle():
    agg = server_aggregator.Aggregator()
    result = agg.handle("bad_data")
    assert result.startswith("failed")

    result = agg.handle(cPickle.dumps([]))
    assert result.startswith("failed")

    @staticmethod
    def success_response(x):
        return ''

    @staticmethod
    def fail_response(x):
        return 'error'

    @staticmethod
    def handshake_response(x):
        return 'handshake'

    old_stb = server_aggregator.Aggregator.socket_to_buffer
    try:
        server_aggregator.Aggregator.socket_to_buffer = handshake_response
        result = agg.handle(cPickle.dumps(['test']))
        assert result == 'handshake'

        server_aggregator.Aggregator.socket_to_buffer = fail_response
        result = agg.handle(cPickle.dumps(['test']))
        assert result.startswith("failed")

        server_aggregator.Aggregator.socket_to_buffer = success_response
        result = agg.handle(cPickle.dumps(['test']))
        assert result == 'success'
    finally:
        server_aggregator.Aggregator.socket_to_buffer = old_stb


def test_agg_ensure_thread():
    assert server_aggregator.IMPORTER_THREAD is None or not server_aggregator.IMPORTER_THREAD.is_alive()
    agg = server_aggregator.Aggregator()
    agg.ensure_processing_thread()
    assert server_aggregator.IMPORTER_THREAD is not None
    assert server_aggregator.IMPORTER_THREAD.is_alive()
    time.sleep(0.1)
    server_aggregator.IMPORTER_THREAD.shutdown()
    server_aggregator.IMPORTER_THREAD.join()
    assert server_aggregator.IMPORTER_THREAD.is_alive() is False

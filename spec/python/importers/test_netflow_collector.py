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
from sam.importers import netflow_collector
from sam.importers.import_tcpdump import TCPDumpImporter
from py._path.local import LocalPath


def test_transmit_lines():
    collector = netflow_collector.Collector()
    collector.transmit_buffer = ['data1', 'data2', 'data3']
    old_request = requests.request
    try:
        mocker = db_connection.Mocker()

        class Response:
            content = "test_response"

        mocker._retval = Response()
        requests.request = mocker

        assert collector.transmit_lines() == 'test_response'
        assert len(mocker.calls) == 1
        call_data_pickled = mocker.calls[0][2]['data']
        call_data = cPickle.loads(call_data_pickled)
        assert set(call_data.keys()) == {'access_key', 'version', 'headers', 'lines'}
        assert collector.transmit_buffer == []
        assert collector.transmit_buffer_size == 0

        mocker._retval = None
        collector.transmit_buffer = ['data1', 'data2', 'data3']
        assert collector.transmit_lines() == 'error'
        assert collector.transmit_buffer == ['data1', 'data2', 'data3']
        assert collector.transmit_buffer_size == 3
    finally:
        requests.request = old_request


def test_test_connection():
    collector = netflow_collector.Collector()
    old_request = requests.request
    mocker = db_connection.Mocker()

    class GoodResponse:
        content = "handshake"

        def __init__(self):
            pass

    class BadResponse:
        content = "problem"

        def __init__(self):
            pass

    class NoResponse:
        def __init__(self):
            pass

    try:

        mocker._retval = GoodResponse()
        requests.request = mocker
        assert collector.test_connection() is True

        mocker._retval = BadResponse()
        requests.request = mocker
        assert collector.test_connection() is False

        mocker._retval = NoResponse()
        assert collector.test_connection() is False

        assert len(mocker.calls) == 3
        call_data_pickled = mocker.calls[0][2]['data']
        call_data = cPickle.loads(call_data_pickled)
        assert set(call_data.keys()) == {'access_key', 'version', 'headers', 'msg', 'lines'}
        assert call_data['msg'] == 'handshake'
    finally:
        requests.request = old_request


def test_thread_batch_processor(tmpdir):
    """
    :type tmpdir: LocalPath
    """
    # testing periodic import and time_between_imports
    collector = netflow_collector.Collector()
    collector.decode_captures = db_connection.Mocker()
    collector.time_between_imports = 0.1  # seconds
    collector.nfcapd_folder = str(tmpdir)
    f1 = tmpdir.join("nfcapd.136488391344")
    f1.write("data1")
    f2 = tmpdir.join("nfcapd.136488391346")
    f2.write("data2")
    f3 = tmpdir.join("nfcapd.current.13648")
    f3.write("data3")

    #t1 = threading.Thread(target=mini_thread, args=(collector,))
    t1 = threading.Thread(target=collector.thread_batch_processor)
    t1.start()
    time.sleep(0.25)
    collector.shutdown()
    t1.join()
    assert len(collector.decode_captures.calls) == 3

    # testing transmissions
    collector = netflow_collector.Collector()
    collector.time_between_imports = 0.1
    collector.time_between_transmits = 0.18
    collector.transmit_buffer_threshold = 2
    collector.transmit_lines = db_connection.Mocker()
    t2 = threading.Thread(target=collector.thread_batch_processor)
    t2.start()
    # thread waiting 0.1
    collector.transmit_buffer_size = 3
    time.sleep(0.14)  # t2 calls transmit due to buffer being overfull.
    # thread waiting 0.1
    collector.transmit_buffer_size = 1
    time.sleep(0.12)  # t2 does nothing.
    # thread waiting 0.1
    collector.transmit_buffer_size = 1
    time.sleep(0.12)  # t2 calls transmit due to time up.
    #thread waiting 0.1
    time.sleep(0.12)  # t2 does nothing.
    #thread waiting 0.1
    collector.transmit_buffer_size = 0
    collector.shutdown()
    t2.join() # t2 does nothing due to empty buffer.
    assert len(collector.transmit_lines.calls) == 2


def test_new_capture_exists(tmpdir):
    collector = netflow_collector.Collector()
    collector.nfcapd_folder = str(tmpdir)

    assert collector.new_capture_exists() == False
    f1 = tmpdir.join("unrelated")
    f1.write("data1")
    assert f1.check()
    assert collector.new_capture_exists() == False
    f2 = tmpdir.join("nfcapd.current.13648")
    f2.write("data2")
    assert f2.check()
    assert collector.new_capture_exists() == False
    f3 = tmpdir.join("nfcapd.136488391346")
    f3.write("data3")
    assert f3.check()
    assert collector.new_capture_exists() == True


def test_decode_netflow_file(tmpdir):
    collector = netflow_collector.Collector()
    with pytest.raises(ValueError):
        collector.decode_netflow_file(str(tmpdir) + "oops")

    path = os.path.join(os.path.dirname(__file__), "nfcapd_test")
    data = collector.decode_netflow_file(path)
    assert len(data) == 13
    assert data[7] == 'TCP  ,     192.168.1.7, 50682,     52.84.25.29,   443,2017-09-05 15:29:15.480,' \
                      '    6831,       0,       0,       0,    0.000\n'


def test_decode_captures(tmpdir):
    """
    :type tmpdir: LocalPath
    """
    path = os.path.join(os.path.dirname(__file__), "nfcapd_test")
    f1 = tmpdir.join('nfcapd.123456789')
    with open(path, 'rb') as f:
        f1.write_binary(f.read())
    assert f1.check()
    collector = netflow_collector.Collector()
    collector.nfcapd_folder = str(tmpdir)
    collector.decode_captures()
    assert collector.transmit_buffer_size == 8
    assert len(collector.transmit_buffer) == 8
    assert collector.transmit_buffer[6] == [3232235783, 50682, 877926685, 443,
        datetime(2017, 9, 5, 15, 29, 15, 480000), 'TCP', 0, 6831, 0, 0, 1]


def test_form_connection():
    q = [True, False, False]
    def mock_test():
        return q.pop()

    collector = netflow_collector.Collector()
    collector.test_connection = mock_test
    assert collector.form_connection(sleep=0) == True

    q.extend([False, False, False])
    assert collector.form_connection(sleep=0, max_tries=3) == False
    assert len(q) == 0


def coll_proc1():
    collector = netflow_collector.Collector()
    collector.test_connection = lambda: True
    collector.run(port=54323, access_key='abc123')


def test_run():
    p_collector = multiprocessing.Process(target=coll_proc1)
    p_collector.daemon = True
    p_collector.start()
    time.sleep(0.2)
    os.kill(p_collector.pid, signal.SIGINT)
    p_collector.join()
    assert True

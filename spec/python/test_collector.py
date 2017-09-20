import os
import requests
import cPickle
from spec.python import db_connection
from sam import server_collector
from sam.importers.import_tcpdump import TCPDumpImporter
from sam.importers.import_paloalto import PaloAltoImporter
import threading
import multiprocessing
import time
import signal

# db = db_connection.db
# sub_id = db_connection.default_sub
# ds_full = db_connection.dsid_default


def test_SocketBuffer():
    assert isinstance(server_collector.SOCKET_BUFFER, server_collector.SocketBuffer)

    buffer = server_collector.SocketBuffer()
    assert len(buffer) == 0
    bs = "".join(map(chr, range(256))) + '\x00'
    buffer.store_data('abc')
    buffer.store_data('def\nghi\rjkl\r\nmno\n\rp')
    buffer.store_data(bs)
    assert len(buffer) == 3

    contents = buffer.pop_all()
    assert len(buffer) == 0
    assert contents[0] == 'abc'
    assert contents[2] == bs


def test_SocketListener():
    buffer = server_collector.SOCKET_BUFFER
    buffer.pop_all()
    assert len(buffer) == 0

    server_collector.SocketListener(('data1', None), ('foreign', 'address'), None)
    server_collector.SocketListener(('data2\n', None), ('foreign', 'address'), None)
    server_collector.SocketListener((' \t data3', None), ('foreign', 'address'), None)
    assert len(buffer) == 3
    datas = buffer.pop_all()
    assert datas == ['data1', 'data2\n', ' \t data3']


def test_FileListener():
    buffer = server_collector.SOCKET_BUFFER
    buffer.pop_all()
    assert len(buffer) == 0

    fl = server_collector.FileListener()
    file_path = os.path.join(os.path.dirname(__file__), "dummy_content.txt")
    assert os.path.exists(file_path)
    with open(file_path, 'r') as f:
        fl.set_file(f)
        fl.daemon = True
        fl.start()
        fl.join()
    assert len(buffer) == 4
    lines = buffer.pop_all()
    assert lines[0] == 'this is line 1'
    assert lines[3] == 'this'


def test_import_packets():
    buffer = server_collector.SOCKET_BUFFER
    buffer.pop_all()
    assert len(buffer) == 0
    buffer_data = [
        "",
        "1491525947.515414 STP 802.1d, Config, Flags [none], bridge-id 8000.f8:32:e4:af:0a:a8.8001, "
            "length 43",
        "1491525947.915376 ARP, Request who-has 192.168.10.106 tell 192.168.10.254, length 46",
        "1491525948.268015 IP 192.168.10.113.33060 > 172.217.3.196.443: Flags [P.], seq 256:730, "
            "ack 116, win 3818, options [nop,nop,TS val 71847613 ecr 4161606244], length 474",
        "1491525737.317942 IP 192.168.10.254.1900 > 239.238.237.236.55943: UDP, length 166, "
            "other info",
        "1491525737.317942 IP 192.168.10.254.55943 > 239.255.255.250.1900: UDP, length 449",
        "",
        "nonsensical entry",
        "",
    ]
    map(buffer.store_data, buffer_data)

    collector = server_collector.Collector()
    collector.importer = TCPDumpImporter()
    assert len(buffer) == 9
    assert collector.transmit_buffer == []
    assert collector.transmit_buffer_size == 0

    collector.import_packets()
    assert len(buffer) == 0
    assert len(collector.transmit_buffer) == 3
    assert collector.transmit_buffer_size == 3


def test_transmit_lines():
    collector = server_collector.Collector()
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
    collector = server_collector.Collector()
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


def test_thread_batch_processor():
    buffer = server_collector.SOCKET_BUFFER
    buffer.pop_all()
    assert len(buffer) == 0

    # testing periodic import and time_between_imports
    collector = server_collector.Collector()
    buffer.store_data('data1')
    collector.import_packets = db_connection.Mocker()
    collector.time_between_imports = 0.1  # seconds
    #t1 = threading.Thread(target=mini_thread, args=(collector,))
    t1 = threading.Thread(target=collector.thread_batch_processor)
    t1.start()
    time.sleep(0.25)
    collector.shutdown()
    t1.join()
    assert len(collector.import_packets.calls) == 3
    buffer.pop_all()
    assert len(buffer) == 0

    # testing transmissions
    collector = server_collector.Collector()
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
    time.sleep(0.1)  # t2 does nothing.
    # thread waiting 0.1
    collector.transmit_buffer_size = 1
    time.sleep(0.1)  # t2 calls transmit due to time up.
    #thread waiting 0.1
    collector.transmit_buffer_size = 0
    collector.shutdown()
    t2.join() # t2 does nothing due to empty buffer.
    assert len(collector.transmit_lines.calls) == 2


def test_get_importer():
    collector = server_collector.Collector()
    collector.default_format = "tcpdump"
    imp = collector.get_importer("paloalto")
    assert isinstance(imp, PaloAltoImporter)
    imp = collector.get_importer(None)
    assert isinstance(imp, TCPDumpImporter)
    imp = collector.get_importer("missing")
    assert imp is None


def test_form_connection():
    q = [True, False, False]
    def mock_test():
        return q.pop()

    collector = server_collector.Collector()
    collector.test_connection = mock_test
    assert collector.form_connection(sleep=0) == True

    q.extend([False, False, False])
    assert collector.form_connection(sleep=0, max_tries=3) == False
    assert len(q) == 0


def coll_proc1():
    collector = server_collector.Collector()
    collector.test_connection = lambda: True
    imp_format = "tcpdump"
    collector.run(port=54323, format=imp_format, access_key='abc123')


def test_run():
    p_collector = multiprocessing.Process(target=coll_proc1)
    p_collector.daemon = True
    p_collector.start()
    time.sleep(0.2)
    os.kill(p_collector.pid, signal.SIGINT)
    p_collector.join()
    assert True


def coll_proc2(stream):
    collector = server_collector.Collector()
    collector.test_connection = lambda: True
    collector.transmit_lines = lambda: None
    imp_format = "tcpdump"
    collector.run_streamreader(stream, format=imp_format, access_key='abc123')


def test_run_stream():
    file_path = os.path.join(os.path.dirname(__file__), "dummy_content.txt")
    assert os.path.exists(file_path)
    f = open(file_path, 'r')
    try:
        p_collector = multiprocessing.Process(target=coll_proc2, args=(f,))
        p_collector.daemon = True
        p_collector.start()
        time.sleep(0.2)
        os.kill(p_collector.pid, signal.SIGINT)
        p_collector.join()
    finally:
        f.close()
    assert True

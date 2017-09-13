import os
import requests
import cPickle
from spec.python import db_connection
from sam import server_collector
from sam.importers.import_tcpdump import TCPDumpImporter
import sam.common
import sam.constants
import web

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
        """1491525947.515414 STP 802.1d, Config, Flags [none], bridge-id 8000.f8:32:e4:af:0a:a8.8001, length 43""",
        """1491525947.915376 ARP, Request who-has 192.168.10.106 tell 192.168.10.254, length 46""",
        """1491525948.268015 IP 192.168.10.113.33060 > 172.217.3.196.443: Flags [P.], seq 256:730, ack 116, win 3818, options [nop,nop,TS val 71847613 ecr 4161606244], length 474""",
        """1491525737.317942 IP 192.168.10.254.1900 > 239.238.237.236.55943: UDP, length 166, other info""",
        """1491525737.317942 IP 192.168.10.254.55943 > 239.255.255.250.1900: UDP, length 449""",
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




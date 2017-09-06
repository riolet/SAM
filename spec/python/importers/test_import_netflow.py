import os
import pytest
from datetime import datetime
from spec.python import db_connection
from sam.importers import import_base, import_netflow

sample_log = [
    "",
    "UDP  ,     192.168.1.8, 43047,   199.19.167.36,   123,2017-09-05 15:28:41.960,       0,       0,       0,       0,    0.000",
    "ICMP ,     192.168.1.7,     0,     192.168.1.1,   0.0,2017-09-05 15:28:41.960,       0,       0,       0,       0,    0.000",
    "TCP  ,     192.168.1.7, 54766,    23.60.72.157,   443,2017-09-05 15:29:10.470,   12557,       0,       0,       0,    0.000",
    "ICMP ,     192.168.1.7,     0,     192.168.1.1,   0.0,2017-09-05 15:29:10.480,     315,       0,       0,       0,    0.000",
    "TCP  ,     192.168.1.7, 55178,   157.240.11.22,   443,2017-09-05 15:29:11.500,   68616,       0,       0,       0,    0.000",
    'TCP  ,    172.21.15.65,  8080,   172.21.51.236, 38597,2016-07-22 12:54:01.385,    4292,       0,      10,       0,    0.236',
    'TCP  ,   172.21.51.236, 38597,    172.21.15.65,  8080,2016-07-22 12:54:01.385,    1461,     230,      11,       2,    0.236',
    'UDP  ,     172.21.35.5, 33877,   172.21.51.236,  1514,2016-07-22 13:06:12.649,   3.9 M,       0,    7756,       0,  152.037',
    'UDP  ,   172.21.51.236, 40293,  168.94.169.251,    53,2016-07-22 12:54:01.560,     140,       0,       2,       0,    0.001',
    "",
    "nonsensical entry",
    "",
]


def test_class():
    assert import_netflow.class_ == import_netflow.NetFlowImporter


def test_safe_translate():
    assert import_netflow.safe_translate("0") == 0
    assert import_netflow.safe_translate("1") == 1
    assert import_netflow.safe_translate("123456") == 123456
    assert import_netflow.safe_translate("12.45 M") == 12450000
    assert import_netflow.safe_translate("12.45 G") == 12450000000
    assert import_netflow.safe_translate("12.45 T") == 12450000000000
    assert import_netflow.safe_translate("12.45M") == 12450000
    with pytest.raises(ValueError):
        assert import_netflow.safe_translate("12.45W") == 1245


def test_import_file():
    nf = import_netflow.NetFlowImporter()
    collected = []
    def mock_inserter(rows, counter):
        print("adding {} lines.".format(counter))
        collected.extend(rows[:counter])
    nf.insert_data = mock_inserter

    with pytest.raises(ValueError):
        nf.import_file(os.path.join(os.path.dirname(__file__), "error"))

    assert nf.import_file(os.path.join(os.path.dirname(__file__), "nfcapd_test")) == 8
    assert len(collected) == 8
    assert collected[3] == {
        'bytes_received': 150517,
        'bytes_sent': 0,
        'dst': 2649756223,
        'dstport': 443,
        'duration': 1,
        'packets_received': 0,
        'packets_sent': 0,
        'protocol': 'TCP',
        'src': 3232235783,
        'srcport': 45092,
        'timestamp': datetime(2017, 9, 5, 15, 29, 12, 530000)
    }


def test_import_string():
    with open(os.path.join(os.path.dirname(__file__), "nfcapd_test"), 'rb') as f:
        data = f.read()
    nf = import_netflow.NetFlowImporter()
    collected = []
    def mock_inserter(rows, counter):
        print("adding {} lines.".format(counter))
        collected.extend(rows[:counter])
    nf.insert_data = mock_inserter

    assert nf.import_string(data) == 8
    assert len(collected) == 8
    assert collected[3] == {
        'bytes_received': 150517,
        'bytes_sent': 0,
        'dst': 2649756223,
        'dstport': 443,
        'duration': 1,
        'packets_received': 0,
        'packets_sent': 0,
        'protocol': 'TCP',
        'src': 3232235783,
        'srcport': 45092,
        'timestamp': datetime(2017, 9, 5, 15, 29, 12, 530000)
    }


def test_translate():
    nf = import_netflow.NetFlowImporter()

    translated_lines = []
    for i, line in enumerate(sample_log):
        d = {}
        r = nf.translate(line, i+1, d)
        if r == 0:
            assert set(d.keys()) == set(import_base.BaseImporter.keys)
            translated_lines.append(d)

    assert len(translated_lines) == 9
    assert translated_lines[3] == {
        "src": 3232235783,
        "srcport": 0,
        "dst": 3232235777,
        "dstport": 0,
        "timestamp": datetime(2017,9,5,15,29,10,480000),
        "protocol": 'ICMP',
        "bytes_sent": 0,
        "bytes_received": 315,
        "packets_sent": 0,
        "packets_received": 0,
        "duration": 1,
    }
    assert translated_lines[6] == {
        "src": 2887070700,
        "srcport": 38597,
        "dst": 2887061313,
        "dstport": 8080,
        "timestamp": datetime(2016,7,22,12,54,1,385000),
        "protocol": 'TCP',
        "bytes_sent": 230,
        "bytes_received": 1461,
        "packets_sent": 2,
        "packets_received": 11,
        "duration": 1,
    }
    assert translated_lines[7] == {
        "src": 2887066373,
        "srcport": 33877,
        "dst": 2887070700,
        "dstport": 1514,
        "timestamp": datetime(2016,7,22,13,6,12,649000),
        "protocol": 'UDP',
        "bytes_sent": 0,
        "bytes_received": 3900000,
        "packets_sent": 0,
        "packets_received": 7756,
        "duration": 152,
    }

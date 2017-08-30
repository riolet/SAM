from datetime import datetime
from sam.importers import import_base, import_tcpdump

sample_log = [
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


def test_class():
    assert import_tcpdump.class_ == import_tcpdump.TCPDumpImporter


def test_translate():
    tcp = import_tcpdump.TCPDumpImporter()

    translated_lines = []
    for i, line in enumerate(sample_log):
        d = {}
        r = tcp.translate(line, i+1, d)
        if r == 0:
            assert set(d.keys()) == set(import_base.BaseImporter.keys)
            translated_lines.append(d)

    assert len(translated_lines) == 3
    assert translated_lines[0] == {
        "src": 3232238193,
        "srcport": 33060,
        "dst": 2899903428,
        "dstport": 443,
        "timestamp": datetime(2017, 4, 6, 17, 45, 48, 268015),
        "protocol": 'TCP',
        "bytes_sent": 474,
        "bytes_received": '0',
        "packets_sent": '1',
        "packets_received": '0',
        "duration": '1',
    }
    assert translated_lines[1] == {
        "src": 4025413100,
        "srcport": 55943,
        "dst": 3232238334,
        "dstport": 1900,
        "timestamp": datetime(2017, 4, 6, 17, 42, 17, 317942),
        "protocol": 'UDP',
        "bytes_sent": '0',
        "bytes_received": 166,
        "packets_sent": '0',
        "packets_received": '1',
        "duration": '1',
    }
    assert translated_lines[2] == {
        "src": 3232238334,
        "srcport": 55943,
        "dst": 4026531834,
        "dstport": 1900,
        "timestamp": datetime(2017, 4, 6, 17, 42, 17, 317942),
        "protocol": 'UDP',
        "bytes_sent": 449,
        "bytes_received": '0',
        "packets_sent": '1',
        "packets_received": '0',
        "duration": '1',
    }


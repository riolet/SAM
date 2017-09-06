from datetime import datetime
from spec.python import db_connection
from sam.importers import import_base, import_tshark

sample_log = [
    "",
    '1@Sep  6, 2017 11:53:24.635436385 PDT@74.125.135.189@443@@192.168.1.7@40548@@TLSv1.2',
    '2@Sep  6, 2017 11:53:24.635472913 PDT@192.168.1.7@40548@@74.125.135.189@443@@TCP',
    '3@Sep  6, 2017 11:53:26.177349630 PDT@192.168.1.1@@27979@192.168.1.7@@8787@UDP',
    '4@Sep  6, 2017 11:53:26.177373925 PDT@192.168.1.7,192.168.1.1@@27979@192.168.1.1,192.168.1.7@@8787@ICMP',
    '5@Sep  6, 2017 11:53:26.178094470 PDT@192.168.1.1@@514@192.168.1.7@@5140@Syslog',
    '6@Sep  6, 2017 11:53:26.178103965 PDT@192.168.1.7,192.168.1.1@@514@192.168.1.1,192.168.1.7@@5140@ICMP',
    '7@Sep  6, 2017 11:53:31.210863195 PDT@192.168.1.1@@27979@192.168.1.7@@8787@UDP',
    '8@Sep  6, 2017 11:53:31.210909180 PDT@192.168.1.7,192.168.1.1@@27979@192.168.1.1,192.168.1.7@@8787@ICMP',
    '9@Sep  6, 2017 11:53:31.211638790 PDT@192.168.1.1@@514@192.168.1.7@@5140@Syslog',
    '10@Sep  6, 2017 11:53:31.211670857 PDT@192.168.1.7,192.168.1.1@@514@192.168.1.1,192.168.1.7@@5140@ICMP',
    '11@Sep  6, 2017 11:53:33.316380346 PDT@192.168.1.7@@56863@192.168.10.254@@53@DNS',
    '12@Sep  6, 2017 11:53:33.316421252 PDT@192.168.1.7@@56863@192.168.10.254@@53@DNS',
    '13@Sep  6, 2017 11:53:33.346702736 PDT@192.168.10.254@@53@192.168.1.7@@56863@DNS',
    '14@Sep  6, 2017 11:53:33.349263723 PDT@192.168.10.254@@53@192.168.1.7@@56863@DNS',
    '15@Sep  6, 2017 11:53:33.349625896 PDT@192.168.1.7@53128@@104.31.70.170@80@@TCP',
    "",
    "nonsensical entry",
    "",
]


def test_class():
    assert import_tshark.class_ == import_tshark.TSharkImporter


def test_translate():
    pa = import_tshark.TSharkImporter()

    translated_lines = []
    for i, line in enumerate(sample_log):
        d = {}
        r = pa.translate(line, i+1, d)
        print("got {} from: {}".format(r, line[:50]))
        if r == 0:
            assert set(d.keys()) == set(import_base.BaseImporter.keys)
            translated_lines.append(d)

    assert len(translated_lines) == 15
    assert translated_lines[0] == {
        "src": 3232235783,
        "srcport": 40548,
        "dst": 1249740733,
        "dstport": 443,
        "timestamp": datetime(2017,9,6,11,53,24),
        "protocol": 'TCP',
        "bytes_sent": 0,
        "bytes_received": 100,
        "packets_sent": 0,
        "packets_received": 1,
        "duration": 1,
    }

    assert translated_lines[2] == {
        "src": 3232235777,
        "srcport": 27979,
        "dst": 3232235783,
        "dstport": 8787,
        "timestamp": datetime(2017,9,6,11,53,26),
        "protocol": 'UDP',
        "bytes_sent": 100,
        "bytes_received": 0,
        "packets_sent": 1,
        "packets_received": 0,
        "duration": 1,
    }

    assert translated_lines[9] == {
        "src": 3232235777,
        "srcport": 5140,
        "dst": 3232235783,
        "dstport": 514,
        "timestamp": datetime(2017,9,6,11,53,31),
        "protocol": 'ICMP',
        "bytes_sent": 0,
        "bytes_received": 100,
        "packets_sent": 0,
        "packets_received": 1,
        "duration": 1,
    }

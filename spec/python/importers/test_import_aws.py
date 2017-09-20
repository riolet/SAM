from datetime import datetime
from spec.python import db_connection
from sam.importers import import_base, import_aws

sample_log = [
    "",
    "todo:use real template 1.2.3.4 5.6.7.8 54417 80 blah blah blah 1504722134.778341 blah"
    "",
    "nonsensical entry",
    "",
]


def test_class():
    assert import_aws.class_ == import_aws.AWSImporter


def test_translate():
    pa = import_aws.AWSImporter()

    translated_lines = []
    for i, line in enumerate(sample_log):
        d = {}
        r = pa.translate(line, i+1, d)
        if r == 0:
            assert set(d.keys()) == set(import_base.BaseImporter.keys)
            translated_lines.append(d)

    assert len(translated_lines) == 1
    assert translated_lines[0] == {
        "src": 16909060,
        "srcport": 54417,
        "dst": 84281096,
        "dstport": 80,
        "timestamp": datetime(2017,9,6,11,22,14,778341),
        "protocol": 'TCP',
        "bytes_sent": '1',
        "bytes_received": '1',
        "packets_sent": '1',
        "packets_received": '1',
        "duration": '1',
    }

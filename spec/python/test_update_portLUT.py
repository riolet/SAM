import os
import json
from spec.python import db_connection
from sam import constants, update_portLUT
from py._path.local import LocalPath

db = db_connection.db
sub_id = db_connection.default_sub
ds_full = db_connection.dsid_default

mock_origin = "file://{}".format(os.path.join(os.path.dirname(__file__), "portlut_mock.csv"))


def test_get_raw_data():
    update_portLUT.ORIGIN = mock_origin
    rows = update_portLUT.get_raw_data()
    assert len(rows) == 101
    row35_expected = ['', '16', 'tcp', 'Unassigned', '', '', '', '', '', '', '', '']
    assert rows[35] == row35_expected
    row68_expected = ['msg-auth','31','tcp','MSG Authentication','[Robert_Thomas]','[Robert_Thomas]','','','','','','']
    assert rows[68] == row68_expected


def test_expand():
    assert update_portLUT.expand("1") == [1]
    assert update_portLUT.expand("1,2,4,8,16") == [1,2,4,8,16]
    assert update_portLUT.expand("1-2,4-8,16-32") == [1,2,4,5,6,7,8,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32]
    assert update_portLUT.expand("1, 2,3-6") == [1,2,3,4,5,6]


def test_escape():
    assert update_portLUT.escape('test\nnewlines') == 'test newlines'
    assert update_portLUT.escape('test\rnewlines') == 'test newlines'
    assert update_portLUT.escape('test"newlines') == r'test\"newlines'
    assert update_portLUT.escape('test\n\rnewlines') == 'test  newlines'
    assert update_portLUT.escape('test\r\nnewlines') == 'test  newlines'
    assert update_portLUT.escape('test\n\rnewlines') == 'test  newlines'
    assert update_portLUT.escape('test\r\nnewlines') == 'test  newlines'
    assert update_portLUT.escape('abc\r\n"def\n\r\'ghi\'\n\njkl"\r\rmno') == 'abc  \\"def  \'ghi\'  jkl\\"  mno'


def test_filter_lines():
    update_portLUT.ORIGIN = mock_origin
    rows = update_portLUT.get_raw_data()
    filtered = update_portLUT.filter_lines(rows)
    assert len(filtered) == 63
    assert filtered[4] == ['compressnet', 3, {'tcp'}, 'Compression Process']
    assert filtered[5] == ['compressnet', 3, {'udp'}, 'Compression Process']
    assert filtered[43] == ['dsp', 33, {'tcp'}, 'Display Support Protocol']
    assert filtered[44] == ['dsp', 33, {'udp'}, 'Display Support Protocol']


def test_combine_duplicates():
    update_portLUT.ORIGIN = mock_origin
    rows = update_portLUT.get_raw_data()
    filtered = update_portLUT.filter_lines(rows)
    ports = update_portLUT.combine_duplicates(filtered)
    assert len(ports) == 28
    assert ports[2] == ['compressnet', 3, {'udp', 'tcp'}, 'Compression Process']
    assert ports[19] == ['dsp', 33, {'udp', 'tcp'}, 'Display Support Protocol']


def test_build_output_string():
    ports = [
        ['tcpmux', 1, {'udp', 'tcp'}, 'TCP Port Service Multiplexer'],
        ['compressnet', 2, {'udp', 'tcp'}, 'Management Utility'],
        ['compressnet', 3, {'udp', 'tcp'}, 'Compression Process'], ['rje', 5, {'udp', 'tcp'}, 'Remote Job Entry'],
        ['echo', 7, {'udp', 'tcp'}, 'Echo'], ['discard', 9, {'dccp', 'udp', 'sctp', 'tcp'}, 'Discard'],
        ['systat', 11, {'udp', 'tcp'}, 'Active Users'], ['daytime', 13, {'udp', 'tcp'}, 'Daytime'],
        ['qotd', 17, {'udp', 'tcp'}, 'Quote of the Day'],
        ['msp', 18, {'udp', 'tcp'}, 'Message Send Protocol (historic)'],
        ['chargen', 19, {'udp', 'tcp'}, 'Character Generator'],
        ['ftp-data', 20, {'udp', 'sctp', 'tcp'}, 'File Transfer [Default Data]'],
        ['ftp', 21, {'udp', 'sctp', 'tcp'}, 'File Transfer Protocol [Control]'],
        ['ssh', 22, {'udp', 'sctp', 'tcp'}, 'The Secure Shell (SSH) Protocol'],
        ['telnet', 23, {'udp', 'tcp'}, 'Telnet'], ['smtp', 25, {'udp', 'tcp'}, 'Simple Mail Transfer'],
        ['nsw-fe', 27, {'udp', 'tcp'}, 'NSW User System FE'], ['msg-icp', 29, {'udp', 'tcp'}, 'MSG ICP'],
        ['msg-auth', 31, {'udp', 'tcp'}, 'MSG Authentication'],
        ['dsp', 33, {'udp', 'tcp'}, 'Display Support Protocol'], ['time', 37, {'udp', 'tcp'}, 'Time'],
        ['rap', 38, {'udp', 'tcp'}, 'Route Access Protocol'],
        ['rlp', 39, {'udp', 'tcp'}, 'Resource Location Protocol'], ['graphics', 41, {'udp', 'tcp'}, 'Graphics'],
        ['name', 42, {'udp', 'tcp'}, 'Host Name Server'], ['nicname', 43, {'udp', 'tcp'}, 'Who Is'],
        ['mpm-flags', 44, {'udp', 'tcp'}, 'MPM FLAGS Protocol'],
        ['mpm', 45, {'udp', 'tcp'}, 'Message Processing Module [recv]']
    ]
    out_string = update_portLUT.build_output_string(ports)
    j = json.loads(out_string)
    assert j.keys() == ['ports']
    assert len(j['ports']) == 28
    assert j['ports']['33'] == {u'description': u'Display Support Protocol', u'port': 33, u'protocols': u'UDP,TCP', u'name': u'dsp'}
    assert j['ports']['3'] == {u'description': u'Compression Process', u'port': 3, u'protocols': u'UDP,TCP', u'name': u'compressnet'}


def test_write_default_port_data(tmpdir):
    """
    :param tmpdir: temporary directory for test purposes.
     :type tmpdir: LocalPath
    """
    print("tmpdir == {}".format(tmpdir))
    print("type(tmpdir) == {}".format(type(tmpdir)))
    demo = tmpdir.join('demo.json')
    update_portLUT.OUT_FILE = str(demo)
    demo_text = "this is\ndemo text\n.\n"
    update_portLUT.write_default_port_data(demo_text)
    assert demo.read() == demo_text

def test_rebuild_lut(tmpdir):
    """
    :param tmpdir: temporary directory for test purposes.
     :type tmpdir: LocalPath
    """
    demo = tmpdir.join('demo.json')
    update_portLUT.ORIGIN = mock_origin
    update_portLUT.OUT_FILE = str(demo)
    update_portLUT.rebuild_lut()

    j = json.loads(demo.read())
    assert j.keys() == ['ports']
    assert len(j['ports']) == 28
    assert j['ports']['33'] == {u'description': u'Display Support Protocol', u'port': 33, u'protocols': u'UDP,TCP', u'name': u'dsp'}
    assert j['ports']['3'] == {u'description': u'Compression Process', u'port': 3, u'protocols': u'UDP,TCP', u'name': u'compressnet'}

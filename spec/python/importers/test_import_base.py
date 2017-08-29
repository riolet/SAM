import sys
import pytest
from datetime import datetime
from sam import constants
from spec.python import db_connection
from sam.importers import import_asa, import_aws, import_base, import_nfdump, import_paloalto, import_tcpdump, import_tshark

db = db_connection.db
sub_id = db_connection.default_sub
ds_id = db_connection.dsid_default


def test_ip_to_int():
    assert import_base.BaseImporter.ip_to_int(0,0,0,0) == 0
    assert import_base.BaseImporter.ip_to_int(0,0,0,255) == 255
    assert import_base.BaseImporter.ip_to_int(0,0,255,0) == 255 * 2**8
    assert import_base.BaseImporter.ip_to_int(0,255,0,0) == 255 * 2**16
    assert import_base.BaseImporter.ip_to_int(255,0,0,0) == 255 * 2**24
    assert import_base.BaseImporter.ip_to_int(255,255,255,255) == 2**32-1


def test_get_importer():
    sub_id = 1
    ds_id = 1

    # basic
    imp = import_base.get_importer('paloalto', sub_id, ds_id)
    assert isinstance(imp, import_base.BaseImporter)
    assert isinstance(imp, import_paloalto.PaloAltoImporter)
    assert imp.subscription == sub_id
    assert imp.ds_id == ds_id

    # names
    imp = import_base.get_importer('import_paloalto', sub_id, ds_id)
    assert isinstance(imp, import_paloalto.PaloAltoImporter)
    imp = import_base.get_importer('import_paloalto.py', sub_id, ds_id)
    assert isinstance(imp, import_paloalto.PaloAltoImporter)
    imp = import_base.get_importer('paloalto.py', sub_id, ds_id)
    assert isinstance(imp, import_paloalto.PaloAltoImporter)
    imp = import_base.get_importer('paloalto.pyc', sub_id, ds_id)
    assert isinstance(imp, import_paloalto.PaloAltoImporter)
    imp = import_base.get_importer('paloalto.pyo', sub_id, ds_id)
    assert isinstance(imp, import_paloalto.PaloAltoImporter)
    imp = import_base.get_importer('paloalto.pyc', sub_id, ds_id)
    assert isinstance(imp, import_paloalto.PaloAltoImporter)
    imp = import_base.get_importer('PaLoAlTo', sub_id, ds_id)
    assert isinstance(imp, import_paloalto.PaloAltoImporter)

    # different formats
    imp = import_base.get_importer('asa', sub_id, ds_id)
    assert isinstance(imp, import_asa.ASAImporter)
    imp = import_base.get_importer('aws', sub_id, ds_id)
    assert isinstance(imp, import_aws.AWSImporter)
    imp = import_base.get_importer('nfdump', sub_id, ds_id)
    assert isinstance(imp, import_nfdump.NFDumpImporter)
    imp = import_base.get_importer('paloalto', sub_id, ds_id)
    assert isinstance(imp, import_paloalto.PaloAltoImporter)
    imp = import_base.get_importer('tcpdump', sub_id, ds_id)
    assert isinstance(imp, import_tcpdump.TCPDumpImporter)
    imp = import_base.get_importer('tshark', sub_id, ds_id)
    assert isinstance(imp, import_tshark.TSharkImporter)

    # sub and ds are set
    imp = import_base.get_importer('tshark', sub_id=123, ds_id=456)
    assert isinstance(imp, import_tshark.TSharkImporter)
    assert imp.subscription == 123
    assert imp.ds_id == 456
    assert imp.ds_name == None
    imp = import_base.get_importer('tshark', sub_id=123, ds_id="789")
    assert isinstance(imp, import_tshark.TSharkImporter)
    assert imp.subscription == 123
    assert imp.ds_id == 789
    assert imp.ds_name == None
    imp = import_base.get_importer('tshark', sub_id=123, ds_id="title")
    assert isinstance(imp, import_tshark.TSharkImporter)
    assert imp.subscription == 123
    assert imp.ds_id == None
    assert imp.ds_name == "title"


def test_determine_datasource():
    bi = import_base.BaseImporter()

    argv = ['file.py', 'log_file']
    with pytest.raises(ValueError):
        bi.determine_datasource(argv)

    assert bi.ds_id == None
    assert bi.ds_name == None
    argv = ['file.py', 'log_file', 'datasource']
    assert bi.determine_datasource(argv) == 'datasource'
    assert bi.ds_id == None
    assert bi.ds_name == 'datasource'
    argv = ['file.py', 'log_file', '159']
    assert bi.determine_datasource(argv) == 159
    assert bi.ds_id == 159
    assert bi.ds_name == 'datasource'


def test_validate_file(tmpdir):
    path = tmpdir.join("hello.txt")
    path.write("content")

    assert import_base.BaseImporter.validate_file(str(path)) == True
    assert import_base.BaseImporter.validate_file("/dev/null/what") == False


def test_translate():
    bi = import_base.BaseImporter()
    with pytest.raises(NotImplementedError):
        bi.translate("", 1, {})


def test_import_string():
    bi = import_base.BaseImporter()

    def mock_translate(l, ln, d):
        d['src'] = ln
        return 0

    def mock_translate_half(l, ln, d):
        d['src'] = ln
        if ln % 2 == 0:
            return 0
        else:
            return 1


    bi.translate = mock_translate
    bi.insert_data = db_connection.Mocker()
    inserted = bi.import_string("blank\n" * 10)
    assert inserted == 10
    assert len(bi.insert_data.calls) == 1
    assert bi.insert_data.calls[0][1][1] == 10

    bi.translate = mock_translate_half
    bi.insert_data = db_connection.Mocker()
    inserted = bi.import_string("blank\n" * 10)
    assert inserted == 5
    assert len(bi.insert_data.calls) == 1
    assert bi.insert_data.calls[0][1][1] == 5

    bi.translate = mock_translate
    bi.insert_data = db_connection.Mocker()
    inserted = bi.import_string("blank\n" * 2010)
    assert inserted == 2010
    assert len(bi.insert_data.calls) == 3
    assert bi.insert_data.calls[0][1][1] == 1000
    assert bi.insert_data.calls[1][1][1] == 1000
    assert bi.insert_data.calls[2][1][1] == 10


def test_import_file(tmpdir):
    bi = import_base.BaseImporter()
    path = tmpdir.join("log.txt")
    path.write("blank\n" * 2010)

    def mock_translate(l, ln, d):
        d['src'] = ln
        return 0

    def mock_translate_half(l, ln, d):
        d['src'] = ln
        if ln % 2 == 0:
            return 0
        else:
            return 1

    bi.translate = mock_translate
    bi.insert_data = db_connection.Mocker()
    inserted = bi.import_file(str(path))
    assert inserted == 2010
    assert len(bi.insert_data.calls) == 3
    assert bi.insert_data.calls[0][1][1] == 1000
    assert bi.insert_data.calls[1][1][1] == 1000
    assert bi.insert_data.calls[2][1][1] == 10


def test_reverse_connection():
    bi = import_base.BaseImporter()

    b_normal = {
        'src': 111,
        'srcport': 32768,
        'dst': 222,
        'dstport': 80,
        'bytes_sent': 101,
        'bytes_received': 102,
        'packets_sent': 201,
        'packets_received': 202
    }
    b_reversed = {
        'src': 222,
        'srcport': 80,
        'dst': 111,
        'dstport': 32768,
        'bytes_sent': 102,
        'bytes_received': 101,
        'packets_sent': 202,
        'packets_received': 201
    }

    normal = b_normal.copy()
    bi.reverse_connection(normal)
    assert normal == b_reversed

    reversed = b_reversed.copy()
    bi.reverse_connection(reversed)
    assert reversed == b_normal


def test_insert_data():
    table_name = "s{acct}_ds{ds}_Syslog".format(acct=sub_id, ds=ds_id)
    db.query("DELETE FROM {}".format(table_name))

    count = db.query("SELECT COUNT(1) AS 'c' FROM {}".format(table_name)).first()['c']
    assert count == 0

    bi = import_base.BaseImporter()
    param_rows = [{
        "src": 1,
        "srcport": 2,
        "dst": 3,
        "dstport": 4,
        "timestamp": datetime.fromtimestamp(5),
        "protocol": 'TCP',
        "bytes_sent": 7,
        "bytes_received": 8,
        "packets_sent": 9,
        "packets_received": 10,
        "duration": 11,
    }]
    param_count = 1

    # no subscription specified
    with pytest.raises(ValueError):
        bi.subscription = None
        bi.ds_id = None
        bi.ds_name = None
        bi.insert_data(param_rows, param_count)

    # no datasource specified
    with pytest.raises(ValueError):
        bi.subscription = sub_id
        bi.ds_id = None
        bi.ds_name = None
        bi.insert_data(param_rows, param_count)

    with pytest.raises(AssertionError):
        bi.subscription = sub_id
        bi.ds_id = ds_id
        bi.ds_name = None
        missing_param_rows = [param_rows[0].copy()]
        missing_param_rows[0].pop('packets_sent')
        bi.insert_data(missing_param_rows, param_count)

    bi.subscription = sub_id
    bi.ds_id = ds_id
    bi.ds_name = None
    bi.insert_data(param_rows, param_count)
    count = db.query("SELECT COUNT(1) AS 'c' FROM {}".format(table_name)).first()['c']
    assert count == 1

import db_connection
import models.details

db = db_connection.get_test_db_connection()
sub_id = db_connection.default_sub
ds_full = db_connection.dsid_default
ds_empty = db_connection.dsid_short
db_connection.setup_details_network(db, sub_id, ds_full)


def close_to(a, b, epsilon=0.001):
    return abs(float(a) - float(b)) < epsilon


def test_get_metadata():
    m_details = models.details.Details(sub_id, ds_full, "10.20.30.40")
    meta = m_details.get_metadata()

    assert meta['total_out'] == 24
    assert meta['out_packets_sent'] == 69
    assert meta['out_packets_received'] == 63
    assert meta['unique_out_conn'] == 17
    assert meta['in_packets_sent'] == 34
    assert meta['seconds'] == 85200
    assert meta['in_bytes_sent'] == 8400
    assert meta['unique_out_ip'] == 14
    assert meta['unique_in_ip'] == 8
    assert close_to(meta['overall_bps'], 0.3404)
    assert meta['endpoints'] == 1
    assert meta['total_in'] == 13
    assert close_to(meta['in_avg_bps'], 25.4566)
    assert meta['address'] == '10.20.30.40/32'
    assert close_to(meta['out_max_bps'], 500.0000)
    assert meta['out_bytes_sent'] == 13800
    assert meta['unique_in_conn'] == 9
    assert close_to(meta['in_max_bps'], 500.0000)
    assert set(meta['in_protocols'].split(',')) == {'TCP', 'UDP'}
    assert meta['in_bytes_received'] == 2750
    assert close_to(meta['out_duration'], 22.0000)
    assert meta['ports_used'] == 2
    assert meta['hostname'] == ''
    assert set(meta['out_protocols'].split(',')) == {'TCP', 'UDP'}
    assert meta['in_packets_received'] == 37
    assert meta['out_bytes_received'] == 4050
    assert close_to(meta['in_duration'], 33.6923)
    assert close_to(meta['out_avg_bps'], 33.8068)


def test_get_details_connections():
    pass

def test_get_details_ports():
    pass

def test_get_details_children():
    pass

def test_get_details_summary():
    pass
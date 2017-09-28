from spec.python import db_connection
from sam.models.details import Details
from datetime import datetime
import time

db = db_connection.db
sub_id = db_connection.default_sub
ds_full = db_connection.dsid_default
ds_empty = db_connection.dsid_short


def close_to(a, b, epsilon=0.001):
    return abs(float(a) - float(b)) < epsilon


def test_get_metadata():
    m_details = Details(db, sub_id, ds_full, "10.20.30.40")
    meta = m_details.get_metadata()
    print(meta)

    assert meta['seconds'] == 68433000
    assert close_to(meta['overall_bps'], 0)
    assert meta['endpoints'] == 1
    assert meta['address'] == '10.20.30.40/32'
    assert meta['ports_used'] == 2
    assert meta['hostname'] == ''
    assert meta['unique_in_conn'] == 9
    assert meta['unique_in_ip'] == 8
    assert meta['unique_out_conn'] == 17
    assert meta['unique_out_ip'] == 14
    assert meta['total_out'] == 24
    assert meta['total_in'] == 13

    assert meta['in_bytes_sent'] == 8400
    assert meta['in_bytes_received'] == 2750
    assert meta['in_packets_sent'] == 34
    assert meta['in_packets_received'] == 37
    assert close_to(meta['in_avg_conn_bps'], 25.4566)
    assert close_to(meta['in_max_bps'], 500.0000)
    assert set(meta['in_protocols'].split(',')) == {'TCP', 'UDP'}
    assert close_to(meta['in_duration'], 33.6923)

    assert meta['out_bytes_sent'] == 13800
    assert meta['out_bytes_received'] == 4050
    assert meta['out_packets_sent'] == 69
    assert meta['out_packets_received'] == 63
    assert close_to(meta['out_max_bps'], 500.0000)
    assert close_to(meta['out_avg_conn_bps'], 33.8068)
    assert set(meta['out_protocols'].split(',')) == {'TCP', 'UDP'}
    assert close_to(meta['out_duration'], 22.0000)


def test_get_details_connections_in_out():
    m_details = Details(db, sub_id, ds_full, "10.20.30.40")
    details = m_details.get_details_connections(inbound=True, page=1, simple=True)
    assert len(details) == 9
    assert sum([x['links'] for x in details]) == 13
    assert set([x['src'] for x in details]) == {u'10.24.34.44',
                                                u'10.20.30.40',
                                                u'50.64.74.84',
                                                u'50.64.74.85',
                                                u'10.24.34.45',
                                                u'10.20.30.40',
                                                u'10.24.36.46',
                                                u'10.20.32.42',
                                                u'10.20.32.43'}
    details = m_details.get_details_connections(inbound=False, page=1, simple=True)
    assert len(details) == 17
    assert sum([x['links'] for x in details]) == 24
    assert set([x['dst'] for x in details]) == {u'50.64.76.87',
                                                u'10.20.30.40',
                                                u'59.69.79.89',
                                                u'50.60.70.80',
                                                u'50.64.74.85',
                                                u'50.64.76.86',
                                                u'50.60.72.83',
                                                u'50.60.72.82',
                                                u'50.64.74.84',
                                                u'10.20.32.42',
                                                u'10.24.36.46',
                                                u'50.60.70.81',
                                                u'10.24.34.45',
                                                u'10.24.34.44'}


def test_get_details_connections_simple():
    m_details = Details(db, sub_id, ds_full, "10.20.30.40")
    simple = m_details.get_details_connections(inbound=True, page=1, simple=True)
    complx = m_details.get_details_connections(inbound=True, page=1, simple=False)

    assert len(simple) == len(complx)
    assert set(simple[0].keys()) == {'src', 'port', 'links'}
    assert set(complx[0].keys()) == {'src', 'avg_bytes', 'links', 'avg_packets', 'dst', 'sum_packets', 'avg_duration',
                                     'sum_bytes', 'port', 'protocols'}


def test_get_details_connections_sort_dir():
    m_details = Details(db, sub_id, ds_full, "10.20.30.40")
    ascending = m_details.get_details_connections(inbound=True, page=1, order='+src', simple=True)
    descending = m_details.get_details_connections(inbound=True, page=1, order='-src', simple=True)

    expected_asc = [u'10.20.30.40', u'10.20.30.40', u'10.20.32.42', u'10.20.32.43', u'10.24.34.44', u'10.24.34.45',
                    u'10.24.36.46', u'50.64.74.84', u'50.64.74.85']
    expected_asc.sort()
    expected_desc = sorted(expected_asc, reverse=True)

    assert [x['src'] for x in ascending] == expected_asc
    assert [x['src'] for x in descending] == expected_desc


def test_get_details_connections_sort_col():
    m_details = Details(db, sub_id, ds_full, "10.20.30.40")
    ordered = m_details.get_details_connections(inbound=True, page=1, order='-sum_bytes', simple=False)
    expected = [2100, 1650, 1650, 1500, 1050, 1000, 1000, 900, 300]
    assert [int(x['sum_bytes']) for x in ordered] == expected

    ordered = m_details.get_details_connections(inbound=True, page=1, order='+sum_packets', simple=False)
    expected = [2, 5, 5, 5, 7, 7, 8, 16, 16]
    assert [int(x['sum_packets']) for x in ordered] == expected


def test_get_details_connections_page():
    m_details = Details(db, sub_id, ds_full, "10.20.30.40")
    m_details.page_size = 4
    p1 = m_details.get_details_connections(inbound=True, page=1, order='-src', simple=True)
    assert len(p1) == 4
    assert set([x['src'] for x in p1]) == {u'10.24.34.45', u'10.24.36.46', u'50.64.74.84', u'50.64.74.85'}
    p2 = m_details.get_details_connections(inbound=True, page=2, order='-src', simple=True)
    assert len(p2) == 4
    assert set([x['src'] for x in p2]) == {u'10.20.30.40', u'10.24.34.44', u'10.20.32.43', u'10.20.32.42'}
    p3 = m_details.get_details_connections(inbound=True, page=3, order='-src', simple=True)
    assert len(p3) == 1
    assert set([x['src'] for x in p3]) == {u'10.20.30.40'}
    p4 = m_details.get_details_connections(inbound=True, page=4, order='-src', simple=True)
    assert len(p4) == 0


def test_get_details_ports():
    m_details = Details(db, sub_id, ds_full, "50.60.70.80")
    ports = m_details.get_details_ports()
    assert len(ports) == 11
    assert sum([x['links'] for x in ports]) == 14
    assert ports[0]['links'] == 3

    m_details.page_size = 5
    ports = m_details.get_details_ports(page=1, order="-port")
    assert len(ports) == 5
    assert [x['port'] for x in ports] == [360, 328, 320, 312, 232]

    ports = m_details.get_details_ports(page=3, order="-port")
    assert len(ports) == 1
    assert [x['port'] for x in ports] == [120]

    ports = m_details.get_details_ports(page=3, order="+port")
    assert len(ports) == 1
    assert [x['port'] for x in ports] == [360]

    ports = m_details.get_details_ports(page=1, order="+port")
    assert len(ports) == 5
    assert [x['port'] for x in ports] == [120, 136, 152, 160, 192]


def test_get_details_children():
    m_details = Details(db, sub_id, ds_full, "50")
    kids = m_details.get_details_children()
    assert len(kids) == 2
    assert kids[0]['subnet'] == 16
    assert set([x['address'] for x in kids]) == {u'50.60.0.0', u'50.64.0.0'}

    m_details = Details(db, sub_id, ds_full, "50.60")
    kids = m_details.get_details_children()
    assert len(kids) == 2
    assert kids[0]['subnet'] == 24
    assert set([x['address'] for x in kids]) == {u'50.60.70.0', u'50.60.72.0'}

    m_details = Details(db, sub_id, ds_full, "50.60.70")
    kids = m_details.get_details_children()
    assert len(kids) == 2
    assert kids[0]['subnet'] == 32
    assert set([x['address'] for x in kids]) == {u'50.60.70.80', u'50.60.70.81'}

    m_details = Details(db, sub_id, ds_full, "50.60.70.80")
    kids = m_details.get_details_children()
    assert len(kids) == 0


def test_get_details_summary():
    m_details = Details(db, sub_id, ds_full, '10')
    summary = m_details.get_details_summary()
    assert summary['unique_in'] == 17
    assert summary['unique_out'] == 17
    assert summary['unique_ports'] == 40

    m_details = Details(db, sub_id, ds_full, '10.20')
    summary = m_details.get_details_summary()
    assert summary['unique_in'] == 17
    assert summary['unique_out'] == 17
    assert summary['unique_ports'] == 31

    m_details = Details(db, sub_id, ds_full, '10.20.30')
    summary = m_details.get_details_summary()
    assert summary['unique_in'] == 14
    assert summary['unique_out'] == 17
    assert summary['unique_ports'] == 13

    m_details = Details(db, sub_id, ds_full, '10.20.30.40')
    summary = m_details.get_details_summary()
    assert summary['unique_in'] == 8
    assert summary['unique_out'] == 14
    assert summary['unique_ports'] == 2


def test_get_details_summary_timerange():
    time_wide = (1, 2 ** 31 - 1)
    time_full = (int(time.mktime(datetime(2017, 3, 21, 6, 13, 05).timetuple())),
                 int(time.mktime(datetime(2017, 3, 24, 13, 30, 54).timetuple())))
    time_narrow = (int(time.mktime(datetime(2017, 3, 23, 6, 13, 05).timetuple())),
                   int(time.mktime(datetime(2017, 3, 23, 13, 30, 54).timetuple())))
    #    d_start = datetime(2017, 3, 21, 6, 13, 05)
    #    d_end = datetime(2017, 3, 24, 13, 30, 54)
    m_details = Details(db, sub_id, ds_full, '10', timestamp_range=time_wide)
    summary = m_details.get_details_summary()
    assert summary['unique_in'] == 17
    assert summary['unique_out'] == 17
    assert summary['unique_ports'] == 40

    m_details = Details(db, sub_id, ds_full, '10', timestamp_range=time_full)
    summary = m_details.get_details_summary()
    assert summary['unique_in'] == 17
    assert summary['unique_out'] == 17
    assert summary['unique_ports'] == 40

    m_details = Details(db, sub_id, ds_full, '10', timestamp_range=time_narrow)
    summary = m_details.get_details_summary()
    assert summary['unique_in'] == 9
    assert summary['unique_out'] == 14
    assert summary['unique_ports'] == 9

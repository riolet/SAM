import dbaccess
from datetime import datetime
import time
import common


def make_timestamp(ts):
    d = datetime.strptime(ts, "%Y-%m-%d %H:%M")
    ts = time.mktime(d.timetuple())
    return int(ts)


def values(d, *keys):
    return tuple(map(lambda k: d[k], keys))


def test_get_details_summary():
    details = dbaccess.get_details_summary(*common.determine_range(21)[:2])
    assert values(details, 'unique_in', 'unique_out', 'unique_ports') == (13418L, 3494L, 20371L)

    details = dbaccess.get_details_summary(*common.determine_range(21, 66)[:2])
    assert values(details, 'unique_in', 'unique_out', 'unique_ports') == (13418L, 3494L, 20371L)

    details = dbaccess.get_details_summary(*common.determine_range(21, 66, 10)[:2])
    assert values(details, 'unique_in', 'unique_out', 'unique_ports') == (2816L, 1L, 3464L)

    details = dbaccess.get_details_summary(*common.determine_range(21, 66, 10, 70)[:2])
    assert values(details, 'unique_in', 'unique_out', 'unique_ports') == (30L, 0L, 30L)

    details = dbaccess.get_details_summary(*common.determine_range(21, 66, 40, 231)[:2])
    assert values(details, 'unique_in', 'unique_out', 'unique_ports') == (7L, 40L, 1L)


def test_get_details_summary_ports():
    ip_start, ip_end, _ = common.determine_range(21, 66, 40, 231)
    details = dbaccess.get_details_summary(ip_start, ip_end, port=445)
    assert values(details, 'unique_in', 'unique_out', 'unique_ports') == (7L, 0L, 1L)

    details = dbaccess.get_details_summary(ip_start, ip_end, port=80)
    assert values(details, 'unique_in', 'unique_out', 'unique_ports') == (0, 2, 0)

    details = dbaccess.get_details_summary(ip_start, ip_end, port=1)
    assert values(details, 'unique_in', 'unique_out', 'unique_ports') == (0, 0, 0)


def test_get_details_summary_timerange():
    time_all = (1, 2 ** 31 - 1)
    time_crop = (make_timestamp('2016-06-21 17:10'), make_timestamp('2016-06-21 18:05'))
    time_tiny = (make_timestamp('2016-06-21 17:45'), make_timestamp('2016-06-21 17:50'))
    ip_start, ip_end, _ = common.determine_range(21, 66, 40, 231)
    ip_start2, ip_end2, _ = common.determine_range(79, 35, 103, 221)

    details = dbaccess.get_details_summary(ip_start, ip_end, timestamp_range=time_all)
    assert values(details, 'unique_in', 'unique_out', 'unique_ports') == (7, 40, 1)

    details = dbaccess.get_details_summary(ip_start, ip_end, timestamp_range=time_crop)
    assert values(details, 'unique_in', 'unique_out', 'unique_ports') == (7, 40, 1)

    details = dbaccess.get_details_summary(ip_start2, ip_end2, timestamp_range=time_crop)
    assert values(details, 'unique_in', 'unique_out', 'unique_ports') == (1, 0, 1)

    details = dbaccess.get_details_summary(ip_start, ip_end, timestamp_range=time_tiny)
    assert values(details, 'unique_in', 'unique_out', 'unique_ports') == (3, 21, 1)


def test_get_details_conn():
    ipstart, ipend, _ = common.determine_range(21)
    details = dbaccess.get_details_connections(ipstart, ipend, True)
    assert len(details) == 50
    details = dbaccess.get_details_connections(ipstart, ipend, False)
    assert len(details) == 50

    ipstart, ipend, _ = common.determine_range(21, 66)
    details = dbaccess.get_details_connections(ipstart, ipend, True)
    assert len(details) == 50
    details = dbaccess.get_details_connections(ipstart, ipend, False)
    assert len(details) == 50

    ipstart, ipend, _ = common.determine_range(21, 66, 10)
    details = dbaccess.get_details_connections(ipstart, ipend, True)
    assert len(details) == 50
    details = dbaccess.get_details_connections(ipstart, ipend, False)
    assert len(details) == 1

    ipstart, ipend, _ = common.determine_range(21, 66, 10, 70)
    details = dbaccess.get_details_connections(ipstart, ipend, True)
    assert len(details) == 50
    details = dbaccess.get_details_connections(ipstart, ipend, False)
    assert len(details) == 0

    ipstart, ipend, _ = common.determine_range(21, 66, 40, 231)
    details = dbaccess.get_details_connections(ipstart, ipend, True)
    assert len(details) == 7
    details = dbaccess.get_details_connections(ipstart, ipend, False)
    assert len(details) == 50


def test_get_details_conn_ports():
    ipstart, ipend, _ = common.determine_range(21, 66, 40, 231)
    details = dbaccess.get_details_connections(ipstart, ipend, True, port=445)
    assert len(details) == 7
    details = dbaccess.get_details_connections(ipstart, ipend, False, port=445)
    assert len(details) == 0

    details = dbaccess.get_details_connections(ipstart, ipend, True, port=80)
    assert len(details) == 0
    details = dbaccess.get_details_connections(ipstart, ipend, False, port=80)
    assert len(details) == 2

    details = dbaccess.get_details_connections(ipstart, ipend, True, port=1)
    assert len(details) == 0
    details = dbaccess.get_details_connections(ipstart, ipend, False, port=1)
    assert len(details) == 0


def test_get_details_conn_timerange():
    time_all = (1, 2 ** 31 - 1)
    time_crop = (make_timestamp('2016-06-21 17:10'), make_timestamp('2016-06-21 18:05'))
    time_tiny = (make_timestamp('2016-06-21 17:45'), make_timestamp('2016-06-21 17:50'))
    ipstart, ipend, _ = common.determine_range(21, 66, 40, 231)
    ipstart2, ipend2, _ = common.determine_range(79, 35, 103, 221)

    details = dbaccess.get_details_connections(ipstart, ipend, True, timestamp_range=time_all)
    assert len(details) == 7
    details = dbaccess.get_details_connections(ipstart, ipend, False, timestamp_range=time_all)
    assert len(details) == 50

    details = dbaccess.get_details_connections(ipstart, ipend, True, timestamp_range=time_crop)
    assert len(details) == 7
    details = dbaccess.get_details_connections(ipstart, ipend, False, timestamp_range=time_crop)
    assert len(details) == 50

    details = dbaccess.get_details_connections(ipstart, ipend, True, timestamp_range=time_tiny)
    assert len(details) == 3
    details = dbaccess.get_details_connections(ipstart, ipend, False, timestamp_range=time_tiny)
    assert len(details) == 34

    details = dbaccess.get_details_connections(ipstart2, ipend2, True, timestamp_range=time_crop)
    assert len(details) == 1
    details = dbaccess.get_details_connections(ipstart2, ipend2, False, timestamp_range=time_crop)
    assert len(details) == 0


def test_get_details_ports():
    time_all = (1, 2 ** 31 - 1)
    time_crop = (make_timestamp('2016-06-21 17:10'), make_timestamp('2016-06-21 18:05'))
    time_tiny = (make_timestamp('2016-06-21 17:45'), make_timestamp('2016-06-21 17:50'))
    ipstart1, ipend1, _ = common.determine_range(21, 66, 40, 231)
    ipstart2, ipend2, _ = common.determine_range(79, 35, 103, 221)

    ipstart, ipend, _ = common.determine_range(21)
    details = dbaccess.get_details_ports(ipstart, ipend)
    assert len(details) == 50
    ipstart, ipend, _ = common.determine_range(21, 66)
    details = dbaccess.get_details_ports(ipstart, ipend)
    assert len(details) == 50
    ipstart, ipend, _ = common.determine_range(21, 66, 10)
    details = dbaccess.get_details_ports(ipstart, ipend)
    assert len(details) == 50
    ipstart, ipend, _ = common.determine_range(21, 66, 10, 70)
    details = dbaccess.get_details_ports(ipstart, ipend)
    assert len(details) == 30
    details = dbaccess.get_details_ports(ipstart1, ipend1)
    assert len(details) == 1

    details = dbaccess.get_details_ports(ipstart1, ipend1, port=445)
    assert len(details) == 1
    details = dbaccess.get_details_ports(ipstart1, ipend1, port=80)
    assert len(details) == 0
    details = dbaccess.get_details_ports(ipstart1, ipend1, port=1)
    assert len(details) == 0

    details = dbaccess.get_details_ports(ipstart1, ipend1, timestamp_range=time_all)
    assert len(details) == 1
    details = dbaccess.get_details_ports(ipstart1, ipend1, timestamp_range=time_crop)
    assert len(details) == 1
    details = dbaccess.get_details_ports(ipstart1, ipend1, timestamp_range=time_tiny)
    assert len(details) == 1
    details = dbaccess.get_details_ports(ipstart2, ipend2, timestamp_range=time_crop)
    assert len(details) == 1


def test_get_details_children():
    ipstart1, ipend1, _ = common.determine_range(79)
    ipstart2, ipend2, _ = common.determine_range(79, 35)
    ipstart3, ipend3, _ = common.determine_range(79, 35, 103)
    details = dbaccess.get_details_children(ipstart1, ipend1, 1, 256, "ipstart")
    assert len(details) == 8
    details = dbaccess.get_details_children(ipstart2, ipend2, 1, 256, "ipstart")
    assert len(details) == 59
    details = dbaccess.get_details_children(ipstart3, ipend3, 1, 256, "ipstart")
    assert len(details) == 96
